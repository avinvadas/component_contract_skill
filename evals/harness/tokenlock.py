"""Steps 4-5 of references/token-naming-validation.md — the stateful half.

tokencheck.py covers Steps 1-3 (canonicalize, generate, match at depth). That
part was already verified against the fixture tree. This module covers the
locking and per-run consistency rules, which is where the three defects found
on the first real run actually live:

  1. silent wrong-lock       -> a lock now requires an explicitly confirmed name
  2. row ambiguity           -> lock on first UNAMBIGUOUS success, not first success
  3. depth non-injectivity   -> depth > 1 requires a uniqueness check first

Run directly to execute the self-tests that exercise each.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tokencheck import canonical_words, generate, match, strip_file_prefix, ROWS

ALERT, WARNING, INFO = "ALERT", "WARNING", "INFO"


class Finding:
    def __init__(self, kind, severity, name, detail):
        self.kind, self.severity, self.name, self.detail = kind, severity, name, detail
    def __repr__(self):
        return f"[{self.severity}] {self.kind}: {self.name} — {self.detail}"


class Lock:
    """A platform's locked naming convention: three independent axes."""
    def __init__(self, row=None, prefix=None, depth=None, confirmed=False):
        self.row, self.prefix, self.depth, self.confirmed = row, prefix, depth, confirmed
    def is_set(self):
        return self.row is not None and self.depth is not None
    def __repr__(self):
        return f"Lock(row={self.row}, prefix={self.prefix}, depth={self.depth}, confirmed={self.confirmed})"


def depth_is_verifiable(token_map, depth, row):
    """Step 4, fix 3 — a depth is only usable while names stay distinct.

    Returns (ok, collisions). Leading truncation discards the segments that
    distinguish tokens; past some depth two different tokens render identically
    and a wrong binding would pass."""
    forms = {}
    for path in token_map:
        w = canonical_words(path)
        if depth >= len(w):
            continue
        forms.setdefault(generate(w[depth:], row), []).append(path)
    collisions = {f: ps for f, ps in forms.items() if len(ps) > 1}
    return (not collisions), collisions


def attempt_lock(candidate, token_path, token_map, confirmed=False):
    """Step 4 — try to establish the lock from one known-correct name.

    Returns (Lock or None, [Finding]). A lock is only returned when the match is
    unambiguous, the depth is verifiable, AND the name was confirmed correct."""
    words = canonical_words(token_path)
    hits = match(candidate, words)
    findings = []

    if not hits:
        return None, [Finding("Unknown token / structural mismatch", ALERT, candidate,
                              f"matches no row at any depth of {token_path}")]

    # Both blocking conditions are independently true or false — report every one
    # that applies rather than returning on the first. A name can be ambiguous AND
    # sit at a collapsing depth, and hearing only "keep looking" would send you
    # looking for a name that cannot exist at that depth.
    rows_hit = sorted({r for r, _ in hits})
    ambiguous = len(rows_hit) > 1
    if ambiguous:
        # fix 2 — a multi-row match is a pass that carries no information
        findings.append(Finding("Row undetermined", INFO, candidate,
                                f"matches {len(rows_hit)} rows at once ({', '.join(rows_hit)}) — "
                                f"cannot fix the convention; keep looking"))

    # fix 3 — depth verifiability is a property of the token map at that depth,
    # independent of whether this name happens to determine a row
    depth_blocked = False
    for depth in sorted({d for _, d in hits}):
        if depth <= 1:
            continue
        ok, collisions = depth_is_verifiable(token_map, depth, rows_hit[0])
        if not ok:
            depth_blocked = True
            example = next(iter(collisions.items()))
            findings.append(Finding("Depth not verifiable", ALERT, candidate,
                                    f"at depth {depth}, {len(collisions)} name(s) are shared by "
                                    f"multiple tokens (e.g. '{example[0]}' <- {', '.join(example[1])}). "
                                    f"A wrong binding would pass; check stops for this platform"))

    if ambiguous or depth_blocked:
        return None, findings

    row, depth = hits[0]

    if depth > 0:
        findings.append(Finding("Namespace scoping detected", WARNING, candidate,
                                f"omits leading segment(s) {words[:depth]} — confirm intentional"))

    if not confirmed:
        # fix 1 — never lock silently on an unverified name
        findings.append(Finding("Lock not established", WARNING, candidate,
                                "a lock must come from a name already known correct; "
                                "confirm before it becomes the standard for every later name"))
        return None, findings

    return Lock(row, None, depth, confirmed=True), findings


