#!/usr/bin/env python3
"""Token-tree analysis and slot resolution.

Three things, in order of how much they can be trusted:

1. STRUCTURE — tiers, component scopes, dimension axes. Read from paths. Always reliable.
2. LEAF MEANING — which property a leaf segment names. NOT readable from paths. Derived
   from the alias graph where a component leaf annotates the semantic token it consumes,
   and from a seed table of synonyms where it cannot be.
3. RESOLUTION — (property, scope, dimensions) -> a token, or a named reason it is absent.

The states a slot can land in are closed, and only one of them is "nothing is wrong":

    bound             a single token satisfies property + type + dimensions
    not-applicable    the property does not apply to this component (declared, with reason)
    absent-from-tree  the property applies; no token anywhere expresses it
    ambiguous         more than one candidate survived; scope and dimension did not narrow
    dimension-unmet   a token matches the property but cannot carry the state/variant
    unmapped-leaf     a candidate probably exists; we could not read which leaf means this

`unmapped-leaf` is kept separate from `absent-from-tree` on purpose. Merging them tells
someone to add a token that already exists under a name we failed to parse, which pollutes
the very tree this is meant to protect.
"""
import json, re

# ---- property vocabulary -----------------------------------------------------------
# The canonical property names a contract may declare, each with the $type a token must
# carry to satisfy it, and the leaf spellings seen in the wild. The synonym lists are a
# SEED, not an authority: the alias graph extends them per design system.
PROPERTIES = {
    "background":     {"type": "color",     "syn": ["background", "bg", "fill", "surface"]},
    "foreground":     {"type": "color",     "syn": ["foreground", "fg", "text", "content", "label",
                                                    "on-color"]},
    "border-color":   {"type": "color",     "syn": ["border", "border-color", "stroke", "outline"]},
    "border-width":   {"type": "dimension", "syn": ["border-width", "stroke-width"]},
    "radius":         {"type": "dimension", "syn": ["radius", "corner-radius", "border-radius"]},
    "padding-inline": {"type": "dimension", "syn": ["padding-inline", "padding-x", "padding"]},
    "padding-block":  {"type": "dimension", "syn": ["padding-block", "padding-y"]},
    "font-size":      {"type": "dimension", "syn": ["font-size", "text-size"]},
    "elevation":      {"type": "shadow",    "syn": ["elevation", "shadow"]},
    "opacity":        {"type": "number",    "syn": ["opacity", "alpha"]},
    "focus-ring":     {"type": "color",     "syn": ["focus-ring", "ring"]},
    "duration":       {"type": "duration",  "syn": ["duration", "enter-duration", "exit-duration"]},
    # Type, spacing, size and motion are tokenised as often as colour is. A property may accept
    # more than one $type where design systems genuinely differ: a line height is a length in one
    # tree and a unitless number in another, and both are the same fact about the component.
    "font-family":    {"type": ("fontFamily", "other"), "syn": ["font-family", "typeface", "font"]},
    "font-weight":    {"type": ("fontWeight", "number"), "syn": ["font-weight", "weight"]},
    "line-height":    {"type": ("dimension", "number"), "syn": ["line-height", "leading"]},
    "letter-spacing": {"type": "dimension", "syn": ["letter-spacing", "tracking"]},
    "gap":            {"type": "dimension", "syn": ["gap", "spacing", "space-between"]},
    "height":         {"type": "dimension", "syn": ["height", "control-height", "min-height"]},
    "easing":         {"type": ("cubicBezier", "other"), "syn": ["easing", "curve", "timing-function"]},
}

def types_of(prop):
    """The $type(s) a token must carry to satisfy a property."""
    t = PROPERTIES[prop]["type"]
    return t if isinstance(t, tuple) else (t,)

def fits(prop, token_type):
    return token_type in types_of(prop)

# State suffixes fused into a leaf. `background-hover` is one segment carrying two facts.
STATES = ["hover", "pressed", "active", "focus-visible", "focus", "disabled", "selected", "checked", "error"]

# Segments that introduce a dimension axis; the segment after one is that axis's value.
AXES = ["variant", "size", "state", "mode", "tone", "emphasis", "density"]

