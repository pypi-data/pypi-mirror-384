import sys
from pathlib import Path
from .obfuscator import build_stub

def main():
    if len(sys.argv) != 3:
        print("Usage: pyobf input.py output.py")
        return 2
    in_path, out_path = sys.argv[1:]
    in_path = Path(in_path)
    out_path = Path(out_path)
    if not in_path.is_file():
        print(f"Input file not found: {in_path}")
        return 2
    try:
        code = in_path.read_text(encoding='utf-8')
        stub = build_stub(code, str(in_path.absolute()))
    except Exception as e:
        print("Obfuscation failed:", e)
        return 1
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(stub, encoding='utf-8', newline='\n')
    except Exception as e:
        print(f"Error writing output file: {e}")
        return 1
    try:
        in_size = in_path.stat().st_size
        out_size = out_path.stat().st_size
        pct = (out_size / max(1, in_size)) * 100.0
        print(f"Done. Output size: {out_size} bytes (~{pct:.1f}% of input)")
    except Exception:
        pass
    return 0

if __name__ == '__main__':
    sys.exit(main())
