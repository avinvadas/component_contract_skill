#!/usr/bin/env python3
"""Generate the platform-neutral RESOLVED VIEW.

Organised by the contract's own chapters, so a reader moving between source and view is not
relearning the layout. Origin is a COLUMN, not a grouping: chapters answer "what kind of fact
is this", origin answers "is this mine to change".
"""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from resolve import (SRC, LIB, parse_frontmatter, requirement_rows,  # noqa: E402
                     parse_tables, resolve_slots)
import machine as sm  # noqa: E402
COMPONENT = sys.argv[1] if len(sys.argv) > 1 else "Button"

NL = "\n"
fm, body = parse_frontmatter((SRC / (COMPONENT + ".md")).read_text())
arch_text = (LIB / ("role-archetypes/%s.md" % fm["role-archetype"])).read_text()
arch_fm, arch_body = parse_frontmatter(arch_text)
policy_body = (SRC / "system/policy.md").read_text()

ORIGIN, rows = {}, []
for src, label in ((arch_body, "archetype `%s`" % fm["role-archetype"]),
                   (policy_body, "policy"), (body, "this component")):
    for r in requirement_rows(src):
        ORIGIN[r["id"]] = label
        rows.append(r)

# ---- token slots -------------------------------------------------------------------
# The canonical document carries the five-way state, because a machine routes on it.
# A reader does not need a five-way taxonomy — they need to know whether a property is
# bound, and if not, who fixes it. So the view renders two things: a status per row, and
# a gap table addressed to whoever owns the token tree.
SLOTS = resolve_slots(body, fm)

STATUS_LABEL = {
    "bound":            "bound",
    "not-applicable":   "n/a",
    "absent-from-tree": "**absent from tree**",
    "ambiguous":        "**ambiguous**",
    "dimension-unmet":  "**state unexpressed**",
    "unmapped-leaf":    "**unreadable token name**",
}

def slot_label(s_):
    return s_["property"] + ("@" + s_["state"] if s_["state"] else "")

def token_table():
    body_rows = []
    for s_ in SLOTS:
        tok = ("`%s`" % s_["token"]) if s_["token"] else "—"
        status = STATUS_LABEL.get(s_["status"], s_["status"])
        if s_["status"] == "not-applicable":
            status = "n/a — " + s_["detail"]
        body_rows.append("| %s | %s | %s | %s |" % (s_.get("when", "always"),
                                                    s_["property"], tok, status))
    return md_table(["when", "property", "token", "status"], body_rows)

def gap_table():
    gaps = [s_ for s_ in SLOTS if s_["status"] not in ("bound", "not-applicable")]
    if not gaps:
        return "*None. Every declared property resolves.*" + NL
    intro = ("%d propert%s could not resolve. These are fixed in the token tree, not in "
             "this contract — leave the cells above unbound until the tree can express them."
             % (len(gaps), "y" if len(gaps) == 1 else "ies")) + NL + NL
    rows_ = []
    for s_ in gaps:
        if s_["status"] == "absent-from-tree":
            need = "no token anywhere expresses this property"
            fix = "add `%s`" % s_["detail"]
        elif s_["status"] == "dimension-unmet":
            need = "`%s` exists but carries no `%s` state" % (s_["detail"], s_["state"])
            fix = "add a `%s` variant of that token" % s_["state"]
        elif s_["status"] == "ambiguous":
            cands = s_["detail"] if isinstance(s_["detail"], list) else [str(s_["detail"])]
            need = "%d candidates; scope and dimension did not narrow it" % len(cands)
            fix = "pin one: " + ", ".join("`%s`" % c for c in cands[:3])
        else:
            need, fix = str(s_["detail"]), "extend the leaf map in design-system-context"
        rows_.append("| %s | %s | %s |" % (slot_label(s_), need, fix))
    return intro + md_table(["property", "what is wrong", "what to do"], rows_)

