#!/usr/bin/env python3
"""Contract.md + role-archetype + policy + token tree  ->  one canonical document per platform.

    python3 scripts/resolve.py path/to/Button.md [--out DIR] [--context PATH]

Everything the contract draws from is named, never assumed:

    role-archetype   frontmatter `role-archetype:`; looked up in the design system's own
                     archetype directory first (context `contracts.archetypes`), then in the
                     library shipped with this skill (`system/role-archetypes/`)
    bindings         `<Component>.bindings.json`, beside the contract
    policy           frontmatter `policy:`, relative to the contract; its bindings beside it
    token tree       frontmatter `tokens:`, relative to the contract — or, if absent, context
                     `tokens.source`, relative to the directory holding `.claude/`
    context          `.claude/design-system-context.yml`, found by walking up from the
                     contract, or `--context`

Output defaults to the contract's own directory — the component directory the skill writes.
"""
import argparse, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from tokens import Tree, PROPERTIES  # noqa: E402
import machine as sm  # noqa: E402
import context as ctx  # noqa: E402

# The skill's own shipped layer, located relative to this file so it works wherever the
# skill is installed. Never relative to the working directory.
SKILL = pathlib.Path(__file__).resolve().parent.parent
LIB = SKILL / "system"

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
# LOADED, not restated. Two copies drifted in both directions: `expanded`, `rtl` and
# `pointer_input` were in the vocabulary and unknown to this resolver, which would have
# lint-failed a contract that used them correctly; `hover` and `focused` were the reverse.
CONDITIONS = json.loads((LIB / "vocabulary/conditions.json").read_text())["conditions"]
ZONE_PRESENT = re.compile(r"^(\w+)_present$")
# `following:<transition>` — an effect of a transition, generated per declared transition id.
# Not `after:`, which the spec already uses for a zone's position; one token, one meaning.
FOLLOWING = re.compile(r"^following:([A-Za-z0-9][\w-]*)$")
TRANSITION_IDS: set = set()

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
            for bucket, kv in CONDITIONS[cond]["scenario"].items():
                scen.setdefault(bucket, {}).update(kv)
        elif (m := ZONE_PRESENT.match(cond)):
            scen.setdefault("zones", {})[m.group(1)] = "present"
        elif (m := FOLLOWING.match(cond)):
            if m.group(1) not in TRANSITION_IDS:
                lint.append(f"{rid}: `following:{m.group(1)}` names no declared transition")
            scen.setdefault("machine", {})["following"] = m.group(1)
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

# ---- token slots -------------------------------------------------------------
# A slot table declares which properties are tokenised. It is NOT a requirement table —
# it carries no statement and no observe — so it has to be recognised on its own terms.
# Before this existed the table matched nothing and was dropped in silence, which is the
# one outcome the design exists to prevent: a contract that states a fact, and a resolver
# that reports clean without checking it.
SLOT_HEADERS = {"property", "token", "id"}
gaps: list[dict] = []

def slot_rows(text):
    for headers, rows in parse_tables(text):
        if SLOT_HEADERS <= set(headers) and "statement" not in headers:
            return rows
    return []

def default_dims(text):
    """A variant prop's DEFAULT supplies the dimension a slot resolves against."""
    dims = {}
    for headers, rows in parse_tables(text):
        if {"prop", "type", "default"} <= set(headers):
            for r in rows:
                name = r["prop"].strip("`")
                if r["type"].startswith("enum:") and name in ("variant", "size", "tone", "emphasis"):
                    dims[name] = r["default"].strip("`")
    return dims

def state_of(when):
    if when.startswith("when:"):
        first = when[len("when:"):].split(",")[0].strip()
        if first in ("hover", "disabled", "focused", "pressed", "selected"):
            return "focus" if first == "focused" else first
    return None

def kebab(name):
    """`IconButton` -> `icon-button`: how a component's name appears as a token scope."""
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"-\1", name).lower()

