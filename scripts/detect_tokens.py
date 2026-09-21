#!/usr/bin/env python3
"""Phase 0B — read a design system's token tree and PROPOSE the facts the resolver needs.

    python3 scripts/detect_tokens.py path/to/tokens.json            # a report for a person
    python3 scripts/detect_tokens.py path/to/tokens.json --json     # proposals + questions

Proposes, never decides. Every proposal carries its evidence, and everything uncertain is
returned as a question, so the skill can confirm it with the person once and write the
answers to `.claude/design-system-context.yml` under `tokens:`. Nothing here writes that file.

What is proposed, and from what:

  tiers      From the DIRECTION aliases point, not from the names. A tier that aliases almost
             nothing is primitive; one that aliases into primitive is semantic; one that
             aliases into semantic is component. Names are only a tiebreak. When several
             unprefixed groups consume semantic (`button.*`, `chip.*`), the components ARE the
             top-level groups: the component tier is proposed as `*`.
  patterns   From the observed SHAPES of component-tier paths, by POSITION: across a
             component's tokens, the position whose values are all states is `{state}`, the one
             that reads as properties is `{property}`, in whatever order the tree uses. A
             segment that names a known axis (`variant`, `size`) stays literal and the next
             becomes its slot; a varying segment nothing explains becomes `{?}` — and a
             question about that position, never about what property its values name.
  leaf_map   Component-tier property spellings the seed vocabulary cannot read. A suggested
             property is offered only where a known synonym appears in the spelling AND the
             token's $type agrees. It is a suggestion to confirm, not a mapping.
"""
import argparse, collections, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from tokens import (Tree, PROPERTIES, STATES, AXES, DEFAULT_STATES, TIER_ROLES,  # noqa: E402
                    split_state, words, suggest_property, pure_property_spelling)


def classify_tiers(tree):
    counts = collections.Counter(p.split(".")[0] for p in tree.tokens)
    points = collections.defaultdict(collections.Counter)   # tier -> Counter(target tier)
    for src, dst in tree.alias.items():
        points[src.split(".")[0]][dst.split(".")[0]] += 1

    evidence = {}
    for tier, n in counts.items():
        aliased = sum(points[tier].values())
        evidence[tier] = {"tokens": n, "aliased": aliased,
                          "points_to": dict(points[tier].most_common())}

    roles, questions = {}, []
    primitives = [t for t, e in evidence.items() if e["aliased"] <= 0.1 * e["tokens"]]
    if len(primitives) == 1:
        roles["primitive"] = primitives[0]
    for role, below in (("semantic", "primitive"), ("component", "semantic")):
        target = roles.get(below)
        if not target:
            break
        cands = [t for t, e in evidence.items() if t not in roles.values()
                 and e["points_to"] and max(e["points_to"], key=e["points_to"].get) == target]
        if len(cands) == 1:
            roles[role] = cands[0]
        elif len(cands) > 1:
            named = [c for c in cands if role in c or c in role]
            if len(named) == 1:
                roles[role] = named[0]
            elif role == "component" and not named:
                # Several groups consume the semantic tier and none is called "component":
                # the components ARE the top-level groups — `button.*`, `chip.*` — with no
                # namespace. `*` claims every group left over; a list, only these.
                rest = [t for t in evidence if t not in roles.values()]
                roles[role] = "*" if sorted(cands) == sorted(rest) else sorted(cands)
    for role in TIER_ROLES:
        if role not in roles:
            questions.append({"about": "tiers.%s" % role,
                              "question": "Which top-level group is the %s tier?" % role,
                              "options": sorted(counts), "evidence": evidence})
    return roles, evidence, questions