# ---- state machine -----------------------------------------------------------------
# The reader sees the machine as a machine: every authored transition in one table, origin as
# a column like everywhere else. Closure is NOT tabulated — it is generated, nobody wrote it,
# and listing it would bury the rows someone did write. It is named in one line, so a reader
# knows those checks exist and what they cover.
def machine_section():
    arch_rows = sm.machine_rows(parse_tables(arch_body))
    own_rows = sm.machine_rows(parse_tables(body))
    if not arch_rows and not own_rows:
        return "*No state machine.*" + NL
    merged, _ = sm.build(arch_rows + own_rows)
    rows_ = []
    for r, origin in [(r, "archetype `%s`" % fm["role-archetype"]) for r in arch_rows] + \
                     [(r, "this component") for r in own_rows]:
        rows_.append("| %s | %s | %s | %s | %s |" % (r["from"], r["event"], r["to"], origin,
                                                    ("id-" + r["id"]) if r.get("id", "—") not in ("—", "-", "") else "—"))
    out = md_table(["from", "event", "to", "origin", "id"], rows_)
    grid = len(merged["states"]) * len(merged["events"])
    if merged["closure"]:
        cells = ", ".join("`%s × %s`" % (c["from"], c["event"]) for c in merged["closure"])
        out += (NL + "**Closure.** %d states × %d events = %d cells. The %d nobody wrote are each "
                "checked to change no state: %s." % (len(merged["states"]), len(merged["events"]),
                                                     grid, len(merged["closure"]), cells) + NL)
    return out

FALLBACK = {"layout": "Structure", "order": "Structure", "containment": "Structure",
            "token": "Appearance", "event": "Behavior"}

def chapter_of(r):
    return r.get("chapter") or FALLBACK.get(r["observe"], "Accessibility")

def md_table(headers, body_rows):
    if not body_rows:
        return "*None.*" + NL
    head = "| " + " | ".join(headers) + " |" + NL + "|" + "---|" * len(headers)
    return head + NL + NL.join(body_rows) + NL

def reqs(chapter):
    sel = [r for r in rows if chapter_of(r) == chapter]
    sel.sort(key=lambda r: (ORIGIN[r["id"]] != "this component", r["id"]))
    def when(r):
        w = r.get("when") or r.get("required") or "always"
        return "—" if w == "always" else w      # source stays explicit; the view stays light
    return md_table(["when", "statement", "origin", "id"],
                    ["| %s | %s | %s | id-%s |"
                     % (when(r), r["statement"], ORIGIN[r["id"]], r["id"])
                     for r in sel])

def native_backing():
    m = re.search(r"\| Platform \| Native backing \|\n\|[-| ]+\|\n((?:\|.*\|\n)+)", arch_text)
    if m:
        return "| Platform | Native backing |" + NL + "|---|---|" + NL + m.group(1)
    return md_table(["Platform", "Native backing"],
                    ["| %s | native control available |" % p for p in fm["platforms"]])

zones, tokens, props, events, diverge = [], [], [], [], []
for headers, rws in parse_tables(body):
    if "zone" in headers:        zones = rws
    elif "token" in headers:     tokens = rws
    elif "prop" in headers:      props += rws
    elif "direction" in headers: events = rws
    elif "deviation" in headers: diverge += rws

def zone_table(required):
    sel = [z for z in zones if z["cardinality"].startswith("0") != required]
    return md_table(["zone", "accepts", "cardinality", "position", "if absent"],
                    ["| %s | %s | %s | %s | %s |" % (z["zone"], z["accepts"], z["cardinality"],
                                                     z["position"], z["absent"]) for z in sel])

def divergences():
    if not diverge:
        return "*None recorded. Every platform satisfies the above identically.*" + NL
    return md_table(["platform", "affects", "deviation", "reason"],
                    ["| %s | %s | %s | %s |" % (d["platform"], d["affects"], d["deviation"],
                                                d["reason"]) for d in diverge])

