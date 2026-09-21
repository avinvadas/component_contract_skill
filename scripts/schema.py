#!/usr/bin/env python3
"""The props schema: is this a legal set of props to pass?

    python3 scripts/schema.py <Component>.md [--out DIR]

A different subject from everything else generated here. The per-platform documents describe
what a rendered implementation must produce; this validates a CONSUMER-SUPPLIED props instance,
and is consumed by ordinary build tooling that will never read a canonical document.

It was written by the skill, from the contract's own prop tables, until it was noticed that the
derivation has no judgement in it — seven mapping rows against tables with fixed columns. Left
as a per-run authoring task it cost consistency (two components could shape the same situation
differently) and, worse, it put a file in `generated/` that nothing could reproduce, so
"regenerating produces identical files" had an exception and a diff there had two meanings.

    4.3 / 5.3 / 2.3  `| prop | type | required | default | description |`
    3.1 Zones        `| zone | accepts | cardinality | position | absent | id |`

Draft 07, because that is what consumes it. One file per platform in `platforms`, since a zone
accepting `component:Icon` refs that component's schema for the SAME platform.
"""
import argparse, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from resolve import parse_frontmatter, parse_tables, kebab   # noqa: E402

PROPS = {"prop", "type"}
ZONES = {"zone", "accepts", "cardinality"}
lint: list[str] = []


def literal(cell):
    """A contract's `` `false` `` / `` `primary` `` / `—` as the JSON value it denotes."""
    v = (cell or "").strip().strip("`").strip()
    if v in ("", "—", "-"):
        return None
    if v in ("true", "false"):
        return v == "true"
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v


def type_schema(cell, prop):
    """One `type` cell as a JSON Schema fragment."""
    t = (cell or "").strip()
    if t.startswith("enum:"):
        values = [v.strip() for v in t[5:].split(",") if v.strip()]
        if not values:
            lint.append("%s: `enum:` with no values" % prop)
        return {"type": "string", "enum": values}
    if t == "boolean":
        return {"type": "boolean"}
    if t == "string":
        return {"type": "string"}
    m = re.fullmatch(r"(number|integer)(?::(-?[\d.]+)\.\.(-?[\d.]+))?", t)
    if m:
        # Bounds only where the contract states them — never a default range, which would
        # reject a legal instance on the strength of something nobody wrote down.
        out = {"type": m.group(1)}
        if m.group(2) is not None:
            out["minimum"], out["maximum"] = literal(m.group(2)), literal(m.group(3))
        return out
    if t == "handler":
        # A function is not JSON, so its SHAPE cannot be checked here. It stays in the schema,
        # and stays in `required`, because "you must pass onPress" is a legal fact about a props
        # instance — and omitting it would let an instance missing a required handler validate
        # clean, which is the one thing nothing here is allowed to do.
        return {"$comment": "a handler; its shape is not expressible in JSON Schema"}
    lint.append("%s: unknown prop type %r — add it to schema.py or fix the contract" % (prop, t))
    return {}


def cardinality(cell):
    """`1` · `0..1` · `2+` · `1..3` -> (min, max or None). Cardinality grammar is resolve.py's."""
    c = (cell or "").strip()
    if re.fullmatch(r"\d+", c):
        return int(c), int(c)
    m = re.fullmatch(r"(\d+)\.\.(\d+)", c)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.fullmatch(r"(\d+)\+", c)
    if m:
        return int(m.group(1)), None
    lint.append("cardinality %r does not parse" % c)
    return 0, None


def accepts_schema(cell, platform):
    """What a zone accepts. `component:X` refs X's schema for the SAME platform."""
    a = (cell or "").strip()
    if a.startswith("component:"):
        return {"$ref": "%s.%s.schema.json" % (a.split(":", 1)[1].strip(), platform)}
    if a == "text":
        return {"type": "string"}
    return {"$comment": "accepts %s" % a} if a else {}


def build(fm, body, platform):
    name = fm["component"]
    props, required = {}, []
    for headers, rows in parse_tables(body):
        if PROPS <= set(headers):
            for r in rows:
                prop = r["prop"].strip("`")
                s = type_schema(r.get("type"), prop)
                if r.get("description"):
                    s["description"] = r["description"]
                d = literal(r.get("default"))
                if d is not None:
                    s["default"] = d
                props[prop] = s
                if (r.get("required") or "").strip().lower() == "yes":
                    required.append(prop)
        elif ZONES <= set(headers):
            for r in rows:
                zone = r["zone"].strip("`")
                lo, hi = cardinality(r.get("cardinality"))
                item = accepts_schema(r.get("accepts"), platform)
                if hi == 1:
                    s = dict(item)
                else:
                    s = {"type": "array", "items": item}
                    if lo:
                        s["minItems"] = lo
                    if hi is not None:
                        s["maxItems"] = hi
                s.setdefault("description", "zone: accepts %s" % (r.get("accepts") or "anything"))
                props[zone] = s
                if lo >= 1:
                    required.append(zone)

    doc = {"$schema": "http://json-schema.org/draft-07/schema#",
           "$id": "%s-%s" % (kebab(name), platform),
           "title": "%s props (%s)" % (name, platform),
           "$comment": "%s.md v%s. Do not edit." % (name, fm.get("version", "?")),
           "type": "object",
           # Written out although `true` is the default, because its absence reads as an
           # oversight and invites someone to close it. The contract is a FLOOR, not a
           # ceiling: it says what must hold for an implementation to be compliant, and an
           # implementation may carry whatever else it needs. "Nothing passes by accident"
           # governs requirements that EXIST going unchecked — a missing required handler
           # fails — never props the contract never spoke to.
           "additionalProperties": True}
    if required:
        # A name can be both a zone and a prop — `label` is the content in 3.1 and the API
        # surface in 5.3 — so the later table wins the schema and the name is required once.
        doc["required"] = sorted(set(required))
    doc["properties"] = props
    return doc


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("contract", help="path to <Component>.md")
    ap.add_argument("--out", help="directory (default: generated/ beside the contract)")
    args = ap.parse_args()

    path = pathlib.Path(args.contract).resolve()
    fm, body = parse_frontmatter(path.read_text())
    out = pathlib.Path(args.out).resolve() if args.out else path.parent / "generated"
    out.mkdir(parents=True, exist_ok=True)

    platforms = fm.get("platforms") or []
    if isinstance(platforms, str):
        platforms = [p.strip() for p in platforms.strip("[]").split(",") if p.strip()]
    for platform in platforms:
        doc = build(fm, body, platform)
        f = out / ("%s.%s.schema.json" % (fm["component"], platform))
        f.write_text(json.dumps(doc, indent=2) + "\n")
        print("  %-8s %d propert%s, %d required"
              % (platform, len(doc["properties"]),
                 "y" if len(doc["properties"]) == 1 else "ies", len(doc.get("required", []))))
    if lint:
        print("\nlint: %d finding(s)" % len(set(lint)))
        for x in sorted(set(lint)):
            print("  - " + x)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