def resolve_slots(body, fm, tree):
    """Each declared property -> a bound token, or a NAMED reason it is not bound."""
    rows = slot_rows(body)
    if not rows:
        return []
    if tree is None:
        lint.append("%d token slot(s) declared but no token tree — set `tokens:` in the "
                    "frontmatter or `tokens.source` in the design-system context" % len(rows))
        return []
    scope, dims = kebab(fm["component"]), default_dims(body)
    out = []
    for r in rows:
        when = r.get("when", "always")
        cell = r["token"].strip().strip("`")
        slot = {"id": r["id"], "when": when, "property": r["property"],
                "state": state_of(when), "dims": dims}
        if cell.lower().startswith("n/a"):
            reason = cell[3:].lstrip(" —-:").strip() or "declared not applicable"
            slot.update(token=None, status="not-applicable", detail=reason)
        elif cell in ("—", "-", ""):
            tok, status, detail = tree.resolve(slot["property"], scope,
                                               dims=dims, state=slot["state"])
            slot.update(token=tok, status=status, detail=detail)
        elif cell in tree.tokens:
            slot.update(token=cell, status="bound", detail="pinned")
        else:
            # A pinned name absent from the tree is the one failure that must never be
            # quietly accepted: it is how an invented token name enters a design system.
            slot.update(token=None, status="absent-from-tree", detail=cell)
            lint.append("%s: pinned token %r is not in the token tree" % (r["id"], cell))
        if slot["status"] not in ("bound", "not-applicable"):
            gaps.append(slot)
        out.append(slot)
    return out

def slot_requirement(slot):
    """A slot becomes a real requirement, bound or explicitly pending — never absent."""
    label = slot["property"] + ("@" + slot["state"] if slot["state"] else "")
    base = {"id": slot["id"], "observe": "token", "kind": "state",
            "scenario": scenario_for(slot["when"], slot["id"]), "needs": ["source"]}
    if slot["status"] == "not-applicable":
        return {"id": slot["id"],
                "statement": "%s is not tokenised." % label,
                "binds": False, "reason": slot["detail"]}
    if slot["status"] == "bound":
        return dict(base, statement="%s resolves through `%s`." % (label, slot["token"]),
                    expect={"equals": slot["token"]})
    # No `expect`. A verifier with nothing to compare against reports `unverified`, which
    # is the whole point — an unresolved token must never be able to produce a pass.
    return dict(base, statement="%s resolves through a design token." % label,
                pending={"reason": slot["status"], "detail": slot["detail"]})

