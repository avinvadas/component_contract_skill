"""Contract invariants — properties every contract this skill produces must hold.

These are derived from SKILL.md and are component-independent, so they are
written once and applied to every case. They are deliberately separate from a
case's own named regression, which is the one specific mistake that case exists
to catch: invariants keep corpus growth from being linear in effort.

Assertions are property-based, never diff-based — contract prose legitimately
varies between correct runs, so only structural properties are stable.

Run directly to check the fixtures under evals/fixtures/contracts/.
"""
import re, sys, os, json

SUPPORTED = {"Web", "iOS", "Android", "macOS"}
# Treatment-2 sections: intent stated once, then one manifestation row per platform.
TREATMENT_2 = ["2.1", "5.3", "5.4", "6.1"]


class Violation:
    def __init__(self, invariant, detail):
        self.invariant, self.detail = invariant, detail
    def __repr__(self):
        return f"{self.invariant}: {self.detail}"


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def declared_platforms(text):
    fm = frontmatter(text) or {}
    raw = fm.get("platforms", "")
    return [p.strip() for p in raw.strip("[]").split(",") if p.strip()]


def tables(text):
    """Yield (heading, header_cells, [row_cells]) for every markdown table."""
    heading, out = None, []
    lines, i = text.splitlines(), 0
    while i < len(lines):
        if lines[i].startswith("#"):
            heading = lines[i].lstrip("#").strip()
        if lines[i].strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            hdr = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            out.append((heading, hdr, rows))
            i = j
            continue
        i += 1
    return out


def section_body(text, num):
    """Text of section `num` (e.g. '2.1') up to the next heading of same or higher level."""
    m = re.search(rf"^#+[ \t]*{re.escape(num)}\b[^\n]*$", text, re.M)
    if not m:
        return None
    start = m.end()
    nxt = re.search(r"^#{1,3}\s", text[start:], re.M)
    return text[start:start + nxt.start()] if nxt else text[start:]


# ------------------------------------------------------------------ invariants
def inv_frontmatter(text, **kw):
    fm = frontmatter(text)
    if fm is None:
        return [Violation("frontmatter", "no YAML frontmatter block")]
    v = [Violation("frontmatter", f"missing key: {k}")
         for k in ("component", "version", "status", "last_updated", "platforms") if k not in fm]
    plats = declared_platforms(text)
    if not plats:
        v.append(Violation("frontmatter", "platforms is empty"))
    for p in plats:
        if p not in SUPPORTED:
            v.append(Violation("frontmatter", f"'{p}' is not a supported platform {sorted(SUPPORTED)}"))
    return v


def inv_treatment2_rows(text, **kw):
    """One manifestation row per declared platform — never merged, never omitted."""
    plats, v = declared_platforms(text), []
    for num in TREATMENT_2:
        body = section_body(text, num)
        if body is None:
            continue
        if re.search(r"^\s*(None|N/A)\b", body.strip(), re.I):
            continue
        for heading, hdr, rows in tables(body):
            if not hdr or hdr[0].lower() != "platform":
                continue
            seen = [r[0] for r in rows if r]
            for p in plats:
                if not any(p == s or re.search(rf"\b{re.escape(p)}\b", s) for s in seen):
                    v.append(Violation(f"treatment-2 rows (§{num})", f"no row for declared platform '{p}'"))
            for s in seen:
                if "," in s:
                    v.append(Violation(f"treatment-2 rows (§{num})",
                                       f"platforms merged into one row ('{s}') — treatment 2 never merges"))
    return v


def inv_no_cross_reference(text, **kw):
    """A platform's value is never 'same as' another's — see Phase 5, treatment 2."""
    v = []
    for heading, hdr, rows in tables(text):
        for r in rows:
            for c in r:
                if re.search(r"\bsame as (Web|iOS|Android|macOS|above)\b", c, re.I):
                    v.append(Violation("no cross-reference", f"under '{heading}': cell reads '{c[:60]}'"))
    return v


def inv_design_intent(text, **kw):
    body = section_body(text, "Design Intent") or ""
    if not body.strip():
        m = re.search(r"^##\s*Design Intent\s*$", text, re.M)
        if not m:
            return [Violation("design intent", "section missing")]
        nxt = re.search(r"^(##|---)", text[m.end():], re.M)
        body = text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]
    body = re.sub(r"\n-{3,}\s*$", "", body.strip()).strip()  # trailing rule is not a sentence
    if not body:
        return [Violation("design intent", "section is empty")]
    v = []
    if re.search(r"\b(delegat|owns everything|is responsible for its children)\w*", body, re.I):
        v.append(Violation("design intent",
                           "contains ownership/delegation language — that belongs solely in §2.2's Accepts"))
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    if len(sentences) > 1:
        v.append(Violation("design intent", f"{len(sentences)} sentences; must be exactly one"))
    return v


