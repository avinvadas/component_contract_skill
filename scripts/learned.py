#!/usr/bin/env python3
"""What this run taught the design system — made visible, so the accumulation can be reviewed.

    python3 scripts/learned.py snapshot [--context PATH]     # at the start of a run (Phase 0)
    python3 scripts/learned.py diff     [--context PATH]     # at the end of a run (Phase 6)

The design system's own layer grows component by component: facts in
`.claude/design-system-context.yml`, decisions in its policy, role-archetypes in its own
directory. Nothing in this skill writes those files silently — every addition comes from a
confirmed answer — but a confirmed answer buried mid-interview is still easy to miss. The diff
names each one, so a reviewer sees exactly what the next component will inherit.

The snapshot is tool state, written beside the context as `.claude/.context-snapshot.json`.
It is not the design system's content; it can be deleted, and belongs in `.gitignore`.
"""
import argparse, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import context as ctx  # noqa: E402
from resolve import parse_frontmatter, requirement_rows, policy_status  # noqa: E402

SNAPSHOT = ".context-snapshot.json"


def flatten(node, prefix=""):
    out = {}
    if isinstance(node, dict):
        for k, v in node.items():
            out.update(flatten(v, "%s.%s" % (prefix, k) if prefix else str(k)))
    elif isinstance(node, list):
        out[prefix] = json.dumps(node)
    elif node is not None:
        out[prefix] = str(node)
    return out


def state(context_path):
    """Everything the design system's own layer currently knows, flattened for comparison."""
    if context_path is None or not context_path.is_file():
        return {"facts": {}, "policy": {}, "archetypes": []}
    data = ctx.load(context_path) or {}
    root = ctx.repo_root(context_path)
    contracts = data.get("contracts") or {}

    policy = {}
    if contracts.get("policy") and (root / contracts["policy"]).is_file():
        for r in requirement_rows((root / contracts["policy"]).read_text()):
            policy[r["id"]] = {"decision": r.get("decision", ""), "status": policy_status(r),
                               "statement": (r.get("statement") or "").strip()}

    archetypes = []
    if contracts.get("archetypes") and (root / contracts["archetypes"]).is_dir():
        archetypes = sorted(f.stem for f in (root / contracts["archetypes"]).glob("*.md"))

    return {"facts": flatten(data), "policy": policy, "archetypes": archetypes}


def diff(before, after):
    changes = {"facts_added": [], "facts_changed": [], "facts_removed": [],
               "policy_decided": [], "policy_deferred": [], "policy_changed": [],
               "archetypes_added": []}
    bf, af = before["facts"], after["facts"]
    for k in sorted(af):
        if k not in bf:
            changes["facts_added"].append((k, af[k]))
        elif bf[k] != af[k]:
            changes["facts_changed"].append((k, bf[k], af[k]))
    changes["facts_removed"] = [(k, bf[k]) for k in sorted(bf) if k not in af]

    bp, ap = before["policy"], after["policy"]
    for rid in sorted(ap):
        now, was = ap[rid], bp.get(rid, {"status": "undecided", "statement": ""})
        if now["status"] == was["status"] and now["statement"] == was["statement"]:
            continue
        if now["status"] == "decided" and was["status"] != "decided":
            changes["policy_decided"].append((rid, now["decision"], now["statement"]))
        elif now["status"] == "deferred" and was["status"] != "deferred":
            changes["policy_deferred"].append((rid, now["decision"]))
        else:
            changes["policy_changed"].append((rid, now["decision"], was["statement"], now["statement"]))

    changes["archetypes_added"] = [a for a in after["archetypes"] if a not in before["archetypes"]]
    return changes


def report(changes):
    lines = []
    for k, v in changes["facts_added"]:
        lines.append("  + fact      %s = %s" % (k, v))
    for k, old, new in changes["facts_changed"]:
        lines.append("  ~ fact      %s: %s -> %s" % (k, old, new))
    for k, v in changes["facts_removed"]:
        lines.append("  - fact      %s (was %s)" % (k, v))
    for rid, decision, statement in changes["policy_decided"]:
        lines.append("  + policy    %s %s: %s" % (rid, decision, statement))
    for rid, decision in changes["policy_deferred"]:
        lines.append("  = policy    %s %s: deferred" % (rid, decision))
    for rid, decision, old, new in changes["policy_changed"]:
        lines.append("  ~ policy    %s %s: %r -> %r" % (rid, decision, old, new))
    for a in changes["archetypes_added"]:
        lines.append("  + archetype %s" % a)
    if not lines:
        return "This run taught the design system nothing new — every answer was already known."
    return ("This run taught the design system %d thing(s); every later component inherits them:\n"
            % len(lines)) + "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Snapshot, then report, what a run added.")
    ap.add_argument("command", choices=["snapshot", "diff"])
    ap.add_argument("--context", help="design-system context file (default: nearest .claude/)")
    ap.add_argument("--json", action="store_true", help="machine-readable diff")
    args = ap.parse_args()

    context_path = pathlib.Path(args.context).resolve() if args.context else ctx.find(pathlib.Path.cwd())
    # Before Phase 0B has written it, there is no context yet: the snapshot records nothing
    # known, so everything 0B confirms counts as learned — which it was.
    claude_dir = context_path.parent if context_path else pathlib.Path.cwd() / ".claude"
    snap = claude_dir / SNAPSHOT

    if args.command == "snapshot":
        claude_dir.mkdir(exist_ok=True)
        snap.write_text(json.dumps(state(context_path), indent=2) + "\n")
        print("snapshot written: %s" % snap)
        return

    if not snap.is_file():
        sys.exit("no snapshot at %s — run `learned.py snapshot` at the start of the run" % snap)
    context_path = context_path or ctx.find(pathlib.Path.cwd())
    changes = diff(json.loads(snap.read_text()), state(context_path))
    print(json.dumps(changes, indent=2) if args.json else report(changes))


if __name__ == "__main__":
    main()
