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
    "element":      ["identity"],
    "name":         ["a11y-tree"],
    "state":        ["a11y-tree"],
    "containment":  ["a11y-tree"],
    "order":        ["a11y-tree"],
    "focus":        ["focus"],
    "layout":       ["geometry"],
    "event":        ["interaction"],
    "announcement": ["announcement"],
    "token":        ["applied-styles"],
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
# `<prop>=<value>` — one value of a visual axis, `kind=secondary`. Checked against the enum props
# the contract declares, so a misspelt variant is a finding, not a scenario no witness matches.
PROP_VALUE = re.compile(r"^([A-Za-z][\w-]*)=([\w-]+)$")
ENUM_PROPS: dict = {}
# The interaction states a component can be in. An archetype names the valid ones; chapter 4.2
# must answer each. Also where a state's spellings in token trees live: `pressed` is `active`
# in Carbon, and a resolver that only looked for `pressed` would call the token absent.
STATES = json.loads((LIB / "vocabulary/interaction-states.json").read_text())["states"]

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

# A markdown table's first row is its header. A row that carries an id or a backticked value is
# DATA, so a table starting with one has lost its header — usually a block appended after a blank
# line, which silently became a table of its own. Nine token slots once vanished that way.
def check_table_headers(text):
    for headers, rows in parse_tables(text):
        if any(re.search(r"`|^id-|^when:", h) for h in headers):
            lint.append("a table starts with a data row (%s…) — it has no header, so nothing reads "
                        "it. A block appended after a blank line becomes a table of its own."
                        % " | ".join(headers[:3])[:60])


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
        elif (m := PROP_VALUE.match(cond)):
            prop, val = m.groups()
            if prop not in ENUM_PROPS:
                lint.append(f"{rid}: `{cond}` names no enum prop — declare `{prop}` in chapter 4.3 or 2.3")
            elif val not in ENUM_PROPS[prop]:
                lint.append(f"{rid}: `{cond}` — {val!r} is not a value of `{prop}` "
                            f"({', '.join(ENUM_PROPS[prop])})")
            scen.setdefault("props", {})[prop] = val
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

AXIS_PROPS = ("variant", "size", "tone", "emphasis")
# Which axes a property varies along. Colour, opacity and elevation vary by emphasis; dimensions
# vary by size. A slot is expanded along its property's axes only — never size x colour.
APPEARANCE_AXES = {"variant", "tone", "emphasis"}

def enum_props(text):
    """{prop: [values]} for every enum prop the contract declares, from any props table."""
    out = {}
    for headers, rows in parse_tables(text):
        if {"prop", "type"} <= set(headers):
            for r in rows:
                if r["type"].startswith("enum:"):
                    out[r["prop"].strip("`")] = [v.strip() for v in r["type"][5:].split(",") if v.strip()]
    return out

def axis_props(text, prop_axes=None):
    """{prop: (axis, default)} for enum props that feed a token axis.

    Which prop feeds which token axis is the design system's naming, not a rule: Carbon calls its
    variant prop `kind`. `tokens.prop_axes` in the context says so — `{kind: variant}` — and a
    prop literally named after an axis needs no declaration."""
    axes = {a: a for a in AXIS_PROPS}
    axes.update(prop_axes or {})
    out = {}
    for headers, rows in parse_tables(text):
        if {"prop", "type", "default"} <= set(headers):
            for r in rows:
                name = r["prop"].strip("`")
                if r["type"].startswith("enum:") and name in axes:
                    out[name] = (axes[name], r["default"].strip("`"))
    return out

def default_dims(text, prop_axes=None):
    """A variant prop's DEFAULT supplies the dimension a slot resolves against."""
    return {axis: default for axis, default in axis_props(text, prop_axes).values()}

def parse_when(when):
    """(interaction state or None, {prop: value}, [other conditions]) of a `when` cell."""
    state, values, other = None, {}, []
    if when.startswith("when:"):
        for c in when[len("when:"):].split(","):
            c = c.strip()
            if (m := PROP_VALUE.match(c)):
                values[m.group(1)] = m.group(2)
            elif state is None and (c in STATES or c == "focused"):
                state = c
            elif c:
                other.append(c)
    return state, values, other

def state_of(when):
    return parse_when(when)[0]

