#!/usr/bin/env python3
"""Which contracts' generated files no longer match what their inputs produce.

    python3 scripts/check_generated.py [--contracts DIR] [--exclude NAME] [--json] [--fix]

A spec is a pure function of six inputs — the contract, its bindings, the role-archetype, the
policy, the token tree and the design system's facts — and only two of those live beside it.
The other four are SHARED, so a change to one can move a contract nobody touched: decide a
policy row while contracting Modal and every contract that ENGAGES that row is now stale, with
nothing in its own directory to say so.

Generation is deterministic, which is what makes this answerable: regenerate, compare bytes.
Five outcomes, and only one of them means nothing is wrong:

    ok             identical
    stale          committed, and different
    missing        produced now, absent from generated/
    orphan         in generated/, and nothing produces it any more — a platform dropped from
                   the contract, whose document a consumer may still be reading
    unresolvable   the contract lint-fails, so there is nothing to compare. Never "ok"

Nothing is rewritten without `--fix`, and `--fix` never deletes: an orphan is reported for a
person to remove, because deciding a file is genuinely dead is not a thing to infer.
"""
import argparse, difflib, json, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent


def find_context(start):
    """The nearest `.claude/design-system-context.yml`, walking up — as resolve.py does."""
    d = start.resolve()
    for cand in [d, *d.parents]:
        f = cand / ".claude/design-system-context.yml"
        if f.is_file():
            return f
    return None


def contracts_root(context_file, override):
    if override:
        return pathlib.Path(override).resolve()
    if context_file:
        # Read only `contracts.path`; a full YAML parse is resolve.py's job, not this one's.
        text = context_file.read_text()
        inside, path = False, None
        for line in text.splitlines():
            if line.startswith("contracts:"):
                inside = True
            elif inside and line[:1] not in (" ", "\t"):
                inside = False
            elif inside and "path:" in line:
                path = line.split("path:", 1)[1].strip().strip("'\"")
        if path:
            return (context_file.parent.parent / path).resolve()
    return pathlib.Path.cwd().resolve()


def contracts_under(root):
    """`<Name>/<Name>.md` — the layout SKILL.md's Output section defines."""
    return sorted(d / (d.name + ".md") for d in root.iterdir()
                  if d.is_dir() and (d / (d.name + ".md")).is_file()) if root.is_dir() else []


def summarise(old, new, name):
    """What moved — requirement ids for a document, changed lines for the spec."""
    if name.endswith(".json"):
        try:
            a = {r["id"] for r in json.loads(old)["requirements"] if "id" in r}
            b = {r["id"] for r in json.loads(new)["requirements"] if "id" in r}
        except Exception:                                  # noqa: BLE001 — shape changed
            return "content differs"
        gained, lost = sorted(b - a), sorted(a - b)
        if not gained and not lost:
            return "same requirements, changed content"
        bits = []
        if gained:
            bits.append("+%d (%s)" % (len(gained), ", ".join(gained[:3])
                                      + ("…" if len(gained) > 3 else "")))
        if lost:
            bits.append("-%d (%s)" % (len(lost), ", ".join(lost[:3])
                                      + ("…" if len(lost) > 3 else "")))
        return " ".join(bits) + " requirement(s)"
    plus = minus = 0
    for line in difflib.ndiff(old.splitlines(), new.splitlines()):
        plus += line.startswith("+ ")
        minus += line.startswith("- ")
    return "+%d / -%d lines" % (plus, minus)