def propose_patterns(tree, component_tier):
    """Generalise component-tier paths into templates, deciding the TAIL from sibling evidence.

    Which segment names the property cannot be read from one path. It is read from its
    siblings — the tokens sharing the same parent:

      1. every sibling's last segment is a state      -> `{property}.{state}`
                                                          (`bgColor.default`, `bgColor.hover`)
      2. the siblings' last segments do NOT read as    -> `{property}.{?}`: the last segment is
         properties, and either the parent does, or      an axis value, not a property
         the same sibling set recurs under another       (`padding-inline.lg`;
         parent in the scope                              `icon-color.info` beside
                                                          `surface-color.info`)
      3. otherwise                                     -> `{property}`

    Recurrence alone decides nothing: `variant.primary.{background, text}` beside
    `variant.ghost.{background, text}` recurs exactly like `icon-color.{info, error}` beside
    `surface-color.{info, error}`. What separates them is which LAYER reads as properties.

    Rule 1 needs EVERY sibling to be a state. `error` alone is in the state list, but beside
    `info`, `success` and `warning` it is a tone — reading it as a state is the trap the
    resolver refuses to fall into without a declared pattern, so detection must not either.
    """
    paths = [p for p in sorted(tree.tokens) if p.split(".")[0] == component_tier and p.count(".") >= 2]
    finals = collections.defaultdict(set)
    for p in paths:
        finals[tuple(p.split(".")[:-1])].add(p.split(".")[-1])

    def recurs(parent):
        values, scope, depth = finals[parent], parent[:2], len(parent)
        return len(values) >= 2 and any(
            other != parent and other[:2] == scope and len(other) == depth and finals[other] == values
            for other in finals)

    def readable(seg, token_type):
        from tokens import split_state
        base, _ = split_state(seg)
        return (base in tree.leafmap) or bool(suggest_property(base, token_type))

    def finals_read_as_properties(parent, token_type):
        values = finals[parent]
        return sum(1 for v in values if readable(v, token_type)) * 2 >= len(values)

    templates = collections.OrderedDict()

    # ---- position first ----------------------------------------------------------------
    # Names do not all put the property last: `button.background.hover.primary` is property,
    # state, variant. Which POSITION holds what is read across a component's tokens of one
    # depth: the position whose values are all states is `{state}`; the one whose values
    # mostly read as properties is `{property}`. Only when the property is NOT last is the
    # shape taken from positions — every property-last tree keeps the sibling reading below,
    # which knows more about tails. Reading the last segment as a property here once asked
    # "which property does `primary` name?" — a question whose answer corrupts every lookup.
    positional = set()
    groups = collections.defaultdict(list)
    for p in paths:
        groups[(p.split(".")[1], p.count("."))].append(p)
    for (scope, _), members in groups.items():
        if len(members) < 2:
            continue
        rows = [m.split(".") for m in members]
        ttype = tree.tokens[members[0]]["type"]
        slots, prop_at = [], []
        for i in range(2, len(rows[0])):
            vals = {r[i] for r in rows}
            if len(vals) == 1 and next(iter(vals)) in AXES:
                slots.append(next(iter(vals)))
            elif slots and slots[-1] in AXES:
                slots.append("{%s}" % slots[-1])
            elif len(vals) >= 2 and vals <= set(STATES) | set(DEFAULT_STATES):
                slots.append("{state}")
            elif sum(1 for v in vals if readable(v, ttype)) * 2 > len(vals):
                slots.append("{property}")
                prop_at.append(i)
            elif len(vals) == 1:
                slots.append(next(iter(vals)))
            else:
                slots.append("{?}")
        if len(prop_at) != 1 or prop_at[0] == len(rows[0]) - 1:
            continue                                # property last, or unclear: the reading below
        tpl = ".".join([component_tier, "{component}"] + slots)
        entry = templates.setdefault(tpl, {"examples": [], "unknown": collections.defaultdict(
            lambda: collections.defaultdict(set)), "by_scope": collections.defaultdict(list)})
        for m, r in zip(members, rows):
            positional.add(m)
            if len(entry["examples"]) < 3:
                entry["examples"].append(m)
            entry["by_scope"][scope].append(m)
            for i, slot in enumerate(slots):
                if slot == "{?}":
                    entry["unknown"][i + 2][scope].add(r[i + 2])

    for path in paths:
        if path in positional:
            continue
        segs = path.split(".")
        rest, parent, ttype = segs[2:], tuple(segs[:-1]), tree.tokens[path]["type"]
        last = rest[-1]
        if len(rest) >= 2 and finals[parent] <= set(STATES) | set(DEFAULT_STATES):
            head, tail = rest[:-2], ["{property}", "{state}"]
        elif len(rest) >= 2 and not finals_read_as_properties(parent, ttype) and \
                (readable(rest[-2], ttype) or recurs(parent)):
            head, tail = rest[:-2], ["{property}", "{?}"]
        else:
            head, tail = rest[:-1], ["{property}"]
        out = []
        for i, seg in enumerate(head):
            if seg in AXES:
                out.append(seg)
            elif i > 0 and head[i - 1] in AXES:
                out.append("{%s}" % head[i - 1])
            else:
                out.append("{?}")
        slots = out + tail
        tpl = ".".join([component_tier, "{component}"] + slots)
        entry = templates.setdefault(tpl, {"examples": [], "unknown": collections.defaultdict(
            lambda: collections.defaultdict(set)), "by_scope": collections.defaultdict(list)})
        if len(entry["examples"]) < 3:
            entry["examples"].append(path)
        entry["by_scope"][segs[1]].append(path)
        for i, slot in enumerate(slots):
            if slot == "{?}":
                entry["unknown"][i + 2][segs[1]].add(rest[i])
    return templates


