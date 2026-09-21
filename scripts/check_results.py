#!/usr/bin/env python3
"""Does a verifier's results file say what a compliance claim has to say?

    python3 scripts/check_results.py results.json [--document Button.web.json] [--json]

`docs/verifier-results-format.md` specifies what a verifier writes back, so that compliance is
a fact about a VERSION rather than a fact about a moment. A verifier is somebody else's
toolchain; this project cannot run it, cannot review it, and should not try to. What it can do
is say, of a file that arrives, whether it is a claim at all.

Two levels, which are the lint/gap distinction the rest of the project uses:

    error   the file is malformed against the format — a required field absent, a digest that
            is not a digest, counts that disagree with the rows they count. Exit 1.
    note    the file is well-formed but says less than it could — a subject with no version,
            a verifier that claims to see everything. Exit 0.

It never judges whether the implementation is compliant. It reads no contract, no document and
no token tree; `--document` is the single exception, and only to confirm the digest is of the
file it names. What a verifier OBSERVED is the verifier's business. Whether what it wrote can
be believed six months from now is this.
"""
import argparse, datetime, hashlib, json, pathlib, re, sys

READS = "1"                       # the format major this checker understands
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
STRATEGIES = {"witness", "construct"}
# `UNVER`, not `UNVERIFIED`: every verifier writes the short spelling and `evidence.py` matches
# it literally, so the long one is not a synonym — it is rows silently dropped.
STATUSES = ("PASS", "FAIL", "UNVER", "N/A")
COUNTS = {"PASS": "pass", "FAIL": "fail", "UNVER": "unverified", "N/A": "n_a"}
LEGACY_STATUS = {"UNVERIFIED": "UNVER", "NA": "N/A", "N-A": "N/A"}


def digest(path):
    """`sha256:…` over a document's bytes, exactly as a verifier reports it."""
    return "sha256:" + hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def unreadable_format(res):
    """The format major this file declares, if this checker cannot read it — else None.

    This is the whole point of `format_version`: a consumer that meets a file from a later
    format should say so and stop, rather than read the fields it recognises and quietly
    ignore a field that changed what they mean. A file declaring nothing predates the format
    and is not refused here; that is a migration, and the digest check handles it.
    """
    fv = res.get("format_version")
    if isinstance(fv, str) and fv.split(".")[0] != READS:
        return fv
    return None


def _obj(findings, res, field, required_keys, level="error"):
    v = res.get(field)
    if not isinstance(v, dict):
        findings.append((level, field, "must be an object; found %s" % _kind(v)))
        return {}
    for k in required_keys:
        if k not in v:
            findings.append((level, "%s.%s" % (field, k), "absent"))
    return v


def _kind(v):
    return "nothing" if v is None else type(v).__name__


def check(res, doc_digest=None):
    """Every finding about one results file, as (level, field, what). Pure; no I/O.

    Ordered as a reader would want them: what makes the file unreadable first, then what is
    absent, then what disagrees with itself, then what it could have said and did not.
    """
    findings = []
    if not isinstance(res, dict):
        return [("error", "", "a results file is a JSON object; found %s" % _kind(res))]

    later = unreadable_format(res)
    if later:
        return [("error", "format_version",
                 "written to format %s; this checker reads %s.x. Refusing to read fields whose "
                 "meaning may have changed." % (later, READS))]
    if "format_version" not in res:
        findings.append(("error", "format_version",
                         "absent. Without it a consumer cannot tell what it is reading"))

    for field in ("contract", "platform", "contract_version", "generated_from"):
        if not isinstance(res.get(field), str) or not res.get(field):
            findings.append(("error", field, "absent or not a string"))

    # The document. `contract_version` is for people and is not enough on its own: a contract
    # does not pin its archetype version, so two documents can both say 1.0 and hold different
    # requirements. The digest is what answers "was it THIS document" later.
    dg = res.get("document_digest")
    if not isinstance(dg, str):
        findings.append(("error", "document_digest", "absent"))
    elif not DIGEST.match(dg):
        findings.append(("error", "document_digest",
                         "not a sha256 of 64 hex digits: %r" % (dg[:80],)))
    elif doc_digest and dg != doc_digest:
        findings.append(("error", "document_digest",
                         "these results were observed against a different document\n"
                         "        results:  %s\n        document: %s" % (dg, doc_digest)))

    # The subject. A verifier cannot discover what it is driving, so this is the one field its
    # runner has to be told — and the one most likely to be left out for that reason.
    subj = _obj(findings, res, "subject", ("name",))
    if subj and not subj.get("version") and not subj.get("ref"):
        findings.append(("note", "subject",
                         "names no version and no ref, so this claim is about an unidentified "
                         "build. It cannot be matched to a release later"))

    # The verifier. A result from a weak verifier and a strong one are not the same claim, and
    # these two maps are what make the difference legible to anyone reading the file cold.
    v = _obj(findings, res, "verifier", ("name", "version", "strategies",
                                         "cannot_observe", "cannot_establish"))
    st = v.get("strategies")
    if st is not None:
        if not isinstance(st, list) or not st:
            findings.append(("error", "verifier.strategies", "must be a non-empty list"))
        elif set(st) - STRATEGIES:
            findings.append(("error", "verifier.strategies",
                             "unknown: %s (known: %s)"
                             % (", ".join(sorted(set(st) - STRATEGIES)),
                                ", ".join(sorted(STRATEGIES)))))
    for k in ("cannot_observe", "cannot_establish"):
        m = v.get(k)
        if k in v and not isinstance(m, dict):
            findings.append(("error", "verifier.%s" % k,
                             "must be an object of name to reason; found %s" % _kind(m)))
        elif isinstance(m, dict) and not m:
            findings.append(("note", "verifier.%s" % k,
                             "empty, which claims there is nothing it cannot %s. True for no "
                             "verifier this project has seen"
                             % ("observe" if k == "cannot_observe" else "establish")))

    when = res.get("produced_at")
    if not isinstance(when, str):
        findings.append(("error", "produced_at", "absent"))
    else:
        try:
            datetime.datetime.fromisoformat(when.replace("Z", "+00:00"))
        except ValueError:
            findings.append(("error", "produced_at", "not ISO 8601: %r" % (when[:40],)))

    findings += check_results_rows(res)
    return findings


