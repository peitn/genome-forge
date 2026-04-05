import argparse
from pathlib import Path
from .compiler import Compiler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    src = Path(args.source).read_text(encoding="utf-8")
    compiled_path = Compiler().compile(src, args.out)
    print(f"Compiled to {compiled_path}")

if __name__ == "__main__":
    main()
