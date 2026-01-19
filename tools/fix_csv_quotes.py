#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

# Default directory to process when no args provided
DEFAULT_DIR = Path('voices')

HEADER = ["String ID","Source text","Translation","Context","Path","Filename"]


def fix_file(path: Path):
    rows = []
    try:
        with path.open('r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for idx, row in enumerate(reader, start=1):
                # Keep rows that have 6 or 7 fields (7th is optional)
                if len(row) in (6, 7):
                    rows.append(row)
                else:
                    # Skip stray/unquoted or malformed lines
                    # print(f"Skipping malformed line {idx} in {path}: {row}")
                    pass
    except FileNotFoundError:
        print(f"File not found: {path}")
        return 1

    if not rows:
        print(f"No valid rows found in {path}")
        return 2

    # Ensure header is present and correct at top
    if rows[0] != HEADER:
        # If current first row looks like header but unquoted, normalize
        if [c.strip() for c in rows[0]] == [c.strip().strip('"') for c in HEADER]:
            rows[0] = HEADER
        else:
            # Prepend a clean header
            rows.insert(0, HEADER)

    # Deduplicate rows (exact match)
    seen = set()
    deduped = []
    for row in rows:
        key = tuple(row)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    # Write back with all fields quoted
    tmp = path.with_suffix('.tmp')
    with tmp.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        for row in deduped:
            writer.writerow(row)

    tmp.replace(path)
    print(f"Fixed: {path} (rows: {len(deduped)})")
    return 0


def collect_targets(args: list[str]) -> list[Path]:
    targets: list[Path] = []
    if not args:
        root = DEFAULT_DIR
        if root.is_dir():
            targets.extend(sorted(root.rglob('*.csv')))
        else:
            print(f"Default directory not found: {root}")
        return targets

    for a in args:
        p = Path(a)
        if p.is_dir():
            targets.extend(sorted(p.rglob('*.csv')))
        elif p.is_file() and p.suffix.lower() == '.csv':
            targets.append(p)
        else:
            # Allow bare names under voices (e.g., 'sv-SE.csv')
            maybe = DEFAULT_DIR / a
            if maybe.is_file() and maybe.suffix.lower() == '.csv':
                targets.append(maybe)
            else:
                print(f"Skipping non-existent target: {a}")
    return targets


def main(argv):
    files = collect_targets(argv)
    if not files:
        print("No CSV files found to process.")
        return 1
    rc = 0
    for p in files:
        rc |= fix_file(p)
    print(f"Processed {len(files)} file(s).")
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
