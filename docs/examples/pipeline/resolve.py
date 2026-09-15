#!/usr/bin/env python3
"""Level 1 -> Level 2.  Contract.md + archetype + policy  ->  one canonical document
per platform.

This is the resolver the design has been assuming and never had. It exists here to test
the parse contract in `contract-md-format-spec.md`: if a cell in the .md cannot be parsed
deterministically, this is where it shows up.
"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
SRC, OUT = HERE / "1-contract", HERE / "2-canonical"
# The shipped library, not a fixture. This is the checkpoint the source-layer plan names:
# the pipeline proves the mechanism on a hand-made archetype; it proves the library only
# once it resolves against the real one.
LIB = HERE.parent.parent.parent / "system"

# ---- `needs` is DERIVED from `observe`, not authored -------------------------
# Most bindings were boilerplate until this table existed. A bindings file now holds
# only what is genuinely platform-specific: an `expect` value that differs, or an
# explicit n/a. Everything else falls out of the closed observe vocabulary.
NEEDS_BY_OBSERVE = {
    "role":         ["a11y-tree"],
    "name":         ["a11y-tree"],
    "state":        ["a11y-tree"],
    "containment":  ["a11y-tree"],
    "order":        ["a11y-tree"],
    "focus":        ["focus"],
    "layout":       ["geometry"],
    "event":        ["interaction"],
    "announcement": ["announcement"],
    "token":        ["source"],
    "prop":         ["source"],
}

# ---- condition vocabulary (closed) ------------------------------------------
CONDITIONS = {
    "hardware_keyboard": ("environment", "hardware_keyboard", True),
    "touch_input":       ("environment", "touch_input", True),
    "reduced_motion":    ("environment", "reduced_motion", True),
    "inside_form":       ("environment", "inside_form", True),
    "disabled":          ("props", "disabled", True),
}
ZONE_PRESENT = re.compile(r"^(\w+)_present$")

lint: list[str] = []

def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        lint.append("no frontmatter block")
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        fm[k.strip()] = v
    return fm, text[m.end():]

def parse_tables(text):
    """Every markdown table in the document, as (headers, [row dicts])."""
    tables, rows, headers = [], [], None
    for line in text.splitlines():
        if line.strip().startswith("|"):
            # split on UNESCAPED pipes only. `\|` is legitimate markdown escaping and
            # appears in any enum type — `primary\|secondary\|ghost` — where the value's
            # own separator collides with the table delimiter.
            cells = [c.strip().replace("\\|", "|")
                     for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
            if headers is None:
                headers = cells
            elif set("".join(cells)) <= set("-: "):
                continue                                   # separator row
            else:
                row = dict(zip(headers, cells))
                # The id is machine metadata. In the .md it sits last, carries an `id-`
                # prefix, and is ghosted with <sub> so the eye skips it. None of that
                # decoration travels downstream: canonical documents, test names and
                # reports use the bare id, where the extra characters are pure noise.
                if "id" in row:
                    # two passes: the prefix is only at the start once the tags are gone
                    bare = re.sub(r"</?sub>|`", "", row["id"]).strip()
                    row["id"] = re.sub(r"^id-", "", bare)
                rows.append(row)
        elif headers is not None:
            tables.append((headers, rows)); rows, headers = [], None
    if headers is not None:
        tables.append((headers, rows))
    return tables

def requirement_rows(text):
    """Rows from any table shaped like a requirement table."""
    out = []
    for headers, rows in parse_tables(text):
        if {"id", "statement", "observe", "kind"} <= set(headers):
            for r in rows:
                r.setdefault("when", r.get("required", "always"))
            out += rows
    return out

def scenario_for(required, rid):
    """A condition token becomes a scenario PREDICATE, never an instance."""
    if required in ("always", ""):
        return {}
    if not required.startswith("when:"):
        lint.append(f"{rid}: `required` is not `always` or `when:<condition>` — got {required!r}")
        return {}
    scen: dict = {}
    for cond in required[len("when:"):].split(","):
        cond = cond.strip()
        if cond in CONDITIONS:
            bucket, key, val = CONDITIONS[cond]
            scen.setdefault(bucket, {})[key] = val
        elif (m := ZONE_PRESENT.match(cond)):
            scen.setdefault("zones", {})[m.group(1)] = "present"
        else:
            lint.append(f"{rid}: unknown condition {cond!r} — not in the closed vocabulary")
    return scen

def check_cardinality(rows):
    for r in rows:
        c = r.get("cardinality", "")
        if any(d in c for d in ("–", "—", "-")):
            lint.append(f"{r.get('id')}: cardinality {c!r} uses a dash — the grammar is `0..1`")
        elif c and not re.fullmatch(r"\d+(\.\.\d+|\+)?", c):
            lint.append(f"{r.get('id')}: cardinality {c!r} does not parse")

def main():
    # ---- load --------------------------------------------------------------------
    contract_text = (SRC / "Button.md").read_text()
    fm, body = parse_frontmatter(contract_text)
    arch_text = (LIB / "archetypes/button.md").read_text()
    _, arch_body = parse_frontmatter(arch_text)
    policy_text = (SRC / "system/policy.md").read_text()
    # Three binding sources, one per ownership layer. Later layers override earlier ones.
    bindings: dict = {}
    for src in (LIB / "archetypes/button.bindings.json",      # shipped with the skill
                SRC / "system/policy.bindings.json",          # the design system's
                SRC / "Button.bindings.json"):                # this contract's own
        for rid, entry in json.loads(src.read_text())["bindings"].items():
            bindings.setdefault(rid, {}).update(entry)

    inherited = requirement_rows(arch_body) + requirement_rows(policy_text)
    local = requirement_rows(body)

    for headers, rows in parse_tables(body):
        if "cardinality" in headers:
            check_cardinality(rows)

    seen = {}
    for r in inherited + local:
        if r["id"] in seen:
            lint.append(f"duplicate requirement id {r['id']}")
        seen[r["id"]] = r

    # ---- emit --------------------------------------------------------------------
    OUT.mkdir(exist_ok=True)
    for platform in fm.get("platforms", []):
        reqs = []
        for r in inherited + local:
            rid = r["id"]
            b = bindings.get(rid, {}).get(platform)
            base = {"id": rid, "statement": r["statement"]}
            if b is None:
                lint.append(f"{rid}: no binding for {platform} — cannot be checked or excused")
                reqs.append({**base, "binds": False, "reason": "NO BINDING - lint failure"})
                continue
            if b.get("binds") is False:
                reqs.append({**base, "binds": False, "reason": b["reason"]})
                continue
            needs = b.get("needs") or NEEDS_BY_OBSERVE.get(r["observe"])
            if needs is not None:
                needs = needs + [n for n in b.get("needs_also", []) if n not in needs]
            if needs is None:
                lint.append(f"{rid}: observe {r['observe']!r} is not in the closed vocabulary")
                needs = []
            entry = {**base, "observe": r["observe"], "kind": r["kind"],
                     "scenario": scenario_for(r.get("when") or r.get("required") or "always", rid),
                     "expect": b["expect"], "needs": needs}
            for k in ("trigger", "unit", "also"):
                if k in b:
                    entry[k] = b[k]
            reqs.append(entry)

        doc = {"format_version": "1.0", "contract": fm["component"],
               "contract_version": fm["version"], "platform": platform,
               "archetype": fm["archetype"], "requirements": reqs}
        (OUT / f"Button.{platform}.canonical.json").write_text(json.dumps(doc, indent=2) + "\n")
        binds = sum(1 for r in reqs if r.get("binds") is not False)
        print(f"  {platform:<8} {len(reqs)} requirements, {binds} binding, {len(reqs)-binds} n/a")

    print(f"\nlint: {len(lint)} finding(s)")
    for l in lint:
        print("  -", l)
    sys.exit(1 if lint else 0)


if __name__ == "__main__":
    main()