def tree_spellings(state):
    if state is None:
        return [None]
    if state == "focused":
        return ["focus"]
    return STATES.get(state, {}).get("tree_spellings") or [state]

def kebab(name):
    """`IconButton` -> `icon-button`: how a component's name appears as a token scope."""
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"-\1", name).lower()

def _resolve_one(tree, prop, scope, dims, state):
    """Try each spelling a token tree may use for the state; the first that binds wins."""
    results = [tree.resolve(prop, scope, dims=dims, state=sp) for sp in tree_spellings(state)]
    for res in results:
        if res[1] == "bound":
            return res
    return next((r for r in results if r[1] != "absent-from-tree"), results[0])

def expand_slots(rows, axes):
    """Each authored slot row, expanded to one case per value of its property's visual axes.

    A slot row without a `<prop>=<value>` condition applies to EVERY value of the axis — that is
    what lets a contract say `when:hover | background | —` once instead of seven times. The
    resolver does the multiplying, so every variant x state x property is addressed in the
    canonical document, and a more specific row (`when:hover,kind=ghost`) overrides the general
    one for its own value only. A value no row covers is a finding: the case was never answered.
    """
    out, groups = [], {}
    for r in rows:
        state, values, _ = parse_when(r.get("when", "always"))
        groups.setdefault((r["property"], state), []).append((r, values))
    for (prop, state), members in groups.items():
        kind = PROPERTIES.get(prop, {}).get("type")
        relevant = [p for p, (axis, _) in axes.items()
                    if (axis == "size") == (kind == "dimension")]
        combos = [{}]
        for p in relevant:
            combos = [dict(c, **{p: v}) for c in combos for v in ENUM_PROPS.get(p, [])]
        uncovered = []
        for combo in combos:
            fits = [(r, v) for r, v in members if all(combo.get(k) == x for k, x in v.items())]
            if not fits:
                uncovered.append(",".join("%s=%s" % kv for kv in combo.items()))
                continue
            r, v = max(fits, key=lambda rv: len(rv[1]))
            if r["token"].strip().strip("`").lower().startswith("n/a"):
                # "not tokenised" is true of every value at once; one case says it
                if not any(o is r for o, _, _ in out):
                    out.append((r, v, {}))
                continue
            extra = {k: x for k, x in combo.items() if k not in v}
            out.append((r, combo, extra))
        if uncovered:
            ids = ", ".join(r["id"] for r, _ in members)
            lint.append("%s: %s%s is not addressed for %s — add a row without a value condition, "
                        "or one per value (`n/a — reason` counts as an answer)"
                        % (ids, prop, "@" + state if state else "", "; ".join(uncovered)))
    return out

def specificity_counts(slots):
    """{component: n, shared:<g>: n, semantic: n} over the bound cases the contract WROTE —
    rest-token aliases repeat a rest case and would inflate every count."""
    out = {}
    for s_ in slots:
        if s_["status"] == "bound" and not s_.get("alias_of"):
            out[s_["scope"]] = out.get(s_["scope"], 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (kv[0] != "component", kv[0] != "semantic", kv[0])))

def valid_states(fm, arch_fm):
    """The archetype's interaction states, plus any the contract's frontmatter adds."""
    return list(dict.fromkeys(list((arch_fm or {}).get("interaction-states") or [])
                              + list(fm.get("interaction-states") or [])))

