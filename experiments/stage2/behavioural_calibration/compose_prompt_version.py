import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--amendment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = args.base.read_text(encoding="utf-8-sig")
    amendment = args.amendment.read_text(encoding="utf-8-sig").strip()
    anchor = "DEPTH AND EXPLANATORY STANDARD"
    if base.count(anchor) != 1:
        raise ValueError(f"Expected one insertion anchor: {anchor}")
    result = base.replace(anchor, amendment + "\n\n" + anchor, 1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