def check_against_lock(candidate, token_path, lock):
    """Step 5 — every subsequent name is checked against all three locked axes."""
    words = canonical_words(token_path)
    hits = match(candidate, words)
    if not hits:
        return Finding("Unknown token / structural mismatch", ALERT, candidate,
                       f"matches no row at any depth of {token_path}")
    for row, depth in hits:
        if row == lock.row and depth == lock.depth:
            return None
    rows_hit = {r for r, _ in hits}
    if lock.row in rows_hit:
        d = [d for r, d in hits if r == lock.row][0]
        return Finding("Inconsistent scoping", ALERT, candidate,
                       f"omits {d} leading segment(s), but this platform is locked to {lock.depth}")
    return Finding("Inconsistent convention", ALERT, candidate,
                   f"matches {sorted(rows_hit)}, but this platform is locked to {lock.row}")


# ---------------------------------------------------------------- self-tests
def _t(label, cond):
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")
    return cond

if __name__ == "__main__":
    from tokencheck import load_paths
    tree = load_paths(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "fixtures", "tokens", "design-tokens.json"))
    ok = True
    print("Fix 1 — silent wrong-lock is prevented:")
    lock, f = attempt_lock("--primitive-color-purple-500", "primitive.color.purple.500", tree)
    ok &= _t("unconfirmed name does not produce a lock", lock is None)
    ok &= _t("  and says why", any(x.kind == "Lock not established" for x in f))
    lock, f = attempt_lock("--primitive-color-purple-500", "primitive.color.purple.500", tree, confirmed=True)
    ok &= _t("confirmed name locks kebab at depth 0", lock and lock.row == "kebab" and lock.depth == 0)

    print("\nFix 2 — an ambiguous name does not fix the row:")
    lock, f = attempt_lock("white", "primitive.color.white", tree, confirmed=True)
    ok &= _t("multi-row match yields no lock", lock is None)
    ok &= _t("  reported as undetermined, not as a failure",
             any(x.kind == "Row undetermined" and x.severity == INFO for x in f))
    lock, f = attempt_lock("40", "primitive.color.black-alpha.40", tree, confirmed=True)
    ok &= _t("numeric tail (matches all 7 rows) yields no lock", lock is None)

    print("\nFix 3 — an unverifiable depth stops the check:")
    tm = ["component.button.radius", "component.toast.radius", "component.badge.radius"]
    lock, f = attempt_lock("radius", "component.button.radius", tm, confirmed=True)
    ok &= _t("colliding depth-2 name yields no lock", lock is None)
    ok &= _t("  reported as Depth not verifiable (ALERT)",
             any(x.kind == "Depth not verifiable" and x.severity == ALERT for x in f))
    okd, _ = depth_is_verifiable(tree, 1, "kebab")
    ok &= _t("depth 1 on the real tree is verifiable", okd)
    okd, coll = depth_is_verifiable(tree, 3, "kebab")
    ok &= _t("depth 3 on the real tree is not", (not okd) and len(coll) > 0)

    print("\nStep 5 — subsequent names checked against the lock:")
    lock = Lock("kebab", None, 0, confirmed=True)
    ok &= _t("correct name passes",
             check_against_lock("--primitive-color-gray-500", "primitive.color.gray.500", lock) is None)
    r = check_against_lock("primitive_color_gray_500", "primitive.color.gray.500", lock)
    ok &= _t("different row -> Inconsistent convention", r and r.kind == "Inconsistent convention")
    r = check_against_lock("--gray-500", "primitive.color.gray.500", lock)
    ok &= _t("different depth -> Inconsistent scoping", r and r.kind == "Inconsistent scoping")
    r = check_against_lock("--primitive-color-500-gray", "primitive.color.gray.500", lock)
    ok &= _t("reordered -> structural mismatch", r and "structural mismatch" in r.kind)

    print("\n" + ("all self-tests passed" if ok else "FAILURES ABOVE"))
    sys.exit(0 if ok else 1)