# When a naming pattern gives state its own segment, a token with no interaction state still
# needs a leaf — `bgColor.default`. These spellings mean "no state".
DEFAULT_STATES = ["default", "rest", "base", "enabled", "idle"]

TIER_ROLES = ("primitive", "semantic", "component")

REF = re.compile(r"^\{(.+?)\}$")


def _leaves(node, path=""):
    if isinstance(node, dict):
        if "$value" in node or "value" in node:
            yield path, node
            return
        for k, v in node.items():
            if k.startswith("$"):
                continue           # $description, $extensions: metadata, never a group of tokens
            yield from _leaves(v, (path + "." + k) if path else k)


def _dig(node, path):
    """Follow a key path. A LIST of keys, or a `/`-separated string — never dots, because real
    extension keys contain them: Carbon's is literally `carbon.themes`."""
    parts = path if isinstance(path, list) else str(path).split("/")
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _themed(node, value_path):
    """Give a node a `$value` from its themed extension when it has none of its own.

    Carbon's component tokens carry no `$value` at all: the value exists per theme, under
    `$extensions -> carbon.themes -> white`. A reader that only knows `$value` sees zero tokens.
    """
    if isinstance(node, dict):
        out = {k: _themed(v, value_path) for k, v in node.items()}
        if "$value" not in node and "value" not in node and "$type" in node and value_path:
            v = _dig(node, value_path)
            if v is not None:
                out["$value"] = v
        return out
    return node



# ---- tokens written as CSS custom properties (shadcn, and most Tailwind systems) ------------
CSS_VAR_DECL = re.compile(r"--([\w-]+)\s*:\s*([^;]+);")
CSS_VAR_REF = re.compile(r"^\s*var\(\s*--([\w-]+)\s*\)\s*$")

def _css_block(text, selector):
    """The declarations inside every block whose selector is exactly `selector`, joined.

    `@theme` counts as a selector of its own: Tailwind v4 (and so shadcn, and any system built
    on it) declares its non-colour tokens — radius, type, spacing — inside `@theme`, not in
    `:root`. Reading only `:root` once reported shadcn's radius as absent from its own tree.
    """
    out = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
        # Only the LAST line before `{` is the selector: what precedes it is the previous
        # statement — `@import "tailwindcss";` once made every selector unreadable.
        head = m.group(1).strip().split("\n")[-1].strip()
        sels = [x.strip() for x in head.split(",")]
        if selector in sels or (selector == "@theme" and sels[0].split(" ")[0] == "@theme"):
            out.append(m.group(2))
    return "\n".join(out) or None

def _css_type(value):
    v = value.strip().lower()
    if re.match(r"^(oklch|oklab|rgb|rgba|hsl|hsla|color|lab|lch)\(|^#[0-9a-f]{3,8}$", v):
        return "color"
    if re.match(r"^-?[\d.]+(px|rem|em|%)$|^calc\(", v):
        return "dimension"
    if re.match(r"^-?[\d.]+(ms|s)$", v):
        return "duration"
    return None

def load_css(path, selector=":root"):
    """A CSS file as a token tree: the custom properties of one theme's block.

    CSS variables carry no $type, so it is inferred from the value, and an exact `var(--x)` is
    an alias — `{x}` — so the alias graph reads it like any DTCG alias. The theme is a SELECTOR:
    shadcn's light theme is `:root`, its dark theme `.dark`, redefining the same names."""
    text = re.sub(r"/\*.*?\*/", "", open(path).read(), flags=re.S)
    # A theme selector OVERRIDES `:root` — shadcn's `.dark` redefines the colours and inherits
    # `--radius`, so reading `.dark` alone would lose every token it does not repeat.
    blocks = [_css_block(text, "@theme"), _css_block(text, ":root")] + \
            ([_css_block(text, selector)] if selector != ":root" else [])
    if not any(blocks):
        return {}
    decls = [d for b in blocks if b for d in CSS_VAR_DECL.findall(b)]
    out = {}
    for name, value in decls:
        value = value.strip()
        ref = CSS_VAR_REF.match(value)
        typ = None if ref else _css_type(value)
        out[name] = {"$value": "{%s}" % ref.group(1) if ref else value, "$type": typ}
    return out


