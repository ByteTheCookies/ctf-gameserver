#!/usr/bin/env python3
import sys
import pathlib

HARD_CODED_STRING = "WORKING-STORAGE SECTION."  # change if needed

def fix_file(filename: str):
    path = pathlib.Path(filename)
    if not path.exists():
        print(f"Error: file {filename} not found", file=sys.stderr)
        sys.exit(1)

    with path.open("r") as f:
        content = f.read()

    # Remove the second occurrence (whole file, not per line)
    index1 = content.find(HARD_CODED_STRING)
    if index1 == -1:
        print("not found")
        return  # string not found at all
    index2 = content.find(HARD_CODED_STRING, index1 + len(HARD_CODED_STRING))
    if index2 == -1:
        print("only one")
        return  # only one occurrence

    # Remove it
    new_content = content[:index2] + content[index2 + len(HARD_CODED_STRING):]

    with path.open("w") as f:
        f.write(new_content)
        print("removed 2nd")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file>")
        sys.exit(1)
    fix_file(sys.argv[1])

if __name__ == "__main__":
    main()
