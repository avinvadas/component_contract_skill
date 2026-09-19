#!/usr/bin/env python3
"""State machines: one table in the source, many checkable requirements in the canonical.

The .md holds the machine AS a machine — every transition someone cares about, in one table
a reader takes in at a glance. The canonical holds its CONSEQUENCES, which is more than the
table says, because a state machine makes a claim no row states: *these are all the
transitions.* That claim is closure, and checking it means checking every (state, event) cell
nobody wrote. The resolver generates those. Nobody should have to.

    | from      | event   | to        | id        |
    | collapsed | open    | expanded  | id-CBX-T1 |
    | expanded  | dismiss | collapsed | id-CBX-T2 |
    | collapsed | commit  | n/a — no candidate is reachable while closed | — |

Grid = states x events. A cell is exactly one of:
    authored      a row states the transition           -> a positive requirement
    unreachable   `to` is `n/a — reason`                  -> no requirement; the event cannot
                                                             happen in that state
    closure       nothing was written                     -> a GENERATED requirement: the
                                                             event changes no state

Rules enforced here, each learned the hard way somewhere else in this project:

  - Ownership. A machine covers state its own component owns. A state named after a zone, or
    dotted into a child (`day.selected`), is a child's state leaking upward — and the moment a
    parent's grid includes its children's states, the grid is their product and closure
    inflates. The child's own contract checks the child.
  - Determinism. Two rows with the same (from, event) and different `to` are two machines.
  - No self-transitions. `expanded -> expanded` asserts no state change, which closure already
    implies; a row saying so is either redundant or hiding an effect that belongs in a
    requirement row conditioned `when:following:<transition-id>`.
  - Stable ids. A closure requirement's id is derived from its cell, never a counter, so a
    report can reference the same finding across runs.

Closure is computed on the RESOLVED machine — archetype rows plus contract rows. Computing it
per file would make an archetype-only closure check forbid a transition the contract adds.
"""
import re

MACHINE_HEADERS = {"from", "event", "to"}


def machine_rows(tables):
    """Rows from any table shaped like a transitions table."""
    out = []
    for headers, rows in tables:
        if MACHINE_HEADERS <= set(headers):
            out += rows
    return out


def closure_id(frm, event):
    return "closure~%s~%s" % (frm, event)


def build(rows, zones=()):
    """-> (machine, lint). `machine` is platform-neutral; bindings are applied per platform."""
    lint = []
    transitions, unreachable = [], []
    cells = {}
    for r in rows:
        frm, event, to = r["from"].strip(), r["event"].strip(), r["to"].strip()
        rid = (r.get("id") or "").strip()
        for st in (frm,) if to.lower().startswith("n/a") else (frm, to):
            if "." in st or st in zones:
                lint.append("machine: state %r belongs to a child, not this component — a "
                            "parent's grid that includes child state is their product" % st)
        if to.lower().startswith("n/a"):
            reason = to[3:].lstrip(" —-:").strip()
            if not reason:
                lint.append("machine: (%s, %s) marked unreachable with no reason" % (frm, event))
            unreachable.append({"from": frm, "event": event, "reason": reason})
            cells[(frm, event)] = "unreachable"
            continue
        if frm == to:
            lint.append("%s: self-transition %s -> %s asserts no state change, which closure "
                        "already implies; state its effect as a `when:following:%s` requirement"
                        % (rid, frm, to, rid))
        if not rid or rid in ("—", "-"):
            lint.append("machine: transition (%s, %s) has no id" % (frm, event))
        prev = cells.get((frm, event))
        if isinstance(prev, dict) and prev["to"] != to:
            lint.append("machine: (%s, %s) goes to both %r and %r — not one machine"
                        % (frm, event, prev["to"], to))
        t = {"id": rid, "from": frm, "event": event, "to": to,
             "guard": (r.get("guard") or "—").strip(), "source": r.get("source", "")}
        transitions.append(t)
        cells[(frm, event)] = t

    states = sorted({t["from"] for t in transitions} | {t["to"] for t in transitions}
                    | {u["from"] for u in unreachable})
    events = sorted({t["event"] for t in transitions} | {u["event"] for u in unreachable})
    closure = [{"id": closure_id(s, e), "from": s, "event": e}
               for s in states for e in events if (s, e) not in cells]
    return {"states": states, "events": events, "transitions": transitions,
            "unreachable": unreachable, "closure": closure}, lint


def merge_bindings(layers):
    """`machine` blocks from each bindings layer, later layers overriding earlier ones."""
    out = {"states": {}, "events": {}}
    for layer in layers:
        m = layer.get("machine", {})
        for kind in ("states", "events"):
            for name, per_platform in m.get(kind, {}).items():
                out[kind].setdefault(name, {}).update(per_platform)
    return out


def requirements(machine, mb, platform, lint):
    """Positive + closure requirements for one platform, and the per-platform machine block."""
    def state_expect(name):
        e = mb["states"].get(name, {}).get(platform)
        if e is None:
            lint.append("machine: state %r has no observation binding for %s" % (name, platform))
        return e

    def trigger(name):
        t = mb["events"].get(name, {}).get(platform)
        if t is None:
            lint.append("machine: event %r has no trigger binding for %s" % (name, platform))
        return t

    needs = ["interaction", "a11y-tree"]
    reqs = []
    for t in machine["transitions"]:
        moves = "From %s, %s moves to %s." % (t["from"], t["event"], t["to"])
        reqs.append({"id": t["id"], "statement": moves,
                     "observe": "state", "kind": "behavior",
                     "scenario": {"machine": {"state": t["from"]}},
                     "trigger": trigger(t["event"]), "expect": state_expect(t["to"]),
                     "needs": needs})
    for c in machine["closure"]:
        reqs.append({"id": c["id"],
                     "statement": "From %s, %s changes no state." % (c["from"], c["event"]),
                     "observe": "state", "kind": "behavior",
                     "scenario": {"machine": {"state": c["from"]}},
                     "trigger": trigger(c["event"]), "expect": state_expect(c["from"]),
                     "needs": needs, "derived": "closure"})

    block = {"states": {s: state_expect(s) for s in machine["states"]},
             "transitions": [{"id": t["id"], "from": t["from"], "to": t["to"],
                              "trigger": trigger(t["event"])} for t in machine["transitions"]],
             "unreachable": machine["unreachable"]}
    return reqs, block
