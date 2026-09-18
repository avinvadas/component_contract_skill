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

def _policy(fm, src, context, root):
    """(policy text, policy bindings path). ONE policy per design system: `contracts.policy`
    in the context is its location, and a contract's `policy:` overrides it for itself."""
    policy_ref, policy_base = fm.get("policy"), src
    if not policy_ref and (context.get("contracts") or {}).get("policy") and root:
        policy_ref, policy_base = context["contracts"]["policy"], root
    if not policy_ref:
        return "", None
    path = (policy_base / policy_ref).resolve()
    if not path.is_file():
        lint.append("policy %r not found at %s" % (policy_ref, path))
        return "", None
    return path.read_text(), path.with_name(path.stem + ".bindings.json")


def _tree(fm, src, context, root):
    facts = context.get("tokens") or {}
    if fm.get("tokens"):
        return Tree(str((src / fm["tokens"]).resolve()), facts)
    if facts.get("source") and root:
        return Tree(str((root / facts["source"]).resolve()), facts)
    return None


def _bindings(arch_dir, archetype, policy_bindings, own):
    """(merged bindings, the layers themselves). Later layers override earlier ones."""
    files = [] if arch_dir is None else [arch_dir / (archetype + ".bindings.json")]
    files += [policy_bindings, own]
    layers = [json.loads(f.read_text()) for f in files if f and f.is_file()]
    merged: dict = {}
    for layer in layers:
        for rid, entry in layer.get("bindings", {}).items():
            merged.setdefault(rid, {}).update(entry)
    return merged, layers



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
    # `none` is a real answer, not a missing one: a Card conveys no distinct role to assistive
    # technology, so there is nothing to inherit and every requirement is stated locally. It is
    # spelled out rather than left blank so a reader can tell a decision from an omission.
    archetype = fm["role-archetype"]
    arch_dir, arch_fm, arch_text, arch_body = None, {"version": "—"}, "", ""
    if archetype != "none":
        search = []
        local = (context.get("contracts") or {}).get("archetypes")
        if local and root:
            search.append(root / local)
        search.append(LIB / "role-archetypes")
        arch_dir = next((d for d in search if (d / (archetype + ".md")).is_file()), None)
        if arch_dir is None:
            raise SystemExit("role-archetype %r not found in: %s — if this component conveys no "
                             "distinct role, say `role-archetype: none`"
                             % (archetype, ", ".join(map(str, search))))
        arch_text = (arch_dir / (archetype + ".md")).read_text()
        arch_fm, arch_body = parse_frontmatter(arch_text)

    policy_text, policy_bindings = _policy(fm, src, context, root)
    bindings, binding_layers = _bindings(arch_dir, archetype, policy_bindings,
                                         src / (component + ".bindings.json"))
    tree = _tree(fm, src, context, root)
    if tree is not None:
        # A wrong FACT is worse than a missing one: it mis-resolves every component quietly.
        lint.extend("design-system context: " + x for x in tree.problems)

    return {"fm": fm, "body": body, "component": component, "src": src,
            "archetype": archetype, "arch_fm": arch_fm, "arch_text": arch_text,
            "arch_body": arch_body, "policy_text": policy_text, "bindings": bindings,
            "binding_layers": binding_layers, "tree": tree, "context_path": context_path}


# ---- policy rows: decided, undecided, deferred ---------------------------------------
# A policy row with no statement is UNDECIDED — not a requirement. It binds nothing and fails
# nothing. Before this existed, a freshly scaffolded policy made every contract fail with a
# missing-binding finding per blank row per platform: Phase 0C would create the file and the
# very next resolve would break. A row is asked the first time a component ENGAGES it.
TOUCH = {"ios", "android"}

def policy_status(row):
    st = (row.get("statement") or "").strip()
    if not st or (st.startswith("*(") and st.endswith(")*")):
        return "undecided"
    if st.lower().startswith("deferred"):
        return "deferred"
    return "decided"

def engages(trigger, facts):
    """Does this component engage a policy row? `facts` is what the component actually has."""
    trigger = (trigger or "").strip()
    if trigger in ("", "any"):
        return True
    kind, _, arg = trigger.partition(":")
    if kind == "observe":
        return arg in facts["observes"]
    if kind == "platform":
        return arg == "touch" and bool(facts["platforms"] & TOUCH)
    if kind == "token":
        return arg in facts["slot_properties"]
    if kind == "state":
        return arg in facts["states"]
    lint.append("policy: unknown `engaged-by` value %r — expected any, observe:<type>, "
                "platform:touch, token:<property> or state:<name>" % trigger)
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("contract", help="path to <Component>.md")
    ap.add_argument("--out", help="directory for canonical documents (default: beside the contract)")
    ap.add_argument("--context", help="design-system context file (default: nearest .claude/)")
    ap.add_argument("--report", help="also write a JSON report — lint, token gaps, the policy "
                                     "rows this component engages, closure — for the skill to act on")
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

    policy_rows = requirement_rows(policy_text)
    decided_policy = [r for r in policy_rows if policy_status(r) == "decided"]
    inherited = requirement_rows(arch_body) + decided_policy
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

    # ---- which undecided policy rows this component engages ----------------------
    engagement_facts = {
        "platforms": set(fm.get("platforms", [])),
        "observes": {r.get("observe") for r in inherited + local}
                    | ({"token"} if slots else set())
                    | ({"state"} if machine["transitions"] else set()),
        "slot_properties": {sl["property"] for sl in slots},
        "states": {r["prop"].strip("`") for h, rows in parse_tables(body)
                   if {"prop", "type"} <= set(h) for r in rows}
                  | set(machine["states"]),
    }
    policy_to_ask, policy_deferred = [], []
    for r in policy_rows:
        status = policy_status(r)
        if status == "decided" or not engages(r.get("engaged-by"), engagement_facts):
            continue
        entry = {"id": r["id"], "decision": r.get("decision", ""),
                 "engaged-by": r.get("engaged-by") or "any"}
        (policy_to_ask if status == "undecided" else policy_deferred).append(entry)

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

    # A decision nobody has made yet — not lint (the document is fine) and not a token gap
    # (the tree is fine). It is asked now, once, and every later component inherits it.
    if policy_to_ask:
        print(f"\npolicy: {len(policy_to_ask)} undecided row(s) this component engages — ask them now:")
        for e in policy_to_ask:
            print("  - %-7s %-24s engaged by %s" % (e["id"], e["decision"], e["engaged-by"]))
    if policy_deferred:
        print(f"\npolicy: {len(policy_deferred)} deferred row(s) this component engages — not re-asked:")
        for e in policy_deferred:
            print("  - %-7s %s" % (e["id"], e["decision"]))

    lint[:] = list(dict.fromkeys(lint))   # one finding per fact, not one per platform pass
    print(f"\nlint: {len(lint)} finding(s)")
    for l in lint:
        print("  -", l)
    if args.report:
        pathlib.Path(args.report).write_text(json.dumps({
            "component": COMPONENT,
            "lint": lint,
            "token_gaps": [{"id": g["id"], "property": g["property"], "state": g["state"],
                            "status": g["status"], "detail": g["detail"]} for g in gaps],
            "policy_to_ask": policy_to_ask,
            "policy_deferred": policy_deferred,
            "closure": [c["id"] for c in machine["closure"]],
        }, indent=2, default=list) + "\n")
    sys.exit(1 if lint else 0)


if __name__ == "__main__":
    main()