def resolve_slots(body, fm, tree, arch_fm=None):
    """Each declared property, per state and per variant -> a bound token, or a NAMED reason."""
    rows = slot_rows(body)
    if not rows:
        return []
    if tree is None:
        lint.append("%d token slot(s) declared but no token tree — set `tokens:` in the "
                    "frontmatter or `tokens.source` in the design-system context" % len(rows))
        return []
    ENUM_PROPS.update(enum_props(body))
    facts = tree.facts or {}
    axes = axis_props(body, facts.get("prop_axes"))
    scope, defaults = kebab(fm["component"]), default_dims(body, facts.get("prop_axes"))
    for r in rows:
        # Every authored condition is checked, including on a row that expands to no case —
        # `kind=tertiary` where kind has no tertiary would otherwise vanish without a word.
        scenario_for(r.get("when", "always"), r["id"])
    defaults_by_prop = {p: d for p, (_, d) in axes.items()}
    out = []
    for r, combo, extra in expand_slots(rows, axes):
        when = r.get("when", "always")
        if extra:
            conds = [] if when in ("always", "") else [when[len("when:"):]]
            when = "when:" + ",".join(conds + ["%s=%s" % kv for kv in extra.items()])
        rid = r["id"] + ("[%s]" % ",".join("%s=%s" % kv for kv in extra.items()) if extra else "")
        dims = dict(defaults, **{axes[p][0]: v for p, v in combo.items()})
        cell = r["token"].strip().strip("`")
        slot = {"id": rid, "base_id": r["id"], "when": when, "property": r["property"],
                "state": state_of(when), "variant": combo, "dims": dims,
                "transform": parse_transform(r.get("transform"), r["id"])}
        pattern = None
        if TOKEN_PLACEHOLDER.search(cell):
            pattern, cell = cell, fill_pattern(cell, combo, r["id"], defaults_by_prop)
        if cell.lower().startswith("n/a"):
            reason = cell[3:].lstrip(" —-:").strip() or "declared not applicable"
            slot.update(token=None, status="not-applicable", detail=reason)
        elif cell in ("—", "-", ""):
            tok, status, detail = _resolve_one(tree, slot["property"], scope, dims, slot["state"])
            slot.update(token=tok, status=status, detail=detail)
        elif cell in tree.tokens:
            slot.update(token=cell, status="bound", detail="pinned")
        elif pattern:
            slot.update(token=None, status="absent-from-tree", detail=cell)
            lint.append("%s: pattern %r gives %r for %s, which is not in the token tree — add an "
                        "override row for that value" % (r["id"], pattern, cell,
                        ", ".join("%s=%s" % kv for kv in combo.items()) or "the default"))
        else:
            # A pinned name absent from the tree is the one failure that must never be
            # quietly accepted: it is how an invented token name enters a design system.
            slot.update(token=None, status="absent-from-tree", detail=cell)
            lint.append("%s: pinned token %r is not in the token tree" % (r["id"], cell))
        slot["scope"] = tree.specificity(slot["token"], scope) if slot["token"] else None
        slot["row_scope"] = (r.get("scope") or "").strip().strip("`")
        if slot["status"] != "bound" and cell in ("—", "-", ""):
            note_shared_candidate(tree, slot, scope)
        if slot["status"] not in ("bound", "not-applicable"):
            gaps.append(slot)
        out.append(slot)
    check_row_scopes(out)
    return out + alias_states(out, valid_states(fm, arch_fm), tree, scope)

# ---- specificity: how specific each token is to this component ----------------------------
# Component tokens are not always 1:1 with a component: `control.border-radius` serves a button
# and a segmented-control tab alike. So every slot row states its `scope` — `component`,
# `shared:<group>` or `semantic` — computed from the tree, never typed, and checked here.
TOKEN_PLACEHOLDER = re.compile(r"\{([A-Za-z][\w-]*)\}")
shared_notes: list[dict] = []

def fill_pattern(cell, combo, rid, defaults):
    """`component.button.{kind}-hover` with kind=secondary -> `component.button.secondary-hover`."""
    def sub(m):
        prop = m.group(1)
        if prop in combo:
            return combo[prop]
        if prop in defaults:
            return defaults[prop]
        lint.append("%s: `{%s}` in a token pattern names no visual-variant prop" % (rid, prop))
        return m.group(0)
    return TOKEN_PLACEHOLDER.sub(sub, cell)

def check_row_scopes(cases):
    """A row's `scope` cell must say what the tree says of every token the row binds."""
    by_row = {}
    for c in cases:
        if c["status"] == "bound":
            by_row.setdefault(c["base_id"], (c["row_scope"], set()))[1].add(c["scope"])
    for rid, (written, found) in by_row.items():
        if len(found) > 1:
            lint.append("%s: binds tokens of different scope (%s) — one row, one scope; split it "
                        "with an override row per value" % (rid, ", ".join(sorted(found))))
        elif written and written not in ("—", "-") and written not in found:
            lint.append("%s: scope says %r, the tree says %r — run scripts/writeback.py"
                        % (rid, written, next(iter(found))))