def load_sources(base, sources, theme=None, value_path=None, problems=None, selector=None):
    """Several token files -> one tree whose top-level groups are the tiers.

    A real design system rarely ships one file with its tiers as top-level groups. Carbon's
    semantic tokens sit at the TOP of `white.json` with no tier prefix, and alias into a
    separate `color-palette.json` as `{gray.80}`. Each file is placed under its declared tier,
    and every alias is rewritten to the tier that actually defines its target — ambiguity (a
    path defined in two tiers) is reported, never guessed.
    """
    import glob as _glob, pathlib as _pl
    problems = problems if problems is not None else []
    if isinstance(value_path, list):
        vp = [str(x).replace("{theme}", theme or "") for x in value_path] if theme else None
    else:
        vp = value_path.replace("{theme}", theme) if (value_path and theme) else None
    # Tier -> paths is the shape: `{primitive: [palette.json], component: [components/*.json]}`.
    # A list of {path, tier} is accepted too, but is not written by the skill — the
    # dependency-free context reader refuses lists of mappings, deliberately.
    if isinstance(sources, dict):
        pairs = [{"tier": t, "path": pth} for t, pths in sources.items()
                 for pth in (pths if isinstance(pths, list) else [pths])]
    else:
        pairs = list(sources or [])
    tiers = {}
    for src in pairs:
        tier, pat = src.get("tier"), src.get("path")
        if tier not in ("primitive", "semantic", "component"):
            problems.append("tokens.sources: %r has tier %r — expected primitive, semantic or component"
                            % (pat, tier))
            continue
        files = sorted(_glob.glob(str(_pl.Path(base) / pat)))
        if not files:
            problems.append("tokens.sources: %r matches no file" % pat)
        for f in files:
            if f.endswith(".css"):
                data = load_css(f, selector or ":root")
            else:
                data = _themed(json.loads(open(f).read()), vp)
            for k, v in data.items():
                if not k.startswith("$"):
                    tiers.setdefault(tier, {}).setdefault(k, v)
    # where does each unprefixed path live?
    where = {}
    for tier, tree in tiers.items():
        for p, _ in _leaves(tree):
            where.setdefault(p, set()).add(tier)

    def rewrite(node):
        if isinstance(node, dict):
            return {k: rewrite(v) for k, v in node.items()}
        if isinstance(node, str):
            m = REF.match(node)
            if m:
                target = m.group(1)
                homes = where.get(target, set())
                if len(homes) == 1:
                    return "{%s.%s}" % (next(iter(homes)), target)
                if len(homes) > 1:
                    problems.append("alias {%s} is defined in more than one tier: %s"
                                    % (target, sorted(homes)))
        return node
    return {tier: rewrite(tree) for tier, tree in tiers.items()}


def split_state(leaf):
    """`background-hover` -> ('background', 'hover'). Returns (leaf, None) when stateless."""
    for s in STATES:
        if leaf.endswith("-" + s):
            return leaf[: -len(s) - 1], s
    return leaf, None


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
        if token_type not in (spec["type"] if isinstance(spec["type"], tuple) else (spec["type"],)):
            continue
        for syn in sorted(spec["syn"], key=len, reverse=True):
            sw = words(syn)
            if any(w[i:i + len(sw)] == sw for i in range(len(w) - len(sw) + 1)):
                hits.append(prop)
                break
    return hits


GENERIC_WORDS = {"color", "colour", "value"}

def pure_property_spelling(spelling, token_type):
    """Is the spelling NOTHING BUT a property? `bgColor` is (bg + color); Carbon's
    `background-blue` is not — it carries the variant `blue` too, so it is a per-token reading."""
    hits = suggest_property(spelling, token_type)
    if not hits:
        return False
    left = set(words(spelling)) - GENERIC_WORDS
    for prop in hits:
        for syn in PROPERTIES[prop]["syn"]:
            left -= set(words(syn))
    return not left


