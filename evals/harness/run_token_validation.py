"""End-to-end run of the token-name check against real generated output.

This is the first exercise of the `generated_downstream: true` path: a token
tree, real generated platform files derived from it, and a deliberately broken
variant. It measures both halves of a usable check —

  specificity — the clean file must produce ZERO findings
  sensitivity — the broken file must produce EXACTLY the findings its manifest declares

A checker that only ever runs against correct input proves nothing; the negative
control is what makes a green run meaningful.

KNOWN FIDELITY GAP. The spec lists "Unknown token" and "Structural mismatch" as
two separate finding categories; this implementation reports both as one. Telling
them apart means deciding whether a candidate's words exist in the tree at all,
which requires reverse-parsing the candidate into words — precisely what the
algorithm's core idea rejects as unreliable (a `flat`-row name has no delimiters
to split on). Both are ALERTs and both mean the binding is wrong, so the merge
costs severity nothing; it costs only the explanation offered to whoever reads
the finding. Worth resolving before the categories are cited as distinct anywhere
a user sees them.
"""
import sys, os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tokencheck import load_paths, canonical_words
from tokenlock import Lock, check_against_lock, depth_is_verifiable

FIX = os.path.join(HERE, "..", "fixtures")

def parse_css(path):
    """Each line carries the canonical path it claims to bind, in a comment."""
    out = []
    for line in open(path):
        m = re.match(r"\s*(--[\w-]+):\s*/\*\s*([\w.\-]+)\s*\*/", line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out

def parse_swift(path):
    out = []
    for line in open(path):
        m = re.match(r"\s*static let (\w+) = \d+ // ([\w.\-]+)", line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out

def run(pairs, lock, label):
    findings = []
    for name, claimed in pairs:
        f = check_against_lock(name, claimed, lock)
        if f:
            findings.append(f)
    print(f"  {label}: {len(pairs)} names checked, {len(findings)} finding(s)")
    return findings

if __name__ == "__main__":
    tree = load_paths(os.path.join(FIX, "tokens", "design-tokens.json"))
    ok = True

    print("Precondition — is each platform's locked depth verifiable?")
    for depth, row, plat in [(0, "kebab", "Web"), (1, "camel", "iOS")]:
        good, coll = depth_is_verifiable(tree, depth, row)
        print(f"  {plat:5} depth {depth} ({row}): {'verifiable' if good else 'NOT VERIFIABLE'}")
        ok &= good

    print("\nSpecificity — clean generated output must produce no findings:")
    web = Lock("kebab", None, 0, confirmed=True)
    ios = Lock("camel", None, 1, confirmed=True)
    f1 = run(parse_css(os.path.join(FIX, "generated", "tokens.css")), web, "tokens.css   ")
    f2 = run(parse_swift(os.path.join(FIX, "generated", "Tokens.swift")), ios, "Tokens.swift ")
    for f in f1 + f2:
        print(f"     unexpected: {f}")
    ok &= not (f1 or f2)

    print("\nSensitivity — broken output must produce exactly its declared findings:")
    man = json.load(open(os.path.join(FIX, "generated", "tokens.broken.manifest.json")))
    expected = sorted(m["expect_finding"] for m in man["mutations"])
    got = run(parse_css(os.path.join(FIX, "generated", "tokens.broken.css")), web, "tokens.broken")
    got_kinds = sorted(f.kind for f in got)
    for f in got:
        print(f"     caught: {f.name} -> {f.kind}")
    if got_kinds == expected:
        print(f"  all {len(expected)} declared defects caught, none extra")
    else:
        print(f"  MISMATCH\n    expected: {expected}\n    got:      {got_kinds}")
        ok = False

    print("\n" + ("token validation end-to-end: PASS" if ok else "token validation end-to-end: FAIL"))
    sys.exit(0 if ok else 1)