# A token whose name does not carry its property (Carbon's `tertiary` is text colour, its
# `tertiary-hover` a background) can still be read — its `$description` says what it colours.
# These are the openings a description uses; the first that matches wins, and several
# properties are allowed, because one token can serve two.
PROPERTY_WORDS = {"background", "bg", "fill", "surface", "border", "outline",
                  "stroke", "color", "text", "icon", "foreground"}

DESCRIPTION_ROLES = [
    (re.compile(r"^\s*border and text colou?r", re.I), ["border-color", "foreground"]),
    (re.compile(r"^\s*(text and icon|text|icon|foreground) colou?r", re.I), ["foreground"]),
    (re.compile(r"^\s*(background|fill|surface) colou?r", re.I), ["background"]),
    (re.compile(r"^\s*(border|outline|stroke)(/(border|outline|stroke))? colou?r", re.I), ["border-color"]),
    (re.compile(r"^\s*(border|stroke) width", re.I), ["border-width"]),
    (re.compile(r"^\s*(corner )?radius", re.I), ["radius"]),
]


def propose_reading(tree, path):
    """(reading, evidence) for an unreadable component token, or (None, why)."""
    tok = tree.tokens[path]
    desc = tok.get("desc") or ""
    props = next((roles for rx, roles in DESCRIPTION_ROLES if rx.search(desc)), None)
    if not props:
        return None, "its $description does not say what it colours: %r" % desc[:80]
    leaf = path.split(".")[-1]
    if leaf in STATES:
        variant, state = None, leaf        # `disabled`: the state itself, across every variant
    else:
        variant, state = split_state(leaf)
        # A name can lead with its property word — Carbon's `tag.background-blue`,
        # `tag.color-blue`. That word is the property the description already gave; what is
        # left is the variant, `blue`. Left in, 36 tag proposals would have named a variant
        # `background-blue`.
        w = variant.split("-")
        while len(w) > 1 and w[0] in PROPERTY_WORDS:
            w = w[1:]
        variant = "-".join(w)
    reading = {"property": props[0] if len(props) == 1 else props}
    if variant:
        reading["variant"] = variant
    if state:
        reading["state"] = state
    return reading, desc