class Tree:
    def __init__(self, path, facts=None):
        """`facts` is the `tokens:` block of the design-system context, confirmed once in
        Phase 0B. Every key is optional; with none, behaviour is exactly the heuristics.

            tiers:     {primitive: core, semantic: alias, component: comp}
            patterns:  {component: ["comp.{component}.{variant}.{property}.{state}", ...],
                        semantic:  ["alias.{*}.{property}.{*}"]}
            leaf_map:  {bgColor: background, fg: foreground}
            axes:      [variant, size]
            default_states: [default, rest]

        A pattern is the only way a trailing segment is read as a state. Guessing would read
        `semantic.color.surface.error` as an error STATE, when `error` there is a tone.
        """
        self.facts = facts or {}
        self.problems = []   # a fact that is itself wrong — surfaced as lint, never ignored
        self.T = {r: r for r in TIER_ROLES}
        # A component tier WITHOUT a namespace: `button.primary.background` beside `semantic.*`,
        # every component its own top-level group. `component: "*"` claims every top-level group
        # no other tier claims; a list names them. They are read as if under `component.`, the
        # way a tier declared by FILE already is, so everything downstream sees one shape.
        declared = dict(self.facts.get("tiers") or {})
        spec = declared.get("component")
        self.component_groups = None
        if spec == "*" or isinstance(spec, list):
            self.component_groups = spec
            declared.pop("component")
        self.T.update({k: v for k, v in declared.items() if k in TIER_ROLES and v and isinstance(v, str)})
        self.axes = list(self.facts.get("axes") or AXES)
        self.default_states = list(self.facts.get("default_states") or DEFAULT_STATES)
        # Per-token READINGS, for names that do not carry the property. Carbon's `tertiary` is a
        # text colour while `tertiary-hover` is a background; `danger-secondary` is border AND
        # text. No pattern or spelling map can read that — only a statement per token can, and
        # the token's own `$description` is where the detector proposes it from.
        self.readings = {}
        for tok, r in (self.facts.get("readings") or {}).items():
            if isinstance(r, str):
                r = {"property": r}
            props = r.get("property")
            props = props if isinstance(props, list) else [props]
            bad = [x for x in props if x not in PROPERTIES]
            if bad:
                self.problems.append("tokens.readings.%s: %s is not a property"
                                     % (tok, ", ".join(map(str, bad))))
                continue
            self.readings[str(tok)] = {"property": tuple(props), "variant": r.get("variant"),
                                       "state": r.get("state")}
        # Shared groups: component-tier tokens that belong to a PATTERN, not one component —
        # `control.border-radius` serving button and segmented-control tab alike. Which
        # components a group serves is rarely in the tree itself, so it is a confirmed fact.
        self.shared = {}
        for group, comps in (self.facts.get("shared") or {}).items():
            if not isinstance(comps, list) or not comps:
                self.problems.append("tokens.shared.%s: expected a list of components" % group)
                continue
            self.shared[str(group)] = [str(c) for c in comps]
        self.patterns = {}
        for role, templates in (self.facts.get("patterns") or {}).items():
            if role not in TIER_ROLES:
                self.problems.append("tokens.patterns: %r is not a tier (%s)" % (role, ", ".join(TIER_ROLES)))
                continue
            self.patterns[role] = [self._compile(t) for t in (templates or [])]
        if self.facts.get("sources"):
            # `path` is then the directory the sources are relative to.
            theme = self.facts.get("theme") or {}
            raw = load_sources(path, self.facts["sources"], theme.get("name"), theme.get("value_path"),
                               self.problems, theme.get("selector"))
        else:
            raw = json.loads(open(path).read())
        if self.component_groups is not None:
            raw = self._namespace_components(raw)
        self.path = path
        self.tokens = {}
        for p, node in _leaves(raw):
            self.tokens[p] = {
                "type":  node.get("$type") or node.get("type"),
                "value": node.get("$value", node.get("value")),
                "desc":  node.get("$description") or node.get("comment") or "",
            }
        # ---- 1. structure ----------------------------------------------------------
        self.tiers = sorted({p.split(".")[0] for p in self.tokens})
        for role, seg in self.T.items():
            if seg not in self.tiers and (self.facts.get("tiers") or {}).get(role):
                self.problems.append("tokens.tiers.%s is %r, but no top-level %r exists in the tree"
                                     % (role, seg, seg))
        # Tokens no tier claims are invisible to every lookup — and a lookup that cannot see a
        # token calls it ABSENT, telling the tree's owner to add one that exists. So once tiers
        # are declared, an unclaimed group is a problem with the facts, named, never a silence.
        if self.facts.get("tiers") or self.facts.get("sources"):
            unclaimed = sorted(t for t in self.tiers if t not in self.T.values())
            if unclaimed:
                self.problems.append(
                    "no tier claims the top-level group(s) %s (%d tokens) — if they are components, "
                    "declare `tiers.component: \"*\"` (every unclaimed group) or list them"
                    % (", ".join(unclaimed), sum(1 for p in self.tokens if p.split(".")[0] in unclaimed)))

        # ---- alias graph -----------------------------------------------------------
        self.alias, self.consumers = {}, {}
        for p, t in self.tokens.items():
            # Only a STRING is ever an alias. DTCG 2025.10 writes a colour as an object —
            # {"colorSpace": "srgb", "components": [...]} — and its text form also starts with
            # `{`, which once made all 244 of Carbon's palette colours read as aliases.
            m = REF.match(t["value"]) if isinstance(t["value"], str) else None
            if m:
                self.alias[p] = m.group(1)
                self.consumers.setdefault(m.group(1), []).append(p)
        # ---- 2. leaf meaning -------------------------------------------------------
        # Two maps, deliberately not merged.
        #
        # `leafmap` is spelling -> property, and applies to COMPONENT-tier leaves, which
        # do name properties (`background`, `text`, `padding-inline`).
        #
        # `path_role` is a FULL PATH -> property, derived from the alias graph. It cannot
        # be keyed on the leaf: a semantic token's leaf is usually a qualifier, not a
        # property — `semantic.color.action.primary` ends in `primary`, which names a
        # variant everywhere else in the tree. Keying on the leaf would teach the resolver
        # that `primary` means background and break every other component.
        self.leafmap = {}
        for prop, spec in PROPERTIES.items():
            for s in spec["syn"]:
                self.leafmap[s] = prop
        # The design system's own spellings, confirmed once. They override the seed.
        for spelling, prop in (self.facts.get("leaf_map") or {}).items():
            if prop in PROPERTIES:
                self.leafmap[str(spelling)] = prop
            else:
                self.problems.append("tokens.leaf_map: %r maps to %r, which is not a property (%s)"
                                     % (spelling, prop, ", ".join(PROPERTIES)))
        # A component leaf consuming a semantic token annotates what that token is FOR.
        # Primitives are excluded: they are meaning-free by construction, so a role
        # derived onto one is noise at best and a wrong answer at worst.
        self.path_role, self.derived = {}, {}
        for target, cs in self.consumers.items():
            if self.role_of(target) != "semantic":
                continue
            props = set()
            for c in cs:
                base, _ = self.base_state(c)
                if base in self.leafmap:
                    props.add(self.leafmap[base])
            if len(props) == 1:
                prop = props.pop()
                self.path_role[target] = prop
                self.derived[target] = (prop, sorted(cs))
        # Scopes last: parse() prefers a template whose property slot READS, which needs the map.
        self.scopes = sorted({self.scope_of(p) for p in self.tokens if self.scope_of(p)})

    def _namespace_components(self, raw):
        """Move the unprefixed component groups under `component.`, and every alias with them."""
        claimed = {v for k, v in self.T.items() if k != "component"}
        groups = ([k for k in raw if not k.startswith("$") and k not in claimed]
                  if self.component_groups == "*" else list(self.component_groups))
        missing = [g for g in groups if g not in raw]
        if missing:
            self.problems.append("tokens.tiers.component lists %s, which the tree does not have"
                                 % ", ".join(missing))
        moved = [g for g in groups if g in raw]
        out = {k: v for k, v in raw.items() if k not in moved}
        out.setdefault("component", {}).update({g: raw[g] for g in moved})

        def rewrite(node):
            if isinstance(node, dict):
                return {k: rewrite(v) for k, v in node.items()}
            if isinstance(node, str):
                m = REF.match(node)
                if m and m.group(1).split(".")[0] in moved:
                    return "{component.%s}" % m.group(1)
            return node
        return rewrite(out)

    # ---- naming patterns ----------------------------------------------------------
    @staticmethod
    def _compile(template):
        segs = []
        for seg in str(template).split("."):
            m = re.fullmatch(r"\{(\*|[A-Za-z_][\w-]*)\}", seg)
            segs.append(("slot", m.group(1)) if m else ("lit", seg))
        return segs

    def role_of(self, path):
        head = path.split(".")[0]
        return next((r for r, seg in self.T.items() if seg == head), None)

    def parse(self, path):
        """Slots from the declared patterns the path matches, or None.

        When several match, prefer the one whose `{property}` slot actually reads as a
        property. Primer's progressBar has both `track.bgColor` (part, property) and
        `bgColor.accent` (property, variant) at the same depth; taking the first match once
        read `accent` as the property."""
        segs = path.split(".")
        matched = []
        for tpl in self.patterns.get(self.role_of(path), []):
            if len(tpl) != len(segs):
                continue
            slots = {}
            for (kind, name), seg in zip(tpl, segs):
                if kind == "lit":
                    if name != seg:
                        break
                elif name != "*":
                    slots[name] = seg
            else:
                matched.append(slots)
        if not matched:
            return None
        typ = self.tokens.get(path, {}).get("type") if hasattr(self, "tokens") else None
        for slots in matched:
            prop = slots.get("property")
            if prop and (split_state(prop)[0] in getattr(self, "leafmap", {})
                         or (typ and suggest_property(split_state(prop)[0], typ))):
                return slots
        return matched[0]

    def scope_of(self, path):
        if self.role_of(path) != "component":
            return None
        slots = self.parse(path)
        segs = path.split(".")
        if slots is not None and slots.get("component"):
            return slots["component"]
        # A template may name its component literally (`component.button.{?}.{property}`) when
        # detection split it per component; the second segment is still the component.
        return segs[1] if len(segs) >= 3 else None

    def in_scope(self, path, scope):
        return self.scope_of(path) == scope

    def groups_for(self, scope):
        """The shared groups this component draws from, in declared order."""
        return [g for g, comps in self.shared.items() if scope in comps and g != scope]

    def specificity(self, path, scope):
        """How specific a token is to this component: `component` (named for it alone),
        `shared:<group>` (a pattern several components use), `semantic` (a system-wide meaning)."""
        role = self.role_of(path)
        if role == "component":
            owner = self.scope_of(path)
            return "component" if owner == scope else "shared:%s" % owner
        return role or "unknown"

    def base_state(self, path):
        """(property spelling, state) — from the pattern when one matches, else the heuristic."""
        slots = self.parse(path)
        if slots is not None and "property" in slots:
            state = slots.get("state")
            if state in self.default_states:
                state = None
            base = slots["property"]
            if state is None and "state" not in slots:
                base, state = split_state(base)
            return base, state
        return split_state(path.split(".")[-1])

    # ---- dimensions ---------------------------------------------------------------
    def dims_of(self, path):
        if path in self.readings:
            v = self.readings[path]["variant"]
            return {"variant": v} if v else {}
        slots = self.parse(path)
        if slots is not None:
            return {k: v for k, v in slots.items() if k not in ("component", "property", "state")}
        segs = path.split(".")
        d = {}
        for i, s in enumerate(segs[:-1]):
            if s in self.axes and i + 1 < len(segs) - 1:
                d[s] = segs[i + 1]
        return d

    def prop_of(self, path):
        """(property, state) a token path expresses, or (None, state) if unreadable.

        A declared reading wins over everything: it is a confirmed statement about THIS token.
        Its property may be a tuple, when one token serves two properties."""
        if path in self.readings:
            r = self.readings[path]
            prop = r["property"][0] if len(r["property"]) == 1 else r["property"]
            return prop, r["state"]
        base, state = self.base_state(path)
        # A role derived from the alias graph is evidence about THIS path, and beats a
        # spelling match — it is what the tree's own consumers say the token is for.
        prop = self.path_role.get(path) or self.leafmap.get(base)
        if prop and not fits(prop, self.tokens[path]["type"]):
            # `border` is a colour here, a width there. $type decides, not the spelling.
            for cand in PROPERTIES:
                if base in PROPERTIES[cand]["syn"] and fits(cand, self.tokens[path]["type"]):
                    return cand, state
            return None, state
        return prop, state

    def axes_in(self, scope):
        out = {}
        for p in self.tokens:
            if self.in_scope(p, scope):
                for k, v in self.dims_of(p).items():
                    out.setdefault(k, set()).add(v)
        return {k: sorted(v) for k, v in out.items()}

    # ---- 3. resolution ------------------------------------------------------------
    def candidates(self, prop, state, role, scope=None):
        out = []
        for p in self.tokens:
            if self.role_of(p) != role or (scope is not None and not self.in_scope(p, scope)):
                continue
            pr, st = self.prop_of(p)
            if (pr == prop or (isinstance(pr, tuple) and prop in pr)) and st == state:
                out.append(p)
        return out

    def resolve(self, prop, scope, dims=None, state=None):
        """-> (token|None, state_name, detail). Component tier first, then semantic."""
        dims = dims or {}
        if prop not in PROPERTIES:
            return None, "unmapped-leaf", "%r is not a declared property" % prop

        # This component's own tokens, then the shared groups it belongs to, then semantic.
        order = ([("component", scope, "component")]
                 + [("component", g, "shared:%s" % g) for g in self.groups_for(scope)]
                 + [("semantic", None, "semantic")])
        for role, sc, where in order:
            cands = self.candidates(prop, state, role, sc)
            if dims and role == "component":
                # A candidate whose variant CONTRADICTS the one asked for is never eligible —
                # even when that leaves nothing. This once fell back to the un-narrowed list,
                # and on Carbon bound a PRIMARY button's text colour to `button.tertiary`, the
                # tertiary button's, because it was the only foreground token in scope. A token
                # with no such dimension (Carbon's `disabled`, for every variant) stays eligible.
                cands = [c for c in cands
                         if all(self.dims_of(c).get(k) == v for k, v in dims.items()
                                if k in self.dims_of(c))]
            if len(cands) == 1:
                return cands[0], "bound", where
            if len(cands) > 1:
                return None, "ambiguous", cands

        # Nothing carried the state. Does the property exist at all, stateless?
        if state:
            for role, sc, _ in order:
                base = self.candidates(prop, None, role, sc)
                if base:
                    return None, "dimension-unmet", base[0]

        # Before calling it absent: are there tokens of the right $type in this component's
        # own scope whose property this resolver simply cannot read? Then it may well exist
        # under a spelling nobody has mapped, and "absent" would send the tree owner to add a
        # duplicate. That is unmapped-leaf — the fix is a leaf_map entry, not a new token.
        #
        # The detail is example PATHS, not a guessed spelling. Without a pattern the resolver
        # cannot know which segment names the property — in `...bgColor.default` it would
        # guess `default`, and someone mapping `default: background` would poison every token
        # that ends in `.default`. A path lets a person see the shape and declare it.
        want = types_of(prop)
        unread = sorted(p for p in self.tokens
                        if self.in_scope(p, scope) and self.tokens[p]["type"] in want
                        and self.prop_of(p)[0] is None)
        if unread:
            return None, "unmapped-leaf", unread[:3]
        return None, "absent-from-tree", self.suggest(prop, state)

    def suggest(self, prop, state):
        """A path in THIS tree's shape, for the tree owner. Never written into a contract."""
        group = {"color": "color", "dimension": None, "shadow": "elevation",
                 "duration": "motion.duration", "number": "opacity",
                 "fontFamily": "type", "fontWeight": "type", "cubicBezier": "motion.easing"}
        t = types_of(prop)[0]
        stem = group.get(t)
        sem = self.T["semantic"]
        if not stem or stem == prop:
            head = sem + "." + prop
        else:
            head = sem + "." + stem + "." + prop
        return head + "." + (state or "default")
