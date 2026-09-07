"""Reference implementation of references/token-naming-validation.md.
Written to spec, deliberately literal — the point is to find out whether the
spec as written actually works, not to write the best possible checker.
"""
import json, re, sys

def canonical_words(path):
    """Step 1 — split on '.', then on '-'/'_' inside each segment, lowercase."""
    words = []
    for seg in path.split('.'):
        words.extend(re.split(r'[-_]', seg))
    return [w.lower() for w in words if w]

ROWS = ["dot", "kebab", "snake", "camel", "pascal", "flat", "screaming-snake"]

def generate(words, row):
    """Step 2 — generate one convention's form from a word list."""
    if row == "dot":             return ".".join(words)
    if row == "kebab":           return "-".join(words)
    if row == "snake":           return "_".join(words)
    if row == "screaming-snake": return "_".join(w.upper() for w in words)
    if row == "flat":            return "".join(words)
    if row == "camel":
        return words[0] + "".join(w.capitalize() for w in words[1:])
    if row == "pascal":
        return "".join(w.capitalize() for w in words)
    raise ValueError(row)

def strip_file_prefix(candidate):
    """A '--' is a property of the file type, not an eighth convention."""
    return candidate[2:] if candidate.startswith("--") else candidate

def match(candidate, words, custom_prefix=None):
    """Step 3 — try every row at every leading truncation depth.
    Returns list of (row, depth) matches."""
    cand = strip_file_prefix(candidate)
    if custom_prefix and cand.startswith(custom_prefix):
        cand = cand[len(custom_prefix):]
    hits = []
    for depth in range(len(words)):
        truncated = words[depth:]
        if not truncated:
            break
        for row in ROWS:
            if generate(truncated, row) == cand:
                hits.append((row, depth))
    return hits

def load_paths(tokenfile):
    d = json.load(open(tokenfile))
    out = []
    def walk(n, p=""):
        if isinstance(n, dict):
            if "$value" in n or "value" in n:
                out.append(p); return
            for k, v in n.items():
                if k.startswith("$"): continue
                walk(v, p + "." + k if p else k)
    walk(d)
    return out

if __name__ == "__main__":
    paths = load_paths(sys.argv[1])
    index = {p: canonical_words(p) for p in paths}
    print(f"{len(paths)} canonical paths loaded\n")

    # Candidates: name, and the canonical path we claim it refers to
    cases = [
        ("--primitive-color-purple-500", "primitive.color.purple.500", "kebab depth 0"),
        ("primitiveColorPurple500",      "primitive.color.purple.500", "camel depth 0"),
        ("PRIMITIVE_COLOR_PURPLE_500",   "primitive.color.purple.500", "screaming depth 0"),
        ("primitivecolorpurple500",      "primitive.color.purple.500", "flat depth 0"),
        ("--purple-500",                 "primitive.color.purple.500", "kebab depth 2 (scoped)"),
        ("--primitive-color-500-purple", "primitive.color.purple.500", "REORDERED - must fail"),
        ("--base-color-purple-500",      "primitive.color.purple.500", "SUBSTITUTED - must fail"),
        ("--primitive-color-black-alpha-40", "primitive.color.black-alpha.40", "internal-hyphen segment"),
        ("primitiveColorBlackAlpha40",   "primitive.color.black-alpha.40", "internal-hyphen, camel"),
    ]
    for cand, path, label in cases:
        words = index.get(path)
        if words is None:
            print(f"  ?? {cand:38} path not in tree: {path}")
            continue
        hits = match(cand, words)
        status = "PASS" if hits else "FAIL"
        print(f"  {status:4} {cand:38} {str(hits):22} [{label}]")

    # --- Probes: the two properties Step 4 depends on and does not get for free ---
    from collections import defaultdict
    print("\nRow ambiguity (a name matching >1 row cannot fix the convention):")
    counts = defaultdict(int)
    for p, w in index.items():
        for depth in range(len(w)):
            forms = defaultdict(list)
            for row in ROWS:
                forms[generate(w[depth:], row)].append(row)
            for rows in forms.values():
                if len(rows) > 1:
                    counts[len(rows)] += 1
    for n in sorted(counts, reverse=True):
        print(f"    {counts[n]:4} forms match {n} rows at once")

    print("\nDepth injectivity (a depth is only usable while names stay distinct):")
    print(f"    {'depth':>5} {'distinct':>9} {'ambiguous':>10}")
    for depth in range(0, 5):
        forms = defaultdict(list)
        for p, w in index.items():
            if depth < len(w):
                forms[generate(w[depth:], "kebab")].append(p)
        amb = sum(len(ps) for ps in forms.values() if len(ps) > 1)
        print(f"    {depth:>5} {len(forms):>9} {amb:>10}")