def note_shared_candidate(tree, slot, scope):
    """A shared group has a token for this case, and this component is not declared a member.
    Membership is rarely in the tree, so it is asked, never assumed."""
    for group, members in tree.shared.items():
        if scope in members or group == scope:
            continue
        for sp in tree_spellings(slot["state"]):
            cands = tree.candidates(slot["property"], sp, "component", group)
            cands = [c for c in cands if all(tree.dims_of(c).get(k) == v
                                             for k, v in slot["dims"].items() if k in tree.dims_of(c))]
            if len(cands) == 1:
                shared_notes.append({"id": slot["id"], "group": group, "token": cands[0],
                                     "members": members})
                return

# A state in which a property does not change is not "nothing": the property keeps its REST
# token, and saying so is a claim a verifier can check — force the state, and the rest token
# must still be the one applied. `nothing` meant different things in different places (policy
# draws it, the platform draws it, it genuinely stays put); an alias means exactly one.
state_notes: list[dict] = []

def alias_states(cases, states, tree, scope):
    """Every valid state x tokenised property x variant the contract did not write, as an alias
    of that property's rest case. A rest case pending in the tree stays pending here, and the
    gap is reported once, on the rest case, where it is fixed."""
    out = []
    have = {(c["property"], c["state"], tuple(sorted(c["variant"].items()))) for c in cases}
    have_any = {(c["property"], c["state"]) for c in cases}
    for rest in [c for c in cases if c["state"] is None]:
        vkey = tuple(sorted(rest["variant"].items()))
        for st in states:
            if (rest["property"], st, vkey) in have:
                continue
            if not rest["variant"] and (rest["property"], st) in have_any:
                continue              # a collapsed n/a rest, answered per variant for this state
            when = "when:" + ",".join([st] + ["%s=%s" % kv for kv in rest["variant"].items()])
            alias = dict(rest, id="%s@%s%s" % (rest["base_id"], st,
                                                rest["id"][len(rest["base_id"]):]),
                         when=when, state=st, alias_of=rest["id"])
            if rest["status"] == "bound":
                alias["detail"] = "alias of rest (%s)" % rest["id"]
                # The tree has this component's own token for the state, and the contract says the
                # property does not change. One of them is wrong; the person decides which.
                tok, status, where = _resolve_one(tree, rest["property"], scope, rest["dims"], st)
                if status == "bound" and where == "component" and tok != rest["token"]:
                    state_notes.append({"id": alias["id"], "property": rest["property"],
                                        "state": st, "variant": rest["variant"],
                                        "rest_token": rest["token"], "tree_token": tok})
            out.append(alias)
    return out

# ---- interaction states: every valid one is answered -------------------------------------
STATE_HEADERS = {"state", "what changes"}
DRIVERS = {"prop", "platform", "both"}

def state_rows(text):
    for headers, rows in parse_tables(text):
        if STATE_HEADERS <= set(headers):
            return rows
    return []

