import os
import re

COVER_DIR = 'trace_cov'
MODULE_PREFIXES = (
    'src.',
    'spotlighting.',
)


def parse_cover_file(path: str) -> tuple[int, int]:
    executed = 0
    total = 0
    num_re = re.compile(r"^\s*\d+:")
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            # exclude pure blank lines
            if line.strip() == '':
                continue
            total += 1
            if num_re.match(line):
                executed += 1
    return executed, total


def main() -> None:
    files = [f for f in os.listdir(COVER_DIR) if f.endswith('.cover')]
    selected = [f for f in files if f.startswith(MODULE_PREFIXES)]
    if not selected:
        print("No .cover files for target modules found.")
        return
    grand_exec = 0
    grand_total = 0
    per_file = []
    for fname in sorted(selected):
        e, t = parse_cover_file(os.path.join(COVER_DIR, fname))
        grand_exec += e
        grand_total += t
        pct = (e / t * 100.0) if t else 0.0
        per_file.append((fname, e, t, pct))

    print("Approximate coverage by module (trace-based):")
    for fname, e, t, pct in per_file:
        print(f"- {fname}: {pct:.1f}% ({e}/{t})")
    overall = (grand_exec / grand_total * 100.0) if grand_total else 0.0
    print(f"Overall (selected modules): {overall:.1f}% ({grand_exec}/{grand_total})")


if __name__ == '__main__':
    main()