def check_one(contract, fix=False):
    """Regenerate one contract into a temp directory and compare against what is committed."""
    out = {"contract": contract.parent.name, "path": str(contract), "findings": []}
    committed = contract.parent / "generated"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        r = subprocess.run([sys.executable, str(HERE / "resolve.py"), str(contract),
                            "--out", str(tmp)], capture_output=True, text=True)
        if r.returncode != 0:
            # A contract that does not resolve has nothing to compare. Saying "ok" here would
            # be the one failure mode this whole check exists to rule out.
            out["findings"].append({"kind": "unresolvable", "file": contract.name,
                                    "detail": (r.stdout + r.stderr).strip().splitlines()[-1:]
                                    or ["resolve.py exited %d" % r.returncode]})
            return out
        v = subprocess.run([sys.executable, str(HERE / "resolve_view.py"), str(contract),
                            "--out", str(tmp / (contract.stem + ".spec.md"))],
                           capture_output=True, text=True)
        if v.returncode != 0:
            out["findings"].append({"kind": "unresolvable", "file": contract.stem + ".spec.md",
                                    "detail": [v.stderr.strip().splitlines()[-1:][0]
                                               if v.stderr.strip() else "resolve_view failed"]})
            return out

        # The props schema is optional — only a contract that asked for one has any. Its
        # PRESENCE is the signal, since nothing else records that Q10 said yes.
        if committed.is_dir() and any(p.name.endswith(".schema.json")
                                      for p in committed.iterdir() if p.is_file()):
            s = subprocess.run([sys.executable, str(HERE / "schema.py"), str(contract),
                                "--out", str(tmp)], capture_output=True, text=True)
            if s.returncode != 0:
                out["findings"].append({"kind": "unresolvable", "file": "schema",
                                        "detail": (s.stdout + s.stderr).strip().splitlines()[-1:]
                                        or ["schema.py exited %d" % s.returncode]})
                return out

        produced = {p.name: p.read_text() for p in sorted(tmp.iterdir()) if p.is_file()}
        for name, text in produced.items():
            here = committed / name
            if not here.is_file():
                out["findings"].append({"kind": "missing", "file": name})
            elif here.read_text() != text:
                out["findings"].append({"kind": "stale", "file": name,
                                        "detail": summarise(here.read_text(), text, name)})
        if committed.is_dir():
            for p in sorted(committed.iterdir()):
                if not p.is_file() or p.name in produced:
                    continue
                out["findings"].append({"kind": "orphan", "file": p.name})
        if fix:
            committed.mkdir(parents=True, exist_ok=True)
            for name, text in produced.items():
                (committed / name).write_text(text)
            out["fixed"] = [f["file"] for f in out["findings"]
                            if f["kind"] in ("stale", "missing")]
    return out


ACTIONABLE = ("stale", "missing", "orphan", "unresolvable")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--contracts", help="directory holding <Name>/<Name>.md "
                                        "(default: contracts.path from the design-system context)")
    ap.add_argument("--context", help="design-system context file (default: nearest .claude/)")
    ap.add_argument("--exclude", action="append", default=[],
                    help="contract name to skip — the one being worked on, so the report names "
                         "only the OTHERS a shared change moved. Repeatable")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--fix", action="store_true",
                    help="rewrite stale and missing files. Never deletes an orphan")
    args = ap.parse_args()

    ctx = pathlib.Path(args.context).resolve() if args.context else find_context(pathlib.Path.cwd())
    root = contracts_root(ctx, args.contracts)
    found = [c for c in contracts_under(root) if c.parent.name not in args.exclude]
    reports = [check_one(c, args.fix) for c in found]
    moved = [r for r in reports
             if any(f["kind"] in ACTIONABLE for f in r["findings"])]
    # A contract that will not resolve is not "out of date" — it is unreadable, and `--fix`
    # cannot touch it. Counting the two together would send someone to the wrong fix, and
    # would let `--fix` exit 0 over a contract it never managed to read.
    blocked = [r for r in moved if any(f["kind"] == "unresolvable" for f in r["findings"])]
    outdated = [r for r in moved if r not in blocked]
    bad = bool(blocked) or bool(outdated and not args.fix)

    if args.json:
        print(json.dumps({"contracts_root": str(root), "checked": len(reports),
                          "excluded": args.exclude, "reports": reports}, indent=2))
        return 1 if bad else 0

    if not found:
        print("no contracts found under %s" % root)
        return 0
    label = {"stale": "stale", "missing": "missing", "orphan": "orphan",
             "unresolvable": "CANNOT CHECK"}
    for r in reports:
        actionable = [f for f in r["findings"] if f["kind"] in ACTIONABLE]
        if not actionable:
            continue
        print("%s" % r["contract"])
        for f in actionable:
            detail = f.get("detail")
            print("  %-13s %-28s %s" % (label[f["kind"]], f["file"],
                                        detail if isinstance(detail, str) else
                                        " ".join(detail or [])))
    if outdated:
        print("\n%d of %d contract(s) out of date." % (len(outdated), len(reports)),
              "Fixed." if args.fix else "Nothing was changed.")
        if not args.fix:
            print("Read the diff before updating — it names what the shared change did.")
    if blocked:
        print("\n%d contract(s) could not be checked: they do not resolve. Fix the lint first "
              "— an\nunreadable contract is a different problem from a stale one."
              % len(blocked))
    if not moved:
        print("%d contract(s) checked, all up to date." % len(reports))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