def inv_no_fixed_heading_level(text, **kw):
    """Heading level is set by the mounting page, never by the component."""
    v = []
    for heading, hdr, rows in tables(text):
        for r in rows:
            joined = " | ".join(r).replace("`", "")
            # A specific level is never correct anywhere in a contract table — the
            # mounting page decides it. Only the full <h1>-<h6> range form is allowed.
            without_range = re.sub(r"<h1>\s*[-–—]\s*<h6>", "", joined)
            if re.search(r"<h[1-6]>", without_range):
                v.append(Violation("no fixed heading level",
                                   f"names a specific level: '{joined[:70]}'"))
    return v


def inv_no_empty_tables(text, **kw):
    return [Violation("no empty tables", f"table under '{heading or 'document'}' has a header and no rows")
            for heading, hdr, rows in tables(text) if not rows]


def inv_pending_is_explicit(text, **kw):
    """An unknown is flagged, never left blank or as a placeholder."""
    v = []
    for heading, hdr, rows in tables(text):
        for r in rows:
            for c in r:
                if c.strip() in ("", "-", "—", "?", "???", "TBD", "TODO", "N/A?"):
                    v.append(Violation("pending is explicit",
                                       f"under '{heading}': empty or placeholder cell '{c}'"))
    return v


INVARIANTS = [inv_frontmatter, inv_treatment2_rows, inv_no_cross_reference, inv_design_intent,
              inv_no_fixed_heading_level, inv_no_empty_tables, inv_pending_is_explicit]


def check_contract(path):
    text = open(path).read()
    out = []
    for fn in INVARIANTS:
        out.extend(fn(text))
    return out


# structure.json invariant — rootElement must be tree-observable per
# references/structural-fact-validation.md, or explicitly unresolved.
OBSERVABLE = re.compile(r"^(tag=|role=|class=|elementType=|unresolved$)")

def check_structure(path):
    d = json.load(open(path))
    exp = d.get("rootElement", {}).get("expect", "")
    if not OBSERVABLE.match(exp):
        return [Violation("rootElement observable",
                          f"'{exp}' is not tree-observable; use tag=/role=/class=/elementType= or 'unresolved'")]
    return []


def check_output_shape(rundir, component):
    """SKILL.md's Output section: every component gets its own directory,
    [ComponentName]/, holding everything the interview produced. Checked at the
    directory level because no amount of reading one contract file can tell you
    the file landed in the wrong place — and a consumer looking for
    Badge/Badge.md does not find Badge.md."""
    v, comp = [], os.path.join(rundir, component)
    loose = [f for f in os.listdir(rundir)
             if f.startswith(component + ".") and os.path.isfile(os.path.join(rundir, f))]
    if not os.path.isdir(comp):
        v.append(Violation("output shape",
                           f"no {component}/ directory; SKILL.md's Output section requires one"))
    if loose:
        v.append(Violation("output shape",
                           f"{len(loose)} file(s) written loose beside {component}/ "
                           f"instead of inside it: {', '.join(sorted(loose))}"))
    return v


if __name__ == "__main__":
    FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fixtures", "contracts")
    man = json.load(open(os.path.join(FIX, "manifest.json")))
    ok = True

    print("Specificity — a conforming contract must produce no violations:")
    good = check_contract(os.path.join(FIX, "good.md"))
    print(f"  good.md: {len(good)} violation(s)")
    for g in good:
        print(f"     unexpected: {g}")
    ok &= not good

    print("\nSensitivity — each deliberate violation must be caught:")
    bad = check_contract(os.path.join(FIX, "broken.md"))
    caught = {v.invariant.split(" (")[0] for v in bad}
    for v in bad:
        print(f"     caught: {v}")
    missing = [e for e in man["expect_violations"] if e not in caught]
    print(f"\n  {len(caught)} distinct invariant(s) tripped; expected {len(man['expect_violations'])}")
    if missing:
        print(f"  MISSED: {missing}")
        ok = False

    print("\n" + ("contract invariants: PASS" if ok else "contract invariants: FAIL"))
    sys.exit(0 if ok else 1)
