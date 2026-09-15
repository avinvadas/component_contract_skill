#!/usr/bin/env python3
"""Generate the platform-neutral RESOLVED VIEW.

Organised by the contract's own chapters, so a reader moving between source and view is not
relearning the layout. Origin is a COLUMN, not a grouping: chapters answer "what kind of fact
is this", origin answers "is this mine to change".
"""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from resolve import SRC, LIB, parse_frontmatter, requirement_rows, parse_tables  # noqa: E402

NL = "\n"
fm, body = parse_frontmatter((SRC / "Button.md").read_text())
arch_text = (LIB / ("archetypes/%s.md" % fm["archetype"])).read_text()
arch_fm, arch_body = parse_frontmatter(arch_text)
policy_body = (SRC / "system/policy.md").read_text()

ORIGIN, rows = {}, []
for src, label in ((arch_body, "archetype `%s`" % fm["archetype"]),
                   (policy_body, "policy"), (body, "this component")):
    for r in requirement_rows(src):
        ORIGIN[r["id"]] = label
        rows.append(r)

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
    return md_table(["statement", "when", "origin", "id"],
                    ["| %s | %s | %s | <sub>id-%s</sub> |"
                     % (r["statement"], r.get("required", "always"), ORIGIN[r["id"]], r["id"])
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
         % (fm["component"], fm["version"], fm["archetype"], arch_fm["version"]))
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
P.append(md_table(["property", "token", "when"],
                  ["| %s | %s | %s |" % (t["property"], t["token"], t["required"]) for t in tokens]))
P.append("### Requirements")
P.append("")
P.append(reqs("Appearance"))
P.append("### Platform distinctions")
P.append("")
P.append(divergences())
P.append("## 4. Behavior")
P.append("")
P.append("### Requirements")
P.append("")
P.append(reqs("Behavior"))
P.append("### Events")
P.append("")
P.append(md_table(["direction", "name", "payload", "when"],
                  ["| %s | %s | %s | %s |" % (e["direction"], e["name"], e["payload"], e["when"])
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
P.append("%d requirements — %d local, %d inherited, %d policy · %d zones · %d token slots · %d props"
         % (len(rows), n_local, n_arch, n_pol, len(zones), len(tokens), len(props)))

out = pathlib.Path(__file__).parent / "Button.resolved.md"
out.write_text(NL.join(P) + NL)
print("wrote %s: %d lines, %d requirements" % (out.name, len(P), len(rows)))