def detect(tree_path, context=None):
    facts = dict((context or {}).get("tokens") or {})
    if facts.get("sources"):
        # Tiers are DECLARED per source file, so nothing is inferred. Inferring would be wrong
        # here anyway: Carbon's component tokens alias the palette directly, skipping semantic,
        # which alias direction would read as a second primitive-facing tier.
        base = Tree(tree_path, {"sources": facts["sources"], "theme": facts.get("theme")})
        roles = {r: r for r in TIER_ROLES if any(t.startswith(r + ".") for t in base.tokens)}
        _, evidence, _ = classify_tiers(base)
        questions = []
    else:
        base = Tree(tree_path)
        roles, evidence, questions = classify_tiers(base)
    comp = roles.get("component")
    if comp == "*" or isinstance(comp, list):
        # Read the unprefixed groups as the component tier, under `component.`, from here on.
        base = Tree(tree_path, {"tiers": roles, **({"sources": facts["sources"], "theme": facts.get("theme")}
                                                   if facts.get("sources") else {})})
        comp = "component"
    patterns = propose_patterns(base, comp) if comp else {}

    # A `{?}` shared by several components can mean different things in each — badge's last
    # segment is a size, toast's is a tone. One generic template cannot hold two answers, so
    # when more than one component contributes to an unknown, it splits: one template and one
    # question per component, the component's name written in as a literal. Specific
    # templates come first, because the resolver takes the first pattern that matches.
    specific, generic, pattern_questions = [], [], []
    for tpl, info in patterns.items():
        if sum(len(v) for v in info["by_scope"].values()) < 2:
            continue      # one token is not a pattern; it is a question about that token
        if not info["unknown"]:
            generic.append({"template": tpl, "examples": info["examples"], "needs_answer": False})
            continue
        scopes = sorted({sc for per in info["unknown"].values() for sc in per})
        # Split per component only when the components DISAGREE — badge's sizes vs toast's
        # tones. Primer's button, buttonCounter and buttonKeybindingHint all vary by the same
        # danger/default/invisible/primary, and asking that three times is noise.
        split = len(scopes) > 1 and any(len({frozenset(v) for v in per.values()}) > 1
                                        for per in info["unknown"].values())
        for sc in (scopes if split else [None]):
            t = tpl.replace("{component}", sc) if sc else tpl
            examples = info["by_scope"][sc][:3] if sc else info["examples"]
            for pos, per in sorted(info["unknown"].items()):
                values = per[sc] if sc else set().union(*per.values())
                pattern_questions.append({
                    "about": "patterns.component",
                    "question": "In `%s`, what does segment %d vary by? It takes the values %s."
                                % (t, pos + 1, ", ".join(sorted(values))),
                    "options": [a for a in AXES if a != "state"],
                    "template": t, "position": pos, "examples": examples,
                    # the components that actually CONTRIBUTED this unknown — never read off the
                    # template text, which stays generic when only one component has the shape
                    "components": [sc] if sc else sorted(per)})
            (specific if sc else generic).append({"template": t, "examples": examples, "needs_answer": True})
    proposed_patterns = specific + generic

    # Re-read the tree through the proposed facts, with unknown slots treated as `{*}`, to
    # find the property spellings that remain unreadable.
    reread = {"tiers": roles,
              "patterns": {"component": [p["template"].replace("{?}", "{*}") for p in proposed_patterns]}}
    for k in ("sources", "theme", "leaf_map", "readings"):
        if facts.get(k):
            reread[k] = facts[k]
    if facts.get("patterns"):
        reread["patterns"] = facts["patterns"]      # confirmed patterns beat proposed ones
    tree = Tree(tree_path, reread)
    unread = collections.OrderedDict()
    for path, tok in sorted(tree.tokens.items()):
        if tree.role_of(path) != "component":
            continue
        spelling, _ = tree.base_state(path)
        if tree.prop_of(path)[0] is None:
            entry = unread.setdefault(spelling, {"type": tok["type"], "examples": []})
            if len(entry["examples"]) < 2:
                entry["examples"].append(path)

    # How often each property spelling recurs. A spelling used by many tokens is VOCABULARY —
    # Primer's `iconColor` across 13 tokens is one question, even though no seed word reads it.
    # Counted over DISTINCT PARENTS — different variants or parts — not over states of one
    # token: Carbon's `notification.action-tertiary-inverse` appears three times only as
    # itself, `-active` and `-hover`, and that is one token family, not vocabulary.
    parents = collections.defaultdict(set)
    for p in tree.tokens:
        if tree.role_of(p) != "component":
            continue
        spelling = tree.base_state(p)[0]
        segs = p.split(".")
        parent = tuple(segs[:-1]) if split_state(segs[-1])[0] == spelling else tuple(segs[:-2])
        parents[spelling].add(parent)
    spelling_count = {s: len(ps) for s, ps in parents.items()}
    proposed_readings, reading_questions = {}, []
    for path in sorted(tree.tokens):
        if tree.role_of(path) != "component" or tree.prop_of(path)[0] is not None:
            continue
        # A name that DOES carry its property, in a spelling not yet mapped — Primer's
        # `bgColor`, `fgColor` — is one spelling question for hundreds of tokens, not a reading
        # per token. Readings are for names that carry no property at all (Carbon's `tertiary`),
        # and asked per token there, 358 Primer questions would have replaced ~10.
        spelling = tree.base_state(path)[0]
        if pure_property_spelling(spelling, tree.tokens[path]["type"]) or spelling_count[spelling] >= 3:
            continue
        reading, why = propose_reading(tree, path)
        if reading:
            proposed_readings[path] = {"reading": reading, "evidence": why}
            unread.pop(tree.base_state(path)[0], None)
        else:
            unread.pop(tree.base_state(path)[0], None)   # one question per token, never two
            reading_questions.append({"about": "readings.%s" % path,
                                      "question": "What does `%s` colour or size? %s" % (path, why),
                                      "options": list(PROPERTIES)})

    leaf_questions = []
    for spelling, info in unread.items():
        leaf_questions.append({
            "about": "leaf_map.%s" % spelling,
            "question": "Which property does `%s` (%s) name? e.g. %s"
                        % (spelling, info["type"], ", ".join(info["examples"])),
            "suggested": suggest_property(spelling, info["type"]),
            "options": [p for p, s in PROPERTIES.items() if s["type"] == info["type"]],
            "examples": info["examples"]})

    # Which component each question concerns. A pattern whose template names its component
    # literally, a reading of one token, a spelling used by some components and not others.
    # `None` means system-wide: asked in Phase 0B. Everything else waits for the component.
    spelling_scopes = collections.defaultdict(set)
    for p in tree.tokens:
        if tree.role_of(p) == "component":
            spelling_scopes[tree.base_state(p)[0]].add(tree.scope_of(p))
    for q in questions + pattern_questions + reading_questions + leaf_questions:
        about = q["about"]
        if about.startswith("patterns"):
            pass                                       # set where the question was built
        elif about.startswith("readings."):
            q["components"] = [tree.scope_of(about[len("readings."):])]
        elif about.startswith("leaf_map."):
            used = sorted(s for s in spelling_scopes.get(about[len("leaf_map."):], set()) if s)
            q["components"] = used or None
        else:
            q["components"] = None

    # Shared groups. A component-tier group is not always one component — `control.*` can serve
    # a button and a segmented-control tab alike. The tree shows the groups; it rarely says who
    # uses them, so that is asked once, system-wide. A later component that could draw from a
    # declared group it is not a member of is asked by the resolver, when it needs the token.
    groups = sorted({s for s in (tree.scope_of(p) for p in tree.tokens) if s})
    if len(groups) > 1 and not facts.get("shared"):
        questions.append({
            "about": "shared",
            "question": "Which of these component-token groups are SHARED patterns — used by more "
                        "than one component — and which components use each? %s"
                        % ", ".join("`%s`" % g for g in groups),
            "options": groups, "components": None})

    return {
        "tree": str(tree_path),
        "tiers": {"proposed": roles, "evidence": evidence},
        "scopes": sorted({s for s in (tree.scope_of(p) for p in tree.tokens) if s}),
        "patterns": proposed_patterns,
        "derived_roles": len(tree.derived),
        "readings": proposed_readings,
        "questions": questions + pattern_questions + reading_questions + leaf_questions,
    }