def check_states(body, fm, arch_fm, slot_rows_):
    """Chapter 4.2 answers every interaction state valid for this component, and 4.1 agrees.

    Valid = the archetype's `interaction-states`, plus any the contract's frontmatter adds. A
    contract cannot drop one. `what changes` names the properties that take their OWN token in
    that state; `—` says none do. Every other property keeps its rest token — an alias the
    resolver generates and a verifier checks — so no state is ever left unsaid.
    Returns {state: [properties it changes]} for the report and the view."""
    valid = valid_states(fm, arch_fm)
    for st in valid:
        if st not in STATES:
            lint.append("interaction state %r is not in the closed vocabulary (%s)"
                        % (st, ", ".join(STATES)))
    answered = {}
    for r in state_rows(body):
        st = r["state"].strip("`")
        if st not in valid:
            lint.append("§4.2 row %r: not an interaction state of this component (valid: %s) — "
                        "add it to `interaction-states:` in the frontmatter if it is one"
                        % (st, ", ".join(valid) or "none"))
            continue
        cell = r["what changes"].strip()
        if cell in ("—", "-", ""):
            answered[st] = []
        elif cell.lower().startswith("nothing"):
            lint.append("§4.2 %s: `nothing` is not an answer — it means different things in "
                        "different places. Write `—`: every property then keeps its rest token, "
                        "as an alias a verifier checks" % st)
            answered[st] = []
        else:
            props = [x.strip().strip("`") for x in cell.split(",") if x.strip()]
            for p in props:
                if p not in PROPERTIES:
                    lint.append("§4.2 %s: %r is not a property (%s)" % (st, p, ", ".join(PROPERTIES)))
            answered[st] = props
        drv = r.get("driven by", "").strip()
        if drv and drv not in DRIVERS:
            lint.append("§4.2 %s: driven by %r — expected prop, platform or both" % (st, drv))
    for st in valid:
        if st not in answered:
            lint.append("§4.2: interaction state %r is valid for this component and not "
                        "addressed — name what takes its own token, or `—` if every property "
                        "keeps its rest token" % st)

    slotted = {}
    for r in slot_rows_:
        st = state_of(r.get("when", "always"))
        slotted.setdefault(st, set()).add(r["property"])
    for st, props in answered.items():
        for p in props:
            if p not in slotted.get(st, set()):
                lint.append("§4.2 says %s changes %s, and §4.1 has no slot for %s@%s" % (st, p, p, st))
            if p not in slotted.get(None, set()):
                lint.append("§4.2 says %s changes %s, and §4.1 has no rest (`always`) slot for %s"
                            % (st, p, p))
    for st, props in slotted.items():
        if st is None or st not in answered:
            if st is not None and st in valid:
                continue                        # already reported as unaddressed
            if st is not None:
                lint.append("§4.1 tokenises state %r, which is not an interaction state of this "
                            "component" % st)
            continue
        for p in props - set(answered[st]):
            lint.append("§4.1 has a slot for %s@%s, and §4.2 does not list %s as changing in %s"
                        % (p, st, p, st))
    return {"valid": valid, "answered": answered}

# ---- structure: which platform element carries the role ----------------------------------
ELEMENT_HEADERS = {"platform", "element", "id"}
NAME = re.compile(r"`<?([A-Za-z][\w.:-]*)[^`>]*>?`")

def element_names(cell):
    """`<button>` · `<input type=submit>` -> [button, input]; `<h1>`–`<h6>` -> h1..h6."""
    names = [m.group(1) for m in NAME.finditer(cell)]
    rng = re.search(r"`<h([1-6])>`\s*[–-]\s*`<h([1-6])>`", cell)
    if rng:
        names += ["h%d" % i for i in range(int(rng.group(1)), int(rng.group(2)) + 1)]
    return list(dict.fromkeys(names))

def native_backing(arch_body):
    """{platform: [names]} from the archetype's Native backing table."""
    for headers, rows in parse_tables(arch_body):
        if headers[:2] == ["Platform", "Native backing"]:
            return {r["Platform"].lower(): element_names(r["Native backing"]) for r in rows}
    return {}

def element_requirements(body, fm, archetype, arch_body):
    """{platform: requirement} — the semantic element, as chapter 2 states it per platform."""
    rows = []
    for headers, trs in parse_tables(body):
        if ELEMENT_HEADERS <= set(headers) and "statement" not in headers:
            rows = trs
    backing = native_backing(arch_body)
    out = {}
    for r in rows:
        plat, cell = r["platform"].strip().lower(), r["element"]
        names = element_names(cell)
        if not names:
            lint.append("%s: element %r names nothing — write it in backticks, `<button>`" % (r["id"], cell))
            continue
        allowed = backing.get(plat) or []
        custom = cell.lower().lstrip("`").startswith("custom")
        if allowed and not custom and not set(names) <= set(allowed):
            lint.append("%s: %s element %s is not a native backing of `%s` (%s) — if it is "
                        "deliberate, write `custom — <reason>` and the archetype's requirements "
                        "still bind" % (r["id"], plat, ", ".join(names), archetype, ", ".join(allowed)))
        shown = " or ".join("<%s>" % n if plat == "web" else n for n in names)
        out[plat] = {"id": r["id"], "statement": "The element carrying the role is %s." % shown,
                     "observe": "element", "kind": "state", "scenario": {},
                     "expect": {"one_of": names}, "needs": ["identity"]}
    if archetype != "none":
        for plat in fm.get("platforms", []):
            if plat not in out:
                lint.append("§2: no element row for %s — which %s element carries the `%s` role "
                            "is not addressed" % (plat, plat, archetype))
    return out

