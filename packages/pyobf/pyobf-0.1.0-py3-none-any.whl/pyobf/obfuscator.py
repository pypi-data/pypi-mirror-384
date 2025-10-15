from __future__ import annotations
import sys
import os
import base64
import zlib
import hashlib
import random
import textwrap

SEED = os.environ.get("OBFS_SEED")
if SEED is None:
    SEED = str(random.randrange(2**63))
random.seed(SEED)

ALNUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
ALNUMD = ALNUM + "0123456789"

def _rand_ident(min_len=8, max_len=16):
    n = random.randint(min_len, max_len)
    s = random.choice(ALNUM)
    s += ''.join(random.choice(ALNUMD) for _ in range(n - 1))
    return s

def _xor_bytes(data: bytes, key: bytes) -> bytes:
    if not key:
        return data
    out = bytearray(len(data))
    kl = len(key)
    for i, b in enumerate(data):
        out[i] = b ^ key[i % kl]
    return bytes(out)

def build_stub(original_code: str, in_file: str) -> str:
    import marshal
    fake_name = f"<{_rand_ident(6,12)}>"
    code_obj = compile(original_code, fake_name, 'exec', optimize=2)
    marshaled = marshal.dumps(code_obj)
    comp = zlib.compress(marshaled, 9)
    key1 = os.urandom(16)
    key2 = os.urandom(24)
    x1 = _xor_bytes(comp, key1)
    x2 = _xor_bytes(x1, key2)

    def _permute_forward(b: bytes, seed: int) -> bytes:
        a = bytearray(b)
        s = seed & 0xFFFFFFFF
        for i in range(len(a)-1, 0, -1):
            s = (s*1664525 + 1013904223) & 0xFFFFFFFF
            j = s % (i+1)
            a[i], a[j] = a[j], a[i]
        return bytes(a)

    seed = int.from_bytes(hashlib.sha256(key1 + key2).digest()[:4], 'big')
    enc = _permute_forward(x2, seed)

    payload_b85 = base64.b85encode(enc).decode('ascii')
    k1_b85 = base64.b85encode(key1).decode('ascii')
    k2_b85 = base64.b85encode(key2).decode('ascii')
    sha = hashlib.sha256(marshaled).hexdigest()

    def _shard(s: str):
        n = random.randint(7, 13)
        if len(s) < n:
            return [s]
        sizes = [len(s)//n]*(n)
        for i in range(len(s)%n):
            sizes[i] += 1
        random.shuffle(sizes)
        out=[]; idx=0
        for sz in sizes:
            out.append(s[idx:idx+sz]); idx+=sz
        return out

    p_parts = _shard(payload_b85)
    k1_parts = _shard(k1_b85)
    k2_parts = _shard(k2_b85)

    def _gen_names(keys):
        used=set();out={}
        for k in keys:
            n=_rand_ident(1,3)
            while n in used:
                n=_rand_ident(1,3)
            used.add(n);out[k]=n
        return out
    names = _gen_names(['b','z','h','x','m','k1','k2','p','chk','f','ld','vf','ad','up','bf','g','q','w','r','t','n','s','c'])

    def q(l):
        return '+'.join([repr(part) for part in l]) if l else "''"

    base_stub_core = (
        f"{names['b']}=__import__('base64');{names['h']}=__import__('hashlib');{names['x']}=__import__('zlib');{names['m']}=__import__('marshal');{names['z']}=__import__('sys')\n"
        f"{names['p']}={q(p_parts)};{names['k1']}={q(k1_parts)};{names['k2']}={q(k2_parts)};{names['chk']}='{sha}'\n"
        f"def {names['ad']}():\n    e=__import__('os').environ;M={names['z']}.modules\n    if e.get('OBFS_STRICT')=='1':\n        gt={names['z']}.gettrace();((gt is None) and all(k not in e for k in ('PYCHARM_HOSTED','PYTHONINSPECT')) and all(m not in M for m in ('pydevd','uncompyle6','decompiler'))) or (_ for _ in ()).throw(SystemExit(0))\n    else:\n        (all(m not in M for m in ('uncompyle6','decompiler'))) or (_ for _ in ()).throw(SystemExit(0))\n"
        f"def {names['vf']}(a):\n    ({names['h']}.sha256(a).hexdigest()=={names['chk']}) or (_ for _ in ()).throw(RuntimeError(str((1<<31)-1)))\n"
        f"def {names['f']}(d,k):\n    o=bytearray(len(d));L=len(k);[o.__setitem__(i,(d[i]^k[i%L])) for i in range(len(d))];return bytes(o)\n"
        f"def {names['up']}(b,k1,k2):\n    s=int.from_bytes({names['h']}.sha256(k1+k2).digest()[:4],'big')&0xFFFFFFFF;_a=bytearray(b);i=len(_a)-1\n    while i>0:\n        s=(s*1664525+1013904223)&0xFFFFFFFF;j=s%(i+1);_a[i],_a[j]=_a[j],_a[i];i-=1\n    i=1\n    a=bytearray(b)\n    s=int.from_bytes({names['h']}.sha256(k1+k2).digest()[:4],'big')&0xFFFFFFFF;idx=list(range(len(a)))\n    for i in range(len(a)-1,0,-1):\n        s=(s*1664525+1013904223)&0xFFFFFFFF;idx[i],idx[s%(i+1)]=idx[s%(i+1)],idx[i]\n    r=bytearray(len(a))\n    [r.__setitem__(idx[i],a[i]) for i in range(len(a))]\n    return bytes(r)\n"
        f"def {names['bf']}(P):\n    T=[0]*300;c=0;p=0;i=0;O=[]\n    while i<len(P):\n        o=P[i]\n        if o==43:T[c]=(T[c]+1)&255\n        elif o==45:T[c]=(T[c]-1)&255\n        elif o==62:c=(c+1)%300\n        elif o==60:c=(c-1)%300\n        elif o==46:O.append(chr(T[c]))\n        elif o==44:pass\n        if o==91 and T[c]==0:\n            d=1;i+=1\n            while i<len(P) and d>0:\n                P[i]==91 and (d:=d+1);P[i]==93 and (d:=d-1);i+=1\n            continue\n        elif o==93 and T[c]!=0:\n            d=1;i-=1\n            while i>=0 and d>0:\n                P[i]==93 and (d:=d+1);P[i]==91 and (d:=d-1);i-=1\n            continue\n        i+=1\n    return ''.join(O)\n"
        f"def {names['ld']}():\n    {names['ad']}();q={names['b']}.b85decode({names['p']}.encode('ascii'));k1={names['b']}.b85decode({names['k1']}.encode('ascii'));k2={names['b']}.b85decode({names['k2']}.encode('ascii'))\n    q={names['up']}(q,k1,k2);r={names['f']}(q,k2);s={names['f']}(r,k1);t={names['x']}.decompress(s);{names['vf']}(t);N={{'__name__':'__main__','__file__':{repr(fake_name)},'__package__':None,'__cached__':None}}\n    exec({names['m']}.loads(t),N)\n"
        f"{names['ld']}()\n"
    )

    stub_size_now = len(base_stub_core)
    target_size = max(len(original_code) * 4, stub_size_now + 768)
    need_extra = max(0, target_size - stub_size_now)

    raw_est = int(need_extra / 1.25)
    raw_est = max(0, raw_est)
    filler_bytes = os.urandom(raw_est)
    filler_b85 = base64.b85encode(filler_bytes).decode('ascii') if raw_est > 0 else ''

    filler_block = (
        f"{names['g']}='{filler_b85}';\ntry:\n\t{names['q']}=len({names['bf']}(b'++++++++++[>+>+++>+++++++>++++++++++<<<<-]>>>>++++.+.---.'));{names['w']}=sum({names['b']}.b85decode({names['g']}.encode('ascii'))[:257])&255\nexcept Exception:\n\t{names['r']}=0\n" if raw_est>0 else ''
    )

    return base_stub_core + ("\n" + filler_block if filler_block else '') + "\n"