m = re.search(r"## 1\. Intent\n\n(.*?)\n\n##", body, re.S)
intent = m.group(1).strip() if m else ""
n_local = sum(1 for r in rows if ORIGIN[r["id"]] == "this component")
n_arch = sum(1 for r in rows if ORIGIN[r["id"]].startswith("archetype"))
n_pol = sum(1 for r in rows if ORIGIN[r["id"]] == "policy")

P = []
P.append("# %s — resolved" % fm["component"])
P.append("")
P.append("> **Generated. Do not edit.** Source: `%s.md` v%s + archetype `%s` v%s + system policy."
         % (fm["component"], fm["version"], fm["role-archetype"], arch_fm["version"]))
P.append("> **Platform-neutral** — what the component *is*, before any platform's vocabulary.")
P.append("> How each requirement is *observed* per platform is in `2-canonical/`.")
P.append("")
P.append("**Origin** marks what is yours to change. *this component* — decided in your interview. "
         "*archetype* — a fact about what platforms provide free; changing it means a platform "
         "changed. *policy* — your design system's cross-cutting commitment.")
P.append("")
P.append("## 1. Intent")
P.append("")
P.append(intent)
P.append("")
P.append("## 2. Structure")
P.append("")
P.append("### Native backing")
P.append("")
P.append("Where a platform gives you this free, and where you build it by hand.")
P.append("")
P.append(native_backing())
P.append("### Requirements")
P.append("")
P.append(reqs("Structure"))
P.append("### Required children")
P.append("")
P.append(zone_table(True))
P.append("### Optional children")
P.append("")
P.append(zone_table(False))
P.append("## 3. Appearance")
P.append("")
P.append("### Tokenised properties")
P.append("")
P.append(token_table())
P.append("### Token gaps")
P.append("")
P.append(gap_table())
P.append("### Requirements")
P.append("")
P.append(reqs("Appearance"))
P.append("### Platform distinctions")
P.append("")
P.append(divergences())
P.append("## 4. Behavior")
P.append("")
P.append("### State machine")
P.append("")
P.append(machine_section())
P.append("### Requirements")
P.append("")
P.append(reqs("Behavior"))
P.append("### Events")
P.append("")
P.append(md_table(["when", "direction", "name", "payload"],
                  ["| %s | %s | %s | %s |" % (e.get("when", ""), e["direction"], e["name"], e["payload"])
                   for e in events]))
P.append("## 5. Accessibility")
P.append("")
P.append("Reviewable as an aspect: everything governing how the component is exposed, named, "
         "traversed and announced.")
P.append("")
P.append(reqs("Accessibility"))
P.append("### Platform distinctions")
P.append("")
P.append(divergences())
P.append("## What a consumer may pass")
P.append("")
P.append(md_table(["prop", "type", "required", "default"],
                  ["| %s | %s | %s | %s |" % (p["prop"], p["type"], p["required"], p["default"])
                   for p in props]))
P.append("---")
P.append("")
# `9 token slots` hid the state. The gap count is the number someone needs at a glance,
# so it goes in the summary line rather than only in the table above.
n_bound = sum(1 for s_ in SLOTS if s_["status"] == "bound")
n_na    = sum(1 for s_ in SLOTS if s_["status"] == "not-applicable")
n_gap   = len(SLOTS) - n_bound - n_na
slot_summary = "%d token slots — %d bound, %d gap%s, %d n/a" % (
    len(SLOTS), n_bound, n_gap, "" if n_gap == 1 else "s", n_na)
P.append("%d requirements — %d local, %d inherited, %d policy · %d zones · %s · %d props"
         % (len(rows), n_local, n_arch, n_pol, len(zones), slot_summary, len(props)))

out = pathlib.Path(__file__).parent / (COMPONENT + ".resolved.md")
out.write_text(NL.join(P) + NL)
print("wrote %s: %d lines, %d requirements" % (out.name, len(P), len(rows)))