def platform_name(canonical, conv):
    """A canonical token path as one platform renders it — `tokens.naming_convention.<platform>`:
    `row` (kebab, snake, dot, camel, pascal, flat, screaming-snake), an added `prefix`, and the
    `scope_depth` leading canonical words that platform's pipeline drops. Carbon's web row turns
    `component.button.primary` into `--cds-button-primary`; shadcn's turns `semantic.primary`
    into `--primary`."""
    words = canonical.split(".")[int(conv.get("scope_depth") or 0):]
    parts = [p for w in words for p in re.split(r"[-_]", w) if p]
    row = conv.get("row", "kebab")
    joined = {"kebab": "-".join(parts), "snake": "_".join(parts), "dot": ".".join(parts),
              "flat": "".join(parts), "screaming-snake": "_".join(parts).upper(),
              "camel": parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:]) if parts else "",
              "pascal": "".join(p[:1].upper() + p[1:] for p in parts)}.get(row)
    if joined is None:
        lint.append("naming_convention: unknown row %r" % row)
        joined = "-".join(parts)
    return (conv.get("prefix") or "") + joined

TRANSFORM = re.compile(r"^alpha\s+(\d+(?:\.\d+)?)%$")

def parse_transform(cell, rid):
    """A transform the contract STATES — `alpha 80%` — so a derived token is compared exactly,
    never excused. An unstated transform in the implementation is a mismatch."""
    cell = (cell or "").strip()
    if cell in ("", "—", "-"):
        return None
    m = TRANSFORM.match(cell)
    if not m:
        lint.append("%s: transform %r is not in the grammar (`alpha N%%`)" % (rid, cell))
        return None
    return {"alpha": float(m.group(1))}

INTERACTION = ("hover", "focused", "focus-visible", "pressed")

def slot_scenario(slot, slots):
    """The cases a property's slots cover do not overlap, and the scenario says so.

    A property's slots are cases: `always | background` beside `when:hover | background` and
    `when:disabled | background`. Read literally, `always` also claims the disabled button and
    the hovered one — two claims that cannot both hold for one instance, the same contradiction
    the button archetype once had between BTN-03 and BTN-08. So the unconditioned slot is the
    DEFAULT case and excludes every other slot's condition, and an interaction state applies
    only while the component can be used. Found when a real verifier checked Carbon's disabled
    button against `always | background` and correctly saw the disabled token.
    """
    scen = scenario_for(slot["when"], slot["id"])
    siblings = [o for o in slots if o is not slot and o["property"] == slot["property"]]
    has_disabled = any(o["state"] == "disabled" for o in slots)
    if slot["state"] is None:
        for o in siblings:
            if o["state"] == "disabled":
                scen.setdefault("props", {})["disabled"] = False
            elif o["state"] in INTERACTION:
                scen.setdefault("state", {})[o["state"]] = False
    elif slot["state"] in INTERACTION and has_disabled:
        scen.setdefault("props", {})["disabled"] = False
    return scen

def slot_label(slot):
    """`background@hover [kind=secondary]` — property, state, and the variant it is for."""
    label = slot["property"] + ("@" + slot["state"] if slot["state"] else "")
    if slot.get("variant"):
        label += " [%s]" % ", ".join("%s=%s" % kv for kv in slot["variant"].items())
    return label

def slot_requirement(slot, platform=None, conv=None, slots=()):
    req = _slot_requirement(slot, platform, conv, slots)
    if slot.get("alias_of"):
        req["alias_of"] = slot["alias_of"]
        if slot["status"] == "bound":
            req["statement"] = "%s keeps its rest token `%s`." % (slot_label(slot), slot["token"])
    return req