def load_sources(contract_path, context_path=None):
    """Everything a contract draws from, located from the contract itself. Shared with the view."""
    contract_path = pathlib.Path(contract_path).resolve()
    src = contract_path.parent
    fm, body = parse_frontmatter(contract_path.read_text())
    component = fm.get("component") or contract_path.stem

    context_path = pathlib.Path(context_path).resolve() if context_path else ctx.find(src)
    context = ctx.load(context_path) if context_path else {}
    root = ctx.repo_root(context_path) if context_path else None

    # role-archetype: the design system's own extensions first, then the shipped library.
    archetype = fm["role-archetype"]
    search = []
    local = (context.get("contracts") or {}).get("archetypes")
    if local and root:
        search.append(root / local)
    search.append(LIB / "role-archetypes")
    arch_dir = next((d for d in search if (d / (archetype + ".md")).is_file()), None)
    if arch_dir is None:
        raise SystemExit("role-archetype %r not found in: %s" % (archetype, ", ".join(map(str, search))))
    arch_text = (arch_dir / (archetype + ".md")).read_text()
    arch_fm, arch_body = parse_frontmatter(arch_text)

    # policy: named by the contract. Once hardcoded to `system/policy.md`, like the archetype.
    policy_text, policy_bindings = "", None
    if fm.get("policy"):
        policy_path = (src / fm["policy"]).resolve()
        if policy_path.is_file():
            policy_text = policy_path.read_text()
            policy_bindings = policy_path.with_name(policy_path.stem + ".bindings.json")
        else:
            lint.append("policy %r not found at %s" % (fm["policy"], policy_path))

    # Three binding layers, one per ownership layer. Later layers override earlier ones.
    layer_files = [arch_dir / (archetype + ".bindings.json"), policy_bindings,
                   src / (component + ".bindings.json")]
    binding_layers = [json.loads(f.read_text()) for f in layer_files if f and f.is_file()]
    bindings: dict = {}
    for layer in binding_layers:
        for rid, entry in layer.get("bindings", {}).items():
            bindings.setdefault(rid, {}).update(entry)

    # token tree: the contract's own reference wins; otherwise the design system's.
    tree, facts = None, (context.get("tokens") or {})
    if fm.get("tokens"):
        tree = Tree(str((src / fm["tokens"]).resolve()), facts)
    elif facts.get("source") and root:
        tree = Tree(str((root / facts["source"]).resolve()), facts)

    if tree is not None:
        # A wrong FACT is worse than a missing one: it mis-resolves every component quietly.
        lint.extend("design-system context: " + x for x in tree.problems)

    return {"fm": fm, "body": body, "component": component, "src": src,
            "archetype": archetype, "arch_fm": arch_fm, "arch_text": arch_text, "arch_body": arch_body, "policy_text": policy_text,
            "bindings": bindings, "binding_layers": binding_layers, "tree": tree,
            "context_path": context_path}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("contract", help="path to <Component>.md")
    ap.add_argument("--out", help="directory for canonical documents (default: beside the contract)")
    ap.add_argument("--context", help="design-system context file (default: nearest .claude/)")
    args = ap.parse_args()

    S = load_sources(args.contract, args.context)
    fm, body, arch_body = S["fm"], S["body"], S["arch_body"]
    policy_text, bindings, COMPONENT = S["policy_text"], S["bindings"], S["component"]
    OUT = pathlib.Path(args.out).resolve() if args.out else S["src"]

    # The machine is resolved BEFORE any requirement, because `when:following:<transition>`
    # conditions are checked against its transition ids. Closure is computed on the merged
    # machine — archetype rows plus contract rows — never per file.
    zones = {r["zone"] for h, rows in parse_tables(body) if "zone" in h for r in rows}
    machine, mlint = sm.build(sm.machine_rows(parse_tables(arch_body)) +
                              sm.machine_rows(parse_tables(body)), zones)
    lint.extend(mlint)
    TRANSITION_IDS.update(t["id"] for t in machine["transitions"])
    machine_bindings = sm.merge_bindings(S["binding_layers"])

    inherited = requirement_rows(arch_body) + requirement_rows(policy_text)
    local = requirement_rows(body)
    slots = resolve_slots(body, fm, S["tree"])

    for headers, rows in parse_tables(body):
        if "cardinality" in headers:
            check_cardinality(rows)

    seen = {}
    for r in inherited + local:
        if r["id"] in seen:
            lint.append(f"duplicate requirement id {r['id']}")
        seen[r["id"]] = r

    # ---- emit --------------------------------------------------------------------
    OUT.mkdir(parents=True, exist_ok=True)
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
            if "pending" in b:
                # The requirement applies, but nothing can yet be named to check it against —
                # a vocabulary gap, say. `pending` and no `expect`: a verifier has nothing to
                # compare, so it reports unverified. Same mechanism as an unresolved token.
                reqs.append({**base, "observe": r["observe"], "kind": r["kind"],
                             "scenario": scenario_for(r.get("when") or "always", rid),
                             "needs": NEEDS_BY_OBSERVE.get(r["observe"], []),
                             "pending": b["pending"]})
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

        for slot in slots:
            reqs.append(slot_requirement(slot))

        doc = {"format_version": "1.0", "contract": fm["component"],
               "contract_version": fm["version"], "platform": platform,
               "role-archetype": fm["role-archetype"], "requirements": reqs}
        if machine["transitions"]:
            mreqs, block = sm.requirements(machine, machine_bindings, platform, lint)
            reqs.extend(mreqs)
            doc["machine"] = block
        (OUT / (COMPONENT + f".{platform}.canonical.json")).write_text(json.dumps(doc, indent=2) + "\n")
        binds = sum(1 for r in reqs if r.get("binds") is not False)
        print(f"  {platform:<8} {len(reqs)} requirements, {binds} binding, {len(reqs)-binds} n/a")

    # Gaps and lint are different animals. A lint finding means the DOCUMENT is malformed.
    # A gap means the document is fine and the TOKEN TREE cannot express something yet —
    # a task for whoever owns the tree, not a reason to fail the parse.
    print(f"\ntoken slots: {len(slots)} declared, "
          f"{sum(1 for s_ in slots if s_['status'] == 'bound')} bound, "
          f"{sum(1 for s_ in slots if s_['status'] == 'not-applicable')} n/a, "
          f"{len(gaps)} gap(s)")
    for g in gaps:
        label = g["property"] + ("@" + g["state"] if g["state"] else "")
        print("  - %-8s %-17s %s" % (g["id"], g["status"], label))

    if machine["transitions"]:
        grid = len(machine["states"]) * len(machine["events"])
        print(f"\nmachine: {len(machine['states'])} states x {len(machine['events'])} events = {grid} cells — "
              f"{len(machine['transitions'])} authored, {len(machine['unreachable'])} unreachable, "
              f"{len(machine['closure'])} closure (generated)")
        for c in machine["closure"]:
            print("  - %s" % c["id"])

    lint[:] = list(dict.fromkeys(lint))   # one finding per fact, not one per platform pass
    print(f"\nlint: {len(lint)} finding(s)")
    for l in lint:
        print("  -", l)
    sys.exit(1 if lint else 0)


if __name__ == "__main__":
    main()