def report(d):
    out = ["# Token tree — proposed facts", "", "`%s`" % d["tree"], "", "## Tiers", ""]
    for tier, e in sorted(d["tiers"]["evidence"].items()):
        role = next((r for r, t in d["tiers"]["proposed"].items() if t == tier), "?")
        out.append("- `%s` → **%s** — %d tokens, %d aliased%s" % (
            tier, role, e["tokens"], e["aliased"],
            (", pointing into " + ", ".join("`%s` (%d)" % kv for kv in e["points_to"].items()))
            if e["points_to"] else ""))
    out += ["", "## Component scopes", "", ", ".join("`%s`" % s for s in d["scopes"]) or "*none*",
            "", "## Naming patterns", ""]
    for p in d["patterns"]:
        out.append("- `%s`%s — e.g. `%s`"
                   % (p["template"], "  **needs an answer**" if p["needs_answer"] else "",
                                            p["examples"][0]))
    if d.get("readings"):
        out += ["", "## Proposed readings (%d) — from each token's own description; confirm, never assume"
                    % len(d["readings"]), ""]
        for path, r in sorted(d["readings"].items()):
            rd = r["reading"]
            out.append("- `%s` → **%s**%s%s — \"%s\"" % (
                path, rd["property"] if isinstance(rd["property"], str) else " + ".join(rd["property"]),
                (" · variant `%s`" % rd["variant"]) if rd.get("variant") else "",
                (" · state `%s`" % rd["state"]) if rd.get("state") else "",
                r["evidence"][:70]))
    out += ["", "## Questions (%d)" % len(d["questions"]), ""]
    for q in d["questions"]:
        sug = (" — suggested: **%s**" % ", ".join(q["suggested"])) if q.get("suggested") else ""
        out.append("- %s%s" % (q["question"], sug))
    if not d["questions"]:
        out.append("*None — every tier, pattern and property spelling was read.*")
    out += ["", "%d semantic tokens have a role derived from the alias graph." % d["derived_roles"]]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Propose design-system token facts for Phase 0B.")
    ap.add_argument("tree", help="path to the token tree — or, with --context declaring "
                                 "`tokens.sources`, the directory those sources are relative to")
    ap.add_argument("--context", help="design-system context file whose `tokens:` facts to apply")
    ap.add_argument("--component", help="only the questions this component needs, plus the "
                                        "system-wide ones — how the rest stay unasked until needed")
    ap.add_argument("--json", action="store_true", help="machine-readable proposals and questions")
    args = ap.parse_args()
    context = None
    if args.context:
        import context as ctx
        context = ctx.load(args.context)
    d = detect(args.tree, context)
    if args.component:
        scope = args.component
        d["questions"] = [q for q in d["questions"]
                          if q.get("components") is None or scope in q["components"]]
        d["readings"] = {p: r for p, r in d["readings"].items() if p.split(".")[1] == scope}
    print(json.dumps(d, indent=2, default=list) if args.json else report(d))


if __name__ == "__main__":
    # Phase 0A is an instruction; this is the mechanism. Every script that runs early in a
    # run carries it, so the freshness check happens whether or not anyone asked for it.
    import check_references
    check_references.notice()
    main()
