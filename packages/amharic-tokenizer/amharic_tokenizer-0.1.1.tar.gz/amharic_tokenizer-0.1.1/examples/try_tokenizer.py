#!/usr/bin/env python3
import argparse
from pathlib import Path

from amharic_tokenizer import AmharicTokenizer


def main():
    parser = argparse.ArgumentParser(description="Load a trained Amharic tokenizer and test on input data")
    parser.add_argument("model_prefix", nargs="?", default="amh_bpe", help="Model prefix to load (without .json)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="Single text string to tokenize")
    group.add_argument("--file", help="Path to a UTF-8 text file; tokenizes each non-empty line")
    args = parser.parse_args()

    tok = AmharicTokenizer.load(args.model_prefix)

    if args.text is not None:
        tokens = tok.tokenize(args.text)
        print("TOKENS:", tokens)
        print("DETOK:", tok.detokenize(tokens))
        return

    path = Path(args.file)
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        tokens = tok.tokenize(line)
        print(f"LINE {i}:")
        print("  TEXT:", line)
        print("  TOKENS:", tokens)
        print("  DETOK:", tok.detokenize(tokens))


if __name__ == "__main__":
    main()


