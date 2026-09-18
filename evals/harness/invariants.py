"""Contract invariants — properties every contract this skill produces must hold.

Derived from SKILL.md and `docs/contract-md-format-spec.md`, component-independent, so they
are written once and applied to every case. A case's own named regression — the one specific
mistake it exists to catch — stays with the case; invariants keep corpus growth sublinear.

Assertions are property-based, never diff-based: contract prose legitimately varies between
correct runs, so only structural properties are stable.

**The resolver is the deepest invariant.** Anything `scripts/resolve.py` can decide — unknown
conditions, missing bindings, a pinned token absent from the tree, a machine with two answers
for one cell, an id colliding with an inherited one — is checked by running it, not restated
here. Duplicating those rules in a second implementation is how the two drift, which this
project has already watched happen once with the condition vocabulary.

What stays here is what the resolver cannot see: whether the document is shaped like a
contract, and whether its statements are written at the right altitude.

Run directly to check the fixtures under evals/fixtures/contracts/.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# Platform ids are lowercase because they key the bindings files; the display names in Q2
# ("Web", "iOS") are for people.
SUPPORTED = {"web", "ios", "android", "macos"}
CHAPTERS = ["1. Intent", "2. Structure", "3. Composition", "4. Appearance",
            "5. Behavior", "6. Accessibility"]
CHAPTER_PREFIX = {"2": "STR", "3": "CMP", "4": "APP", "5": "BEH", "6": "ACC"}

# A statement names a platform's vocabulary — the mechanical form of Phase 5's translation
# check. These are what a requirement must NOT contain, because a binding holds them instead.
PLATFORM_VOCAB = re.compile(
    r"(<[a-z][a-z0-9]*\s*/?>|`<[^`]+>`|\baria-[a-z]+|\brole=|"
    r"\bUI[A-Z]\w+|\bNS[A-Z]\w+|\bSwiftUI\b|\bCompose\b|\bRole\.[A-Z]|"
    r"\baddEventListener\b|\bAutomationProperties\b|"
    r"\bpress(?:es|ing)? (?:Tab|Enter|Escape|Space)\b|\bthe Tab key\b)")
PLACEHOLDER = re.compile(r"\b(TBD|TODO|FIXME|\?\?\?|XXX)\b")


class Violation:
    def __init__(self, invariant, detail):
        self.invariant, self.detail = invariant, detail

    def __repr__(self):
        return "%s: %s" % (self.invariant, self.detail)


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
            fm[k.strip()] = v
    return fm


def requirement_rows(text):
    """(row cells, header cells) for every row of every requirement-shaped table."""
    out, headers = [], None
    for line in text.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
            if headers is None:
                headers = cells
            elif set("".join(cells)) <= set("-: "):
                continue
            else:
                out.append((dict(zip(headers, cells)), headers))
        else:
            headers = None
    return out


# ---- invariants ----------------------------------------------------------------------
def inv_frontmatter(text):
    fm = frontmatter(text)
    if fm is None:
        return [Violation("frontmatter", "no YAML frontmatter block")]
    v = []
    for key in ("component", "version", "role-archetype", "platforms"):
        if key not in fm:
            v.append(Violation("frontmatter", "missing `%s`" % key))
    return v


def inv_platform_ids(text):
    fm = frontmatter(text) or {}
    plats = fm.get("platforms") or []
    bad = [p for p in plats if p not in SUPPORTED]
    if bad:
        return [Violation("platform ids",
                          "%s — platform ids are lowercase and from %s, because they key the "
                          "bindings file" % (", ".join(bad), sorted(SUPPORTED)))]
    return []


def inv_six_chapters(text):
    found = [c for c in CHAPTERS if re.search(r"^##\s+%s\s*$" % re.escape(c), text, re.M)]
    if len(found) != len(CHAPTERS):
        missing = [c for c in CHAPTERS if c not in found]
        return [Violation("six chapters", "missing %s — an absent chapter is indistinguishable "
                                          "from an overlooked one" % ", ".join(missing))]
    order = [text.index("## " + c) for c in CHAPTERS]
    if order != sorted(order):
        return [Violation("six chapters", "chapters are out of order")]
    return []


def inv_id_discipline(text):
    v, seen = [], {}
    for row, headers in requirement_rows(text):
        if "id" not in row or "statement" not in headers and "property" not in headers:
            continue
        rid = row["id"]
        if rid in ("—", "-", ""):
            continue
        if not rid.startswith("id-"):
            v.append(Violation("id discipline", "%r lacks the `id-` prefix" % rid))
        bare = rid[3:] if rid.startswith("id-") else rid
        if bare in seen:
            v.append(Violation("id discipline", "%s appears more than once" % bare))
        seen[bare] = True
    return v


def inv_when_vocabulary(text, conditions=None):
    if conditions is None:
        with open(os.path.join(ROOT, "system/vocabulary/conditions.json")) as f:
            conditions = set(json.load(f)["conditions"])
    zones = {row["zone"] for row, h in requirement_rows(text) if "zone" in h and "zone" in row}
    transitions = {row["id"].replace("id-", "") for row, h in requirement_rows(text)
                   if {"from", "event", "to"} <= set(h) and "id" in row}
    v = []
    for row, headers in requirement_rows(text):
        w = row.get("when", "")
        if not w or w == "always" or "statement" not in headers and "property" not in headers:
            continue
        if not w.startswith("when:"):
            v.append(Violation("when vocabulary", "%r is not `always` or `when:<condition>`" % w))
            continue
        for cond in w[len("when:"):].split(","):
            cond = cond.strip()
            if cond in conditions:
                continue
            if cond.endswith("_present") and cond[: -len("_present")] in zones:
                continue
            if cond.startswith("following:") and cond[len("following:"):] in transitions:
                continue
            v.append(Violation("when vocabulary", "%r is not in the closed vocabulary" % cond))
    return v


def inv_platform_neutral_statement(text):
    v = []
    for row, headers in requirement_rows(text):
        st = row.get("statement")
        if not st:
            continue
        m = PLATFORM_VOCAB.search(st)
        if m:
            v.append(Violation("platform-neutral statement",
                               "%s names %r — that belongs in the bindings file"
                               % (row.get("id", "?"), m.group(0))))
    return v


def inv_no_fixed_heading_level(text):
    m = re.search(r"`?<h[1-6]>`?", text)
    if m:
        return [Violation("no fixed heading level",
                          "%s — heading level is set by the consuming page's outline"
                          % m.group(0))]
    return []


def inv_pending_is_explicit(text):
    v = []
    for row, _ in requirement_rows(text):
        for cell in row.values():
            if PLACEHOLDER.search(cell or ""):
                v.append(Violation("pending is explicit",
                                   "%r — an unresolved value is `—` (resolve it) or "
                                   "`n/a — reason`, never a placeholder" % cell))
    return v


def inv_no_cross_reference(text):
    m = re.search(r"\b(same as|identical to|as (?:above|Web|iOS|Android))\b", text, re.I)
    if m:
        return [Violation("no cross-reference",
                          "%r — a platform difference is a binding or a divergence row, never "
                          "a reference to another row" % m.group(0))]
    return []


INVARIANTS = [inv_frontmatter, inv_platform_ids, inv_six_chapters, inv_id_discipline,
              inv_when_vocabulary, inv_platform_neutral_statement,
              inv_no_fixed_heading_level, inv_pending_is_explicit, inv_no_cross_reference]


def check_contract(path):
    text = open(path).read()
    out = []
    for fn in INVARIANTS:
        out.extend(fn(text))
    return out


def check_resolves(path, out_dir=None):
    """The deepest invariant: the contract resolves with zero lint findings.

    Token gaps are NOT violations — the document is fine and the token tree cannot express
    something yet, which is a task for whoever owns the tree.
    """
    import tempfile
    out_dir = out_dir or tempfile.mkdtemp()
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts/resolve.py"), path,
                        "--out", out_dir], capture_output=True, text=True)
    if r.returncode == 0:
        return []
    findings = [l.strip("  - ") for l in r.stdout.splitlines() if l.startswith("  - ")]
    return [Violation("resolves clean", f) for f in findings] or \
           [Violation("resolves clean", (r.stderr or r.stdout).strip().splitlines()[-1])]


def check_output_shape(rundir, component):
    """SKILL.md's Output section: every component gets its own directory holding everything
    the interview produced. No amount of reading one contract tells you it landed in the
    wrong place — and a consumer looking for Badge/Badge.md does not find Badge.md."""
    v, comp = [], os.path.join(rundir, component)
    loose = [f for f in os.listdir(rundir)
             if f.startswith(component + ".") and os.path.isfile(os.path.join(rundir, f))]
    if not os.path.isdir(comp):
        v.append(Violation("output shape", "no %s/ directory" % component))
    else:
        for required in ("%s.md" % component, "%s.bindings.json" % component):
            if not os.path.isfile(os.path.join(comp, required)):
                v.append(Violation("output shape", "%s/ has no %s" % (component, required)))
    if loose:
        v.append(Violation("output shape", "%d file(s) written loose beside %s/: %s"
                           % (len(loose), component, ", ".join(sorted(loose)))))
    return v


if __name__ == "__main__":
    FIX = os.path.join(ROOT, "evals", "fixtures", "contracts")
    man = json.load(open(os.path.join(FIX, "manifest.json")))
    ok = True

    print("Specificity — a conforming contract must produce no violations:")
    good = check_contract(os.path.join(FIX, "good.md")) + check_resolves(os.path.join(FIX, "good.md"))
    print("  good.md: %d violation(s)" % len(good))
    for g in good:
        print("     unexpected: %s" % g)
    ok &= not good

    print("\nSensitivity — each deliberate violation must be caught:")
    bad = check_contract(os.path.join(FIX, "broken.md"))
    caught = {v.invariant for v in bad}
    for v in bad:
        print("     caught: %s" % v)
    missing = [e for e in man["expect_violations"] if e not in caught]
    print("\n  %d distinct invariant(s) tripped; expected %d" % (len(caught), len(man["expect_violations"])))
    if missing:
        print("  MISSED: %s" % missing)
        ok = False

    print("\n" + ("contract invariants: PASS" if ok else "contract invariants: FAIL"))
    sys.exit(0 if ok else 1)
