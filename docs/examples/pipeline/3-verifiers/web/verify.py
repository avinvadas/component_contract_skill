#!/usr/bin/env python3
"""A deliberately limited web verifier.

It parses HTML with the standard library: no browser, no layout, no interaction. That is
the point. It declares what it cannot observe, and every requirement needing one of those
is reported `unverified` by name with the verifier's own reason — never passed.

Strategy is `witness`: it satisfies a scenario by finding an instance whose props match the
predicate. It never constructs one. A predicate with no witness is `unverified`, and says so.
"""
import json, pathlib, sys
from html.parser import HTMLParser

HERE = pathlib.Path(__file__).parent
DOC = json.loads((HERE.parent.parent / "2-canonical/Button.web.canonical.json").read_text())
CAP = json.loads((HERE / "capability.json").read_text())
WIT = json.loads((HERE / "witnesses.json").read_text())["witnesses"]

class Tree(HTMLParser):
    def __init__(self): super().__init__(); self.root=None; self.stack=[]
    def handle_starttag(self, tag, attrs):
        n = {"tag": tag, "attrs": dict(attrs), "text": "", "children": []}
        if self.stack: self.stack[-1]["children"].append(n)
        else: self.root = n
        self.stack.append(n)
    def handle_endtag(self, tag):
        if self.stack: self.stack.pop()
    def handle_data(self, data):
        if self.stack: self.stack[-1]["text"] += data.strip()

def parse(html):
    t = Tree(); t.feed(html); return t.root

def zone(node, name):
    if node.get("attrs", {}).get("data-zone") == name: return node
    for c in node["children"]:
        if (f := zone(c, name)): return f

def accessible_name(node):
    """Crude: concatenated text of children not aria-hidden. Not the browser's algorithm."""
    if node["attrs"].get("aria-hidden") == "true": return ""
    return (node["text"] + "".join(accessible_name(c) for c in node["children"])).strip()

def zones_in(node, out=None):
    out = set() if out is None else out
    if node["attrs"].get("data-zone"):
        out.add(node["attrs"]["data-zone"])
    for c in node["children"]:
        zones_in(c, out)
    return out

def matches(predicate, witness):
    """Every bucket of the predicate must be satisfied, or the witness does not match.

    This once read only `props`, so a predicate over `environment`, `zones` or `state` matched
    every witness — `all()` of nothing is true. Requirements conditioned on a keyboard, a hover,
    or an icon being present were checked against instances that never established any of it,
    and two of them passed by coincidence. A bucket this verifier cannot establish is a
    coverage gap, reported as one — never a match.
    """
    for bucket, want in predicate.items():
        if bucket == "props":
            if any(witness["props"].get(k) != v for k, v in want.items()):
                return False
        elif bucket == "zones":
            # Observed from the markup, not asserted by the witness author.
            present = zones_in(parse(witness["html"]))
            for zone, cond in want.items():
                if (cond == "present") != (zone in present):
                    return False
        else:
            # environment, state, machine: static HTML cannot establish these. A witness may
            # declare them explicitly; otherwise nothing here satisfies the predicate.
            declared = witness.get(bucket, {})
            if any(declared.get(k) != v for k, v in want.items()):
                return False
    return True

def observe(req, root):  # noqa: C901
    o, exp = req["observe"], req["expect"]
    if o == "role":
        got = root["attrs"].get("role") or root["tag"]
        ok, why = got == exp.get("equals"), f"role={got!r}"
        # `also` carries a second observation of the same requirement. Here it is the one
        # that matters: a div patched with role=button satisfies the role check and fails
        # identity, which is the entire reason the two are separate observations.
        if ok and (ident := req.get("also", {}).get("identity")):
            if root["tag"] not in ident.get("one_of", []):
                return (False, f"role={got!r} but rendered tag is <{root['tag']}>, not {ident['one_of']}")
        return (ok, why)
    if o == "name":
        n = accessible_name(root)
        if "present" in exp:  return (bool(n) == exp["present"], f"name={n!r}")
        if "absent_from" in exp:
            icon = zone(root, "icon")
            return (not icon or accessible_name(icon) == "", "icon contributes nothing")
        return (None, "unsupported expect form")
    if o == "state":
        states = [s for s in ("disabled",) if root["attrs"].get(f"aria-{s}") == "true"]
        want = exp.get("contains")
        return (want in states, f"states={states}")
    if o == "focus":
        f = "tabindex" in root["attrs"] or root["tag"] in ("button", "a", "input")
        if root["attrs"].get("aria-disabled") == "true": f = False
        return (f == exp.get("equals"), f"focusable={f}")
    if o == "order":
        got = [c["attrs"].get("data-zone") for c in root["children"] if c["attrs"].get("data-zone")]
        return (got == exp.get("order"), f"order={got}")
    return (None, "no observation implemented")

rows = []
def described(req):
    """The statement no longer restates its condition, so the report composes them."""
    scen = req.get("scenario") or {}
    if not scen:
        return req["statement"]
    bits = [f"{k}={v}" for group in scen.values() for k, v in group.items()]
    return f"[{', '.join(bits)}] {req['statement']}"

for req in DOC["requirements"]:
    rid, stmt = req["id"], described(req)
    if req.get("binds") is False:
        rows.append(("N/A", rid, stmt, req["reason"])); continue
    if "pending" in req:
        # The contract declares this property tokenised, but the token tree cannot express
        # it yet, so there is no expectation to compare against. `unverified`, never pass:
        # an unresolved token that reported green would defeat the point of declaring it.
        pend = req["pending"]
        # Where the fix belongs depends on why it is pending. Saying "token tree" for a
        # vocabulary gap would send someone to the wrong place.
        where = {"vocabulary-gap": "fix in the observe vocabulary"}.get(
            pend["reason"], "fix in the token tree")
        rows.append(("UNVER", rid, stmt, "pending (%s) — %s" % (pend["reason"], where))); continue
    missing = [n for n in req["needs"] if n in CAP["cannot_observe"]]
    if missing:
        rows.append(("UNVER", rid, stmt, CAP["cannot_observe"][missing[0]])); continue
    found = [w for w in WIT if matches(req["scenario"], w)]
    if not found:
        rows.append(("UNVER", rid, stmt,
                     f"no witness satisfies {json.dumps(req['scenario'])} — scenario coverage gap")); continue
    verdicts = []
    for w in found:
        ok, detail = observe(req, parse(w["html"]))
        verdicts.append((ok, f"{w['name']}: {detail}"))
    if any(ok is None for ok, _ in verdicts):
        rows.append(("UNVER", rid, stmt, "observation not implemented by this verifier"))
    elif all(ok for ok, _ in verdicts):
        rows.append(("PASS", rid, stmt, "; ".join(d for _, d in verdicts)))
    else:
        rows.append(("FAIL", rid, stmt, "; ".join(d for ok, d in verdicts if not ok)))

c = {k: sum(1 for r in rows if r[0] == k) for k in ("PASS", "FAIL", "UNVER", "N/A")}
print(f"\n{CAP['verifier']}  —  strategy: {'+'.join(CAP['strategy'])}")
print(f"{c['PASS']} pass / {c['FAIL']} fail / {c['UNVER']} unverified / {c['N/A']} n-a\n" + "="*76)
for status, rid, stmt, detail in rows:
    print(f"  {status:<6} {rid:<8} {stmt}")
    if status != "PASS":
        print(f"         {'':8} -> {detail}")
sys.exit(1 if c["FAIL"] else 0)
