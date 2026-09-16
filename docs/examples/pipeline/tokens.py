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
    "foreground":     {"type": "color",     "syn": ["foreground", "text", "content", "label", "on-color"]},
    "border-color":   {"type": "color",     "syn": ["border", "border-color", "stroke", "outline"]},
    "border-width":   {"type": "dimension", "syn": ["border-width", "stroke-width"]},
    "radius":         {"type": "dimension", "syn": ["radius", "corner-radius", "border-radius"]},
    "padding-inline": {"type": "dimension", "syn": ["padding-inline", "padding-x", "padding"]},
    "padding-block":  {"type": "dimension", "syn": ["padding-block", "padding-y"]},
    "font-size":      {"type": "dimension", "syn": ["font-size", "text-size"]},
    "elevation":      {"type": "shadow",    "syn": ["elevation", "shadow"]},
    "opacity":        {"type": "number",    "syn": ["opacity", "alpha"]},
    "duration":       {"type": "duration",  "syn": ["duration", "enter-duration", "exit-duration"]},
}

# State suffixes fused into a leaf. `background-hover` is one segment carrying two facts.
STATES = ["hover", "pressed", "active", "focus", "disabled", "selected", "checked", "error"]

# Segments that introduce a dimension axis; the segment after one is that axis's value.
AXES = ["variant", "size", "state", "mode", "tone", "emphasis", "density"]

REF = re.compile(r"^\{(.+?)\}$")


def _leaves(node, path=""):
    if isinstance(node, dict):
        if "$value" in node or "value" in node:
            yield path, node
            return
        for k, v in node.items():
            yield from _leaves(v, (path + "." + k) if path else k)


def split_state(leaf):
    """`background-hover` -> ('background', 'hover'). Returns (leaf, None) when stateless."""
    for s in STATES:
        if leaf.endswith("-" + s):
            return leaf[: -len(s) - 1], s
    return leaf, None


class Tree:
    def __init__(self, path):
        raw = json.loads(open(path).read())
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
        self.scopes = sorted({p.split(".")[1] for p in self.tokens
                              if p.startswith("component.") and p.count(".") >= 2})
        # ---- alias graph -----------------------------------------------------------
        self.alias, self.consumers = {}, {}
        for p, t in self.tokens.items():
            m = REF.match(str(t["value"]))
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
        # A component leaf consuming a semantic token annotates what that token is FOR.
        # Primitives are excluded: they are meaning-free by construction, so a role
        # derived onto one is noise at best and a wrong answer at worst.
        self.path_role, self.derived = {}, {}
        for target, cs in self.consumers.items():
            if not target.startswith("semantic."):
                continue
            props = set()
            for c in cs:
                base, _ = split_state(c.split(".")[-1])
                if base in self.leafmap:
                    props.add(self.leafmap[base])
            if len(props) == 1:
                prop = props.pop()
                self.path_role[target] = prop
                self.derived[target] = (prop, sorted(cs))

    # ---- dimensions ---------------------------------------------------------------
    def dims_of(self, path):
        segs = path.split(".")
        d = {}
        for i, s in enumerate(segs[:-1]):
            if s in AXES and i + 1 < len(segs) - 1:
                d[s] = segs[i + 1]
        return d

    def prop_of(self, path):
        """(property, state) a token path expresses, or (None, state) if unreadable."""
        base, state = split_state(path.split(".")[-1])
        # A role derived from the alias graph is evidence about THIS path, and beats a
        # spelling match — it is what the tree's own consumers say the token is for.
        prop = self.path_role.get(path) or self.leafmap.get(base)
        if prop and PROPERTIES[prop]["type"] != self.tokens[path]["type"]:
            # `border` is a colour here, a width there. $type decides, not the spelling.
            for cand, spec in PROPERTIES.items():
                if base in spec["syn"] and spec["type"] == self.tokens[path]["type"]:
                    return cand, state
            return None, state
        return prop, state

    def axes_in(self, scope):
        pre = "component." + scope + "."
        out = {}
        for p in self.tokens:
            if p.startswith(pre):
                for k, v in self.dims_of(p).items():
                    out.setdefault(k, set()).add(v)
        return {k: sorted(v) for k, v in out.items()}

    # ---- 3. resolution ------------------------------------------------------------
    def candidates(self, prop, state, prefix):
        out = []
        for p in self.tokens:
            if not p.startswith(prefix):
                continue
            pr, st = self.prop_of(p)
            if pr == prop and st == state:
                out.append(p)
        return out

    def resolve(self, prop, scope, dims=None, state=None):
        """-> (token|None, state_name, detail). Component tier first, then semantic."""
        dims = dims or {}
        if prop not in PROPERTIES:
            return None, "unmapped-leaf", "%r is not a declared property" % prop

        for tier_prefix, tier in (("component." + scope + ".", "component"), ("semantic.", "semantic")):
            cands = self.candidates(prop, state, tier_prefix)
            if dims and tier == "component":
                narrowed = [c for c in cands
                            if all(self.dims_of(c).get(k) == v for k, v in dims.items()
                                   if k in self.dims_of(c))]
                if narrowed:
                    cands = narrowed
            if len(cands) == 1:
                return cands[0], "bound", tier
            if len(cands) > 1:
                return None, "ambiguous", cands

        # Nothing carried the state. Does the property exist at all, stateless?
        if state:
            for tier_prefix in ("component." + scope + ".", "semantic."):
                base = self.candidates(prop, None, tier_prefix)
                if base:
                    return None, "dimension-unmet", base[0]
        return None, "absent-from-tree", self.suggest(prop, state)

    def suggest(self, prop, state):
        """A path in THIS tree's shape, for the tree owner. Never written into a contract."""
        group = {"color": "color", "dimension": None, "shadow": "elevation",
                 "duration": "motion.duration", "number": "opacity"}
        t = PROPERTIES[prop]["type"]
        stem = group.get(t)
        if not stem or stem == prop:
            head = "semantic." + prop
        else:
            head = "semantic." + stem + "." + prop
        return head + "." + (state or "default")
