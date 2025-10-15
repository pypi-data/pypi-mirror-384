from setuptools import setup, find_packages

setup(
    name="pyobf",
    version="0.1.1",
    description="A Python Code Obfuscator",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author="Malware Testing",
    author_email="admin@redstone-studios.de",
    url="https://redstone-studios.de",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'pyobf=pyobf.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
)
