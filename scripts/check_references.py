#!/usr/bin/env python3
"""Which reference files are due to be re-checked against the standard they cite.

    python3 scripts/check_references.py [--days 90] [--online] [--json]

Every file under `references/` condenses one external standard and carries the date it was
last checked against it. That date is the ONLY signal this project has that a standard may
have moved: references feed the skill's REASONING while a contract is written, never the
resolver, so what a standard implied is frozen into the contract's text the moment it is
written. Re-running the resolver reproduces that text byte for byte no matter what the
standard now says — a stale reference is invisible to every other check here.

So this runs on a clock, not on a contract. By default it reads dates and nothing else: no
network, no judgement, no edit — which is what lets it run at the start of every single run.

`--online` asks every source a file cites when IT last changed and compares that against `Last verified:`,
which is a better question than age: a file whose spec has not moved in two years stops
nagging, and one whose spec moved last week is due whatever its age. Where a source publishes
no usable date — Apple's and Google's developer docs, which are rendered per request — it
falls back to age and NAMES the files that fell back, because a weaker check said out loud is
the same discipline a verifier follows when it cannot observe something.

Either way, deciding whether a standard MATERIALLY changed is a reading task for a person, and
rewriting a curated explanation from an automated diff is exactly what this project refuses to
do. All this answers is *which files someone should go and look at*.

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
# A file may set its own re-check window. The rule it encodes: the less a source tells us about
# itself, the more often a person has to look. Apple's and Google's developer docs publish no
# usable date, render their guidance in JavaScript so there is nothing to hash, and ship HIG
# changes with an OS release — so nothing automated can say whether they moved, and the only
# safe answer is to review them oftener. A source that dates itself needs no such help.
RECHECK = re.compile(r"^\*\*Recheck:\*\*\s*(\d+)\s*days?\b", re.M)


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
    rc = RECHECK.search(text)
    return {"file": name,
            "verified": m.group(1) if m else None,
            "sources": urls,
            "recheck": int(rc.group(1)) if rc else None,
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
        window = r["recheck"] or days
        (due if age >= window else fresh).append(dict(r, age=age, window=window))
    due.sort(key=lambda r: -r["age"])
    fresh.sort(key=lambda r: -r["age"])
    return due, fresh, broken


# `Last-Modified` is named, because it is believed in one direction only. See `survey_online`.
HEADER = "Last-Modified header"

MONTHS = {m: i for i, m in enumerate(
    "january february march april may june july august september october november december"
    .split(), 1)}
# A source announces its own change in one of a few shapes. Each yields a DATE, which is all
# that is wanted: compared against `Last verified:`, it answers "has this moved since we looked"
# without storing an ETag or any other state beside the file.
DATE_SHAPES = (
    # W3C: <time class="dt-published" datetime="2023-10-05">, and the TR header line
    (re.compile(r'datetime="(\d{4})-(\d{2})-(\d{2})"'), "w3c <time>"),
    (re.compile(r"W3C (?:Recommendation|Proposed Recommendation|Candidate Recommendation|"
                r"Working Draft|Note|Editor's Draft)[,\s]+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})"),
     "w3c header"),
    # WHATWG living standards: "Living Standard — Last Updated 21 September 2026"
    (re.compile(r"Last Updated\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})"), "whatwg header"),
    # MediaWiki, which freedesktop's wiki runs
    (re.compile(r"last edited on\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})"), "wiki footer"),
)


def extract_date(body, headers=None, today=None):
    """A source's own publication date, as (date, how) — or (None, None). Pure; no I/O.

    The document's OWN date is tried first and the `Last-Modified` header last, which is the
    opposite of the obvious order and is the whole lesson here: a dynamically rendered page
    sends the render time. Apple's accessibility landing page reports `Last-Modified` = now,
    so trusting the header would have marked it changed on every run, for ever — a check that
    always fires is a check nobody reads.

    A header dated today is therefore not believed at all. Real content almost never changes
    in the second you fetch it; a render timestamp always does.
    """
    today = today or datetime.date.today()
    for rx, how in DATE_SHAPES:
        m = rx.search(body or "")
        if not m:
            continue
        a, b, c = m.groups()
        try:
            if a.isdigit() and len(a) == 4:                # ISO: yyyy, mm, dd
                return datetime.date(int(a), int(b), int(c)), how
            month = MONTHS.get(b.lower())                  # d Month yyyy
            if month:
                return datetime.date(int(c), month, int(a)), how
        except ValueError:                                 # a date that does not exist
            continue
    lm = (headers or {}).get("Last-Modified")
    if lm:
        try:
            import email.utils
            when = email.utils.parsedate_to_datetime(lm).date()
            if when < today:
                return when, HEADER
        except Exception:                                  # noqa: BLE001 — a malformed header
            pass
    return None, None


import urllib.request                                      # noqa: E402 — used by _Follow308 below


class _Follow308(urllib.request.HTTPRedirectHandler):
    """urllib follows 301, 302, 303 and 307 — but not 308.

    A standards body that reorganises its site permanently (JSON Schema dropped the `.html`
    suffix) therefore came back `unreachable`, which reads exactly like a dead link and
    silently drops the file to age alone. A moved source is the ordinary case, not a failure.

    Both halves are needed: a handler METHOD for the status, because the dispatch chain is
    built from method names, and `redirect_request`, which refuses outright any code outside
    301/302/303/307 and so raised the error before the method could run.
    """
    http_error_308 = urllib.request.HTTPRedirectHandler.http_error_301

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, 301 if code == 308 else code,
                                        msg, headers, newurl)


def source_date(url, timeout=10):
    """Fetch `url` and read the date it publishes for itself. Never raises."""
    import urllib.request
    req = urllib.request.Request(url, headers={
        "User-Agent": "component-contract-skill reference freshness check"})
    try:
        with urllib.request.build_opener(_Follow308).open(req, timeout=timeout) as r:
            # Only the head of the document: every shape above appears near the top, and a
            # living standard is megabytes.
            body = r.read(200_000).decode("utf-8", "replace")
            return extract_date(body, dict(r.headers))
    except Exception as e:                                 # noqa: BLE001 — offline, 403, timeout
        # The status matters to whoever has to act: 404 means find the new home, 403 means the
        # check cannot read it and a person must, 308 meant this handler was missing.
        code = getattr(e, "code", None)
        return None, "unreachable (%s)" % (("HTTP %s" % code) if code else type(e).__name__)


def read_sources(r):
    """Ask EVERY source a file cites when it last changed, as (moved, dated, undated).

    Every one, not just the first. `native-events-models.md` cites nine sources across five
    platforms, and reading only the head of the list meant its whole freshness verdict came
    from whichever happened to be listed first — with the other eight never asked. Six of the
    shipped files cite more than one source, so this was never about a single file.

    `moved` is the sources that published a date after we verified; `dated` those that
    answered and had not moved; `undated` those that said nothing usable, each with why.
    """
    verified = datetime.date.fromisoformat(r["verified"])
    moved, dated, undated = [], [], []
    for url in r["sources"]:
        when, how = source_date(url)
        if when is None:
            undated.append({"url": url, "why": how or "no date published"})
        elif how == HEADER and when > verified:
            # The header can CLEAR a source and never accuse one. On a page rendered per
            # request it is a render or cache timestamp, not a publication date, and the two
            # are indistinguishable from one fetch. Rejecting only a header dated today was
            # not enough: Apple's returned yesterday, which sailed through and reported three
            # files as changed — a finding that would recur on every run for ever, which is
            # the check nobody reads. Dated BEFORE our own check it still proves something
            # real (nothing re-renders to a 2023 date), so that direction is kept.
            undated.append({"url": url, "why": "no publication date; header says %s but a "
                                               "header newer than our own check proves "
                                               "nothing" % when})
        else:
            (moved if when > verified else dated).append(
                {"url": url, "date": when, "how": how})
    return moved, dated, undated


def survey_online(days, today=None):
    """Age, refined by what each source says about itself.

    Three outcomes per file, and the middle one is the one worth being strict about:

        any source moved     due, whatever its age — the useful finding
        all sources answered and none moved     cleared, whatever its age
        some source could not be dated          nothing is cleared; age decides, and the
                                               fallback is NAMED

    A file is only cleared when every source it cites answered. One undatable source among
    five means the file could have moved without anything here knowing, so claiming it is
    unchanged would be asserting more than was observed — the same rule a verifier follows
    when it cannot observe something, applied to this check's own evidence.
    """
    today = today or datetime.date.today()
    due, fresh, broken = survey(days, today)
    undatable = []
    for r in list(fresh) + list(due):
        if not r["sources"]:
            continue
        moved, dated, undated = read_sources(r)
        n = len(r["sources"])
        if moved:
            # Said whichever list it was already in: "old by the clock" and "the source
            # actually moved" are different reasons to look, and the second is the useful one.
            newest = max(moved, key=lambda m: m["date"])
            r["source_date"], r["source_how"] = newest["date"].isoformat(), newest["how"]
            r["source"] = "source changed %s, ours verified %s%s" % (
                newest["date"], r["verified"],
                "" if n == 1 else " (%d of %d cited sources moved)" % (len(moved), n))
            if r in fresh:
                fresh.remove(r)
                due.append(r)
            continue
        if undated:
            r["source"] = undated[0]["why"] if n == 1 else \
                "%d of %d cited sources publish no date, so this cannot be cleared: %s" % (
                    len(undated), n, ", ".join(u["url"] for u in undated[:2])
                    + (", +%d" % (len(undated) - 2) if len(undated) > 2 else ""))
            undatable.append(r)
            continue
        newest = max(dated, key=lambda m: m["date"])
        r["source_date"], r["source_how"] = newest["date"].isoformat(), newest["how"]
        r["source"] = "source unchanged since %s" % newest["date"] if n == 1 else \
            "all %d cited sources unchanged, newest %s" % (n, newest["date"])
        if r in due:                                       # old by the clock, but not moved
            due.remove(r)
            fresh.append(r)
    due.sort(key=lambda r: -r["age"])
    return due, fresh, broken, undatable


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
    ap.add_argument("--online", action="store_true",
                    help="ask each source when it last changed, instead of judging by age "
                         "alone. Needs network; falls back to age where a source publishes "
                         "no date, and says which")
    args = ap.parse_args()

    undatable = []
    if args.online:
        due, fresh, broken, undatable = survey_online(args.days)
    else:
        due, fresh, broken = survey(args.days)
    if args.json:
        print(json.dumps({"due": due, "fresh": fresh, "unreadable": broken,
                          "undatable": [r["file"] for r in undatable],
                          "online": args.online, "threshold_days": args.days}, indent=2))
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
            print("  - %-52s %3d/%-3d days  %s"
                  % (r["file"], r["age"], r["window"],
                     r.get("source") or how[r["how"]]))
            # Every URL, not just the first: the person has to check each of them, and printing
            # one made a nine-source file look like a one-source file.
            for url in r["sources"][:4]:
                print("      %s" % url)
            if len(r["sources"]) > 4:
                print("      +%d more cited in the file" % (len(r["sources"]) - 4))
        print("\nCheck each against every source it cites. If the standard has materially changed,"
              "\nsay so and ask before editing — a reference is a curated explanation, not a"
              "\nscrape, and an unreviewed rewrite is the thing this check exists to avoid.")
    else:
        short = sorted({r["window"] for r in fresh if r["window"] != args.days})
        print("nothing due — %d reference file(s)%s"
              % (len(fresh),
                 ", on windows of %s days" % "/".join(str(w) for w in short + [args.days])
                 if short else ", none older than %d days" % args.days))
    if undatable:
        print("\n%d source(s) publish no date, so these fell back to age alone:" % len(undatable))
        for r in undatable:
            print("  - %-52s %s" % (r["file"], r["source"]))
    if fresh and due:
        print("\n%d other file(s) not yet due; the next is %d days old."
              % (len(fresh), fresh[0]["age"] if fresh else 0))
    return 1 if due or broken else 0


if __name__ == "__main__":
    sys.exit(main())