def check_results_rows(res):
    """The rows, and whether the summary counts the rows that are actually there.

    The summary is the sentence anybody quotes — "236 checked, 0 failed, 2 unverified" — and
    it is derived, so it can drift from the rows beneath it without anyone noticing. Recounting
    is cheap and it is the only field here that can be checked against the file's own contents.
    """
    findings = []
    rows = res.get("results")
    if not isinstance(rows, list):
        return findings + [("error", "results", "absent or not a list")]
    if not rows:
        findings.append(("error", "results", "empty. A file that checked nothing is not a claim"))

    seen, counts = set(), {k: 0 for k in COUNTS}
    for i, r in enumerate(rows):
        at = "results[%d]" % i
        if not isinstance(r, dict):
            findings.append(("error", at, "must be an object; found %s" % _kind(r)))
            continue
        rid = r.get("id")
        if not isinstance(rid, str) or not rid:
            findings.append(("error", at + ".id", "absent"))
        elif rid in seen:
            findings.append(("error", at + ".id",
                             "%s appears more than once; a requirement has one verdict" % rid))
        else:
            seen.add(rid)
        if not isinstance(r.get("statement"), str) or not r.get("statement"):
            findings.append(("error", "%s.statement" % (rid or at),
                             "absent. A verdict nobody can read is not reportable"))
        s = r.get("status")
        if s in COUNTS:
            counts[s] += 1
        elif s in LEGACY_STATUS:
            findings.append(("error", "%s.status" % (rid or at),
                             "%r is an older spelling of %r. `evidence.py` matches the status "
                             "string literally, so these rows would be read as nothing at all"
                             % (s, LEGACY_STATUS[s])))
        else:
            findings.append(("error", "%s.status" % (rid or at),
                             "%r is not one of %s" % (s, ", ".join(STATUSES))))

    summary = res.get("summary")
    if not isinstance(summary, dict):
        findings.append(("error", "summary", "absent or not an object"))
        return findings
    for status, key in COUNTS.items():
        if key not in summary:
            findings.append(("error", "summary.%s" % key, "absent. All four counts, always: a "
                             "summary that omits `unverified` reads as a clean run"))
        elif summary[key] != counts[status]:
            findings.append(("error", "summary.%s" % key,
                             "says %r; the rows hold %d" % (summary[key], counts[status])))
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("results")
    ap.add_argument("--document", help="the canonical document, to confirm the digest is of it")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = pathlib.Path(args.results)
    try:
        res = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        print("%s cannot be read: %s" % (path, e), file=sys.stderr)
        return 1

    doc_digest = digest(args.document) if args.document else None
    findings = check(res, doc_digest)
    errors = [f for f in findings if f[0] == "error"]
    notes = [f for f in findings if f[0] == "note"]

    if args.json:
        print(json.dumps({"file": str(path), "format_version": res.get("format_version"),
                          "errors": [{"field": f, "says": w} for _, f, w in errors],
                          "notes": [{"field": f, "says": w} for _, f, w in notes]}, indent=2))
        return 1 if errors else 0

    if errors:
        print("%s does not follow docs/verifier-results-format.md (%d):" % (path, len(errors)))
        for _, field, what in errors:
            print("  - %-24s %s" % (field or "(file)", what))
    else:
        rows = res.get("results") or []
        print("%s is a well-formed claim — %d row(s), format %s."
              % (path, len(rows), res.get("format_version")))
    if notes:
        print("\nsays less than it could (%d):" % len(notes))
        for _, field, what in notes:
            print("  - %-24s %s" % (field, what))
    if errors:
        print("\nThis says nothing about whether the implementation is compliant, which is the\n"
              "verifier's report to make. It says the file cannot be relied on to carry it.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