def _slot_requirement(slot, platform=None, conv=None, slots=()):
    """A slot becomes a real requirement, bound or explicitly pending — never absent."""
    label = slot_label(slot)
    base = {"id": slot["id"], "property": slot["property"], "scope": slot.get("scope"),
            "observe": "token", "kind": "state",
            "scenario": slot_scenario(slot, list(slots) or [slot]), "needs": ["applied-styles"]}
    if slot["status"] == "not-applicable":
        # The scenario travels with an n/a case too: it binds nothing, but a verifier can still
        # OBSERVE what the implementation does there — evidence, for a person to judge.
        return {"id": slot["id"], "property": slot["property"], "observe": "token",
                "scenario": base["scenario"],
                "statement": "%s is not tokenised." % label,
                "binds": False, "reason": slot["detail"]}
    if slot["status"] == "bound":
        req = dict(base, statement="%s resolves through `%s`." % (label, slot["token"]),
                   expect={"equals": slot["token"]})
        if conv:
            req["platform_name"] = platform_name(slot["token"], conv)
        if slot.get("transform"):
            req["transform"] = slot["transform"]
            req["statement"] = "%s resolves through `%s`, at %g%% alpha." % (
                label, slot["token"], slot["transform"]["alpha"])
        return req
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

    ENUM_PROPS.update(enum_props(body))
    policy_rows = requirement_rows(policy_text)
    decided_policy = [r for r in policy_rows if policy_status(r) == "decided"]
    inherited = requirement_rows(arch_body) + decided_policy
    local = requirement_rows(body)
    slots = resolve_slots(body, fm, S["tree"], S["arch_fm"])
    states = check_states(body, fm, S["arch_fm"], slot_rows(body))
    elements = element_requirements(body, fm, S["archetype"], arch_body)

    check_table_headers(body)
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
        # Structure first: what the component IS on this platform, before what it does.
        reqs = [elements[platform]] if platform in elements else []
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

        conventions = ((S["tree"].facts if S["tree"] else {}) or {}).get("naming_convention") or {}
        for slot in slots:
            reqs.append(slot_requirement(slot, platform, conventions.get(platform), slots))

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
    if states["valid"]:
        print("\ninteraction states: " + " · ".join(
            "%s (%s)" % (st, ", ".join(states["answered"][st]) or "rest tokens")
            if st in states["answered"] else "%s (NOT ADDRESSED)" % st for st in states["valid"]))
    n_alias = sum(1 for s_ in slots if s_.get("alias_of"))
    print(f"\ntoken slots: {len(slots)} cases from {len(slot_rows(body))} row(s) "
          f"({n_alias} keep their rest token), "
          f"{sum(1 for s_ in slots if s_['status'] == 'bound')} bound, "
          f"{sum(1 for s_ in slots if s_['status'] == 'not-applicable')} n/a, "
          f"{len(gaps)} gap(s)")
    for g in gaps:
        print("  - %-22s %-17s %s" % (g["id"], g["status"], slot_label(g)))

    if machine["transitions"]:
        grid = len(machine["states"]) * len(machine["events"])
        print(f"\nmachine: {len(machine['states'])} states x {len(machine['events'])} events "
              f"= {grid} cells — "
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

    counts = specificity_counts(slots)
    if counts:
        print("specificity: " + " · ".join("%d %s" % (n, k) for k, n in counts.items()))
    if shared_notes:
        print(f"\nshared groups: {len(shared_notes)} case(s) a shared group could fill, and "
              f"{kebab(fm['component'])} is not declared a member — ask:")
        for n in shared_notes:
            print("  - %-28s `%s` (group %s: %s)"
                  % (n["id"], n["token"], n["group"], ", ".join(n["members"])))

    if state_notes:
        print(f"\nstates: {len(state_notes)} case(s) keep their rest token, while the tree has "
              f"this component's own token for that state — confirm which is intended:")
        for n in state_notes:
            print("  - %-28s rest `%s`, tree has `%s`" % (n["id"], n["rest_token"], n["tree_token"]))

    lint[:] = list(dict.fromkeys(lint))   # one finding per fact, not one per platform pass
    print(f"\nlint: {len(lint)} finding(s)")
    for l in lint:
        print("  -", l)
    if args.report:
        pathlib.Path(args.report).write_text(json.dumps({
            "component": COMPONENT,
            "lint": lint,
            "token_gaps": [{"id": g["id"], "property": g["property"], "state": g["state"],
                            "variant": g.get("variant") or {},
                            "status": g["status"], "detail": g["detail"]} for g in gaps],
            "interaction_states": states,
            "state_token_unused": state_notes,
            "shared_unconfirmed": shared_notes,
            "specificity": specificity_counts(slots),
            "policy_to_ask": policy_to_ask,
            "policy_deferred": policy_deferred,
            "closure": [c["id"] for c in machine["closure"]],
        }, indent=2, default=list) + "\n")
    sys.exit(1 if lint else 0)


if __name__ == "__main__":
    main()
