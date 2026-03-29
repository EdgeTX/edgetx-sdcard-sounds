#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

# Find voices directory relative to script location
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DIR = SCRIPT_DIR.parent / "voices"

# Header with 6 required fields and 1 optional field (Skip)
HEADER_REQUIRED = ["String ID", "Source text", "Translation", "Context", "Path", "Filename"]
HEADER_FULL = ["String ID", "Source text", "Translation", "Context", "Path", "Filename", "Skip"]


def fix_file(path: Path):
    rows = []
    has_skip_field = False
    try:
        with path.open('r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for idx, row in enumerate(reader, start=1):
                # Keep rows that have 6 or 7 fields (7th is optional Skip)
                if len(row) in (6, 7):
                    rows.append(row)
                    if len(row) == 7:
                        has_skip_field = True
                else:
                    # Skip rows with fewer fields than expected
                    # print(f"Skipping malformed line {idx} in {path}: {row}")
                    pass
    except FileNotFoundError:
        print(f"File not found: {path}")
        return 1

    if not rows:
        print(f"No valid rows found in {path}")
        return 2

    expected_header = HEADER_FULL if has_skip_field else HEADER_REQUIRED

    # Ensure header is present and correct at top
    if rows[0] != expected_header:
        # If current first row looks like header but unquoted, normalize
        normalized = [c.strip().strip('"') for c in rows[0]]
        if normalized == HEADER_REQUIRED or normalized == HEADER_FULL:
            rows[0] = expected_header
        else:
            # Prepend a clean header
            rows.insert(0, expected_header)

    # Ensure all rows have consistent field count
    for i in range(1, len(rows)):
        if len(rows[i]) < len(expected_header):
            # Pad with empty string for missing 7th field
            rows[i].extend([''] * (len(expected_header) - len(rows[i])))
        elif len(rows[i]) > len(expected_header):
            # Trim to expected length
            rows[i] = rows[i][:len(expected_header)]

    # Deduplicate rows (exact match)
    seen = set()
    deduped = []
    for row in rows:
        key = tuple(row)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    # Write back using standard CSV quoting rules (minimal quoting)
    tmp = path.with_suffix('.tmp')
    with tmp.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
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
