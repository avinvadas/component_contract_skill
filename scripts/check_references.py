#!/usr/bin/env python3
"""Which reference files are due to be re-checked against the standard they cite.

    python3 scripts/check_references.py [--days 90] [--json]

Every file under `references/` condenses one external standard and carries the date it was
last checked against it. That date is the ONLY signal this project has that a standard may
have moved: references feed the skill's REASONING while a contract is written, never the
resolver, so what a standard implied is frozen into the contract's text the moment it is
written. Re-running the resolver reproduces that text byte for byte no matter what the
standard now says — a stale reference is invisible to every other check here.

So this runs on a clock, not on a contract. It reads dates and nothing else: no network, no
judgement, no edit. Deciding whether a standard MATERIALLY changed is a reading task for a
person, and rewriting a curated explanation from an automated diff is exactly what this
project refuses to do. All this answers is *which files someone should go and look at*.

Exit code 1 when anything is due, so a scheduled job or a CI step can act on it.
"""
import argparse, datetime, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REFS = ROOT / "references"
DATE = re.compile(r"^\*\*Last verified:\*\*\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)
# "Sources of authority:" (plural) is as common as the singular, and reading only one of them
# silently reported half the platform files as citing nothing.
SOURCE = re.compile(r"^Sources? of authority:\s*(.+)$", re.M)
URL = re.compile(r"https?://[^\s)\]]+")


def read(path):
    """One reference file's date, and how it would be checked.

    Three ways, and they are not the same job: a cited URL is fetched and compared; a source
    named in prose (an API, a vendor's docs set) is read by a person; and a file citing no
    external source at all aggregates the others, so checking it means confirming it still
    agrees with whichever of them were due — never fetching anything.
    """
    text = path.read_text()
    m = DATE.search(text)
    s = SOURCE.search(text)
    urls = URL.findall(s.group(1)) if s else []
    try:
        name = str(path.relative_to(ROOT))
    except ValueError:      # a file outside the skill — reported by the path given
        name = str(path)
    return {"file": name,
            "verified": m.group(1) if m else None,
            "sources": urls,
            "how": "fetch" if urls else "read" if s else "agrees-with-others"}


def survey(days, today=None):
    today = today or datetime.date.today()
    due, fresh, broken = [], [], []
    for path in sorted(REFS.rglob("*.md")):
        r = read(path)
        if r["verified"] is None:
            # A file with no date can never come due, so it would go unchecked forever.
            # That is a defect in the file, reported as one — never a silent pass.
            broken.append(dict(r, problem="no `Last verified:` line"))
            continue
        age = (today - datetime.date.fromisoformat(r["verified"])).days
        (due if age >= days else fresh).append(dict(r, age=age))
    due.sort(key=lambda r: -r["age"])
    fresh.sort(key=lambda r: -r["age"])
    return due, fresh, broken


def notice(days=90):
    """One line to stderr when a reference is overdue. Silent otherwise. Never raises.

    Phase 0A tells the skill to check at every start, but an instruction is not a mechanism:
    a run that skipped it would produce an identical contract and nothing would say so. So
    every script that runs early in a run calls this, and the check happens whether or not
    anyone remembered to ask for it.

    stderr, so nothing that parses a script's stdout is affected. Silent on any failure — a
    freshness notice must never be the reason a contract cannot be resolved, which is the
    same rule Phase 0A states for itself.
    """
    try:
        due, _, broken = survey(days)
        if not due and not broken:
            return
        names = [pathlib.Path(r["file"]).stem for r in due + broken]
        shown = ", ".join(names[:3]) + (", +%d" % (len(names) - 3) if len(names) > 3 else "")
        print("note: %d reference file(s) due to be re-checked (%s).\n"
              "      Run scripts/check_references.py. A stale reference is invisible to every\n"
              "      other check here — the date is the only signal there is.\n"
              % (len(names), shown), file=sys.stderr)
    except Exception:                                      # noqa: BLE001
        return


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", type=int, default=90,
                    help="age at which a file is due (default: 90)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    due, fresh, broken = survey(args.days)
    if args.json:
        print(json.dumps({"due": due, "fresh": fresh, "unreadable": broken,
                          "threshold_days": args.days}, indent=2))
        return 1 if due or broken else 0

    if broken:
        print("cannot be checked (%d):" % len(broken))
        for r in broken:
            print("  - %s — %s" % (r["file"], r["problem"]))
        print()
    if due:
        how = {"fetch": "fetch and compare", "read": "read the source it names",
               "agrees-with-others": "confirm it still agrees with the others"}
        print("due for re-checking (%d), oldest first:" % len(due))
        for r in due:
            print("  - %-52s %3d days  %s" % (r["file"], r["age"], how[r["how"]]))
            if r["sources"]:
                print("      %s" % r["sources"][0])
        print("\nCheck each against the source it cites. If the standard has materially changed,"
              "\nsay so and ask before editing — a reference is a curated explanation, not a"
              "\nscrape, and an unreviewed rewrite is the thing this check exists to avoid.")
    else:
        print("nothing due — %d reference file(s), none older than %d days"
              % (len(fresh), args.days))
    if fresh and due:
        print("\n%d other file(s) not yet due; the next is %d days old."
              % (len(fresh), fresh[0]["age"] if fresh else 0))
    return 1 if due or broken else 0


if __name__ == "__main__":
    sys.exit(main())
