#!/usr/bin/env python3
"""Generate the platform-neutral RESOLVED VIEW of a contract.

The contract .md is source: thin, deltas only. The archetype is shared: abstract by
construction. Neither reads as "what this component is", which is the signature problem of
any delta-based inheritance — CSS rules vs computed styles, a class vs its full method list.

The answer there is never to merge the source files. It is a computed view. This is it.
"""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from resolve import (SRC, LIB, parse_frontmatter, requirement_rows, parse_tables)  # noqa: E402

fm, body = parse_frontmatter((SRC / "Button.md").read_text())
arch_fm, arch_body = parse_frontmatter((LIB / f"archetypes/{fm['archetype']}.md").read_text())
policy_body = (SRC / "system/policy.md").read_text()

inherited = requirement_rows(arch_body)
policy = requirement_rows(policy_body)
local = requirement_rows(body)

def intent(text):
    m = re.search(r"## 1\. Intent\n\n(.*?)\n\n##", text, re.S)
    return m.group(1).strip() if m else ""

def table(title, rows, origin, extra=""):
    if not rows:
        return ""
    out = [f"\n### {title}\n", f"*{origin}*\n",
           "| id | statement | observe | kind | required |", "|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['id']} | {r['statement']} | {r['observe']} | {r['kind']} | {r.get('required','always')} |")
    return "\n".join(out) + "\n" + extra

# zones and tokens come straight from the contract's own tables
zones, tokens, props = [], [], []
for headers, rows in parse_tables(body):
    if "zone" in headers:        zones = rows
    elif "token" in headers:     tokens = rows
    elif "prop" in headers:      props += rows

doc = f"""# {fm['component']} — resolved

> **Generated. Do not edit.** Source: `Button.md` v{fm['version']} +
> archetype `{fm['archetype']}` v{arch_fm['version']} + system policy.
> Platform-neutral: this is what the component *is*, before any platform's vocabulary.

{intent(body)}

## What this component must do

Every requirement, from all three layers, in one place. **The origin column is the point** —
inherited rows are facts about platforms and are not yours to negotiate; local rows are
decisions your team made and can revisit.
{table(f"Inherited from archetype `{fm['archetype']}`", inherited,
       f"Facts about what platforms provide free. Changing these means changing the archetype, "
       f"which means a platform guarantee changed. See `system/archetypes/{fm['archetype']}.md` "
       f"for provenance and for what was deliberately left out.")}
{table("From system policy", policy,
       "Your design system's cross-cutting commitments. Apply to every archetype, including "
       "those with no native backing. See `system/policy.md`.")}
{table("Specific to this component", local,
       "Decided in this contract's interview. The only rows here that are yours to change "
       "without changing something shared.")}

## What it contains

| zone | accepts | cardinality | position | if absent |
|---|---|---|---|---|
""" + "\n".join(
    f"| {z['zone']} | {z['accepts']} | {z['cardinality']} | {z['position']} | {z['absent']} |" for z in zones
) + """

## What it looks like

| property | token | when |
|---|---|---|
""" + "\n".join(f"| {t['property']} | {t['token']} | {t['required']} |" for t in tokens) + """

## What a consumer may pass

| prop | type | required | default |
|---|---|---|---|
""" + "\n".join(f"| {p['prop']} | {p['type']} | {p['required']} | {p['default']} |" for p in props) + f"""

---

**Counts.** {len(inherited)} inherited · {len(policy)} policy · {len(local)} local =
**{len(inherited)+len(policy)+len(local)} requirements**, {len(zones)} zones, {len(tokens)} token
slots, {len(props)} props.

Platform resolution — which of these bind where, and how each is observed — is in the
canonical documents, one per platform in `2-canonical/`.
"""

out = pathlib.Path(__file__).parent / "Button.resolved.md"
out.write_text(doc)
print(f"wrote {out.name}: {len(doc.splitlines())} lines, "
      f"{len(inherited)+len(policy)+len(local)} requirements from 3 layers")
