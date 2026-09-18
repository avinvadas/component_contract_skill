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
             aliases into semantic is component. Names are only a tiebreak.
  patterns   From the observed SHAPES of component-tier paths. A segment that names a known
             axis (`variant`, `size`) stays literal and the next becomes its slot; a final
             segment that is a state becomes `{state}`; a varying segment nothing explains
             becomes `{?}` — and a question.
  leaf_map   Component-tier property spellings the seed vocabulary cannot read. A suggested
             property is offered only where a known synonym appears in the spelling AND the
             token's $type agrees. It is a suggestion to confirm, not a mapping.
"""
import argparse, collections, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from tokens import Tree, PROPERTIES, STATES, AXES, DEFAULT_STATES, TIER_ROLES, split_state  # noqa: E402


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
    for path in paths:
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


def words(spelling):
    """`bgColor` -> [bg, color]; `icon-color` -> [icon, color]."""
    spaced = re.sub(r"(?<=[a-z0-9])([A-Z])", r" \1", spelling)
    return [w for w in re.split(r"[\s_\-.]+", spaced.lower()) if w]


def suggest_property(spelling, token_type):
    """Properties whose synonym appears as WHOLE WORDS in the spelling, $type permitting.

    Whole words, because substrings coincide: `iconcolor` contains `oncolor`, which once
    suggested `icon-color` means *on-color*. A suggestion is still only a suggestion.
    """
    w = words(spelling)
    hits = []
    for prop, spec in PROPERTIES.items():
        if spec["type"] != token_type:
            continue
        for syn in sorted(spec["syn"], key=len, reverse=True):
            sw = words(syn)
            if any(w[i:i + len(sw)] == sw for i in range(len(w) - len(sw) + 1)):
                hits.append(prop)
                break
    return hits


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
    patterns = propose_patterns(base, comp) if comp else {}

    # A `{?}` shared by several components can mean different things in each — badge's last
    # segment is a size, toast's is a tone. One generic template cannot hold two answers, so
    # when more than one component contributes to an unknown, it splits: one template and one
    # question per component, the component's name written in as a literal. Specific
    # templates come first, because the resolver takes the first pattern that matches.
    specific, generic, pattern_questions = [], [], []
    for tpl, info in patterns.items():
        if not info["unknown"]:
            generic.append({"template": tpl, "examples": info["examples"], "needs_answer": False})
            continue
        scopes = sorted({sc for per in info["unknown"].values() for sc in per})
        split = len(scopes) > 1
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
                    "template": t, "position": pos, "examples": examples})
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

    proposed_readings, reading_questions = {}, []
    for path in sorted(tree.tokens):
        if tree.role_of(path) != "component" or tree.prop_of(path)[0] is not None:
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
        out.append("- `%s`%s — e.g. `%s`" % (p["template"], "  **needs an answer**" if p["needs_answer"] else "",
                                            p["examples"][0]))
    if d.get("readings"):
        out += ["", "## Proposed readings (%d) — from each token's own description; confirm, never assume" % len(d["readings"]), ""]
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
    ap.add_argument("--json", action="store_true", help="machine-readable proposals and questions")
    args = ap.parse_args()
    context = None
    if args.context:
        import context as ctx
        context = ctx.load(args.context)
    d = detect(args.tree, context)
    print(json.dumps(d, indent=2, default=list) if args.json else report(d))


if __name__ == "__main__":
    main()
