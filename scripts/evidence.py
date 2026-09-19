#!/usr/bin/env python3
"""Turn what an implementation was OBSERVED doing into questions for a person — never edits.

    python3 scripts/evidence.py path/to/Button.md results.json [--json]

The token tree is the authority on tokens; `writeback.py` writes what it answers into the
contract without asking. An implementation is evidence, not authority: when a verifier sees it
reference something the tree did not say — a different token, a literal, a token where the
contract has none — that is a question with three possible answers, and only a person can pick:

    contract   the contract is wrong; change it
    component  the implementation is wrong; it is a defect
    tree       the tree's own statement is wrong (a description, a reading); fix it there

Two kinds of finding:

    contradicts  the tree gave a token and the implementation does something else
    adds         the tree gave no answer (a gap), or the contract says `n/a`, and the
                 implementation uses a token there

`results.json` is a verifier's own report: `{"platform", "results": [{id, status, observed}]}`,
where `observed.css` lists, per CSS property, the variables it references. Names are mapped back
to canonical token paths through the context's `tokens.naming_convention`, so every question is
asked in the tree's vocabulary.
"""
import argparse, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import resolve as R  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("contract")
    ap.add_argument("results")
    ap.add_argument("--context")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    S = R.load_sources(args.contract, args.context)
    R.ENUM_PROPS.update(R.enum_props(S["body"]))
    cases = {c["id"]: c for c in R.resolve_slots(S["body"], S["fm"], S["tree"], S["arch_fm"])}
    res = json.loads(pathlib.Path(args.results).read_text())
    tree = S["tree"]
    conv = ((tree.facts or {}).get("naming_convention") or {}).get(res.get("platform", "web")) or {}
    back = {R.platform_name(t, conv): t for t in tree.tokens} if conv else {}

    def canon(name):
        base = name.split(" at ")[0]
        return back.get(base, base) + (" at " + name.split(" at ")[1] if " at " in name else "")

    from tokens import PROPERTIES, types_of

    def of_type(ref, prop):
        """A shorthand carries more than one kind of token — `border: var(--strokeWidthThin) solid
        var(--colorNeutralStroke1)` — and only the one of the property's own type answers it."""
        tok = tree.tokens.get(ref.split(" at ")[0])
        if tok is None or prop not in PROPERTIES:
            return True
        return tok["type"] in types_of(prop)

    def seen(obs, prop=None):
        refs = list(dict.fromkeys(r for r in (canon(r) for c in (obs or {}).get("css") or []
                                              for r in c["references"]) if of_type(r, prop)))
        lits = [c["value"] for c in (obs or {}).get("css") or [] if not c["references"]]
        return refs, lits

    findings = []
    by_id = {r["id"]: r for r in res["results"]}
    for r in res["results"]:
        c = cases.get(r["id"])
        if c is None or not r.get("observed"):
            continue
        refs, lits = seen(r["observed"], c["property"])
        if c.get("alias_of"):
            # The rest case already carries the same observation: one question, not five.
            rest = by_id.get(c["alias_of"], {})
            same = seen(rest.get("observed"), c["property"]) == (refs, lits)
            if rest.get("status") == r["status"] and same:
                continue
        where = "%s (%s)" % (R.slot_label(c), r["observed"].get("witness", "?"))
        if r["status"] == "FAIL" and c["status"] == "bound":
            said = "the tree gives `%s`" % c["token"]
            did = (", ".join("`%s`" % x for x in refs) if refs
                   else "a literal (%s)" % ", ".join(lits) if lits else "nothing")
            findings.append({"id": r["id"], "kind": "contradicts", "case": where,
                             "tree": c["token"], "implementation": refs or lits,
                             "question": "%s: %s; the implementation uses %s." % (where, said, did)})
        elif refs and (c["status"] == "not-applicable" or r["status"] == "UNVER"):
            said = ("the contract says it is not tokenised" if c["status"] == "not-applicable"
                    else "the tree gives no answer (%s)" % c["status"])
            findings.append({"id": r["id"], "kind": "adds", "case": where, "tree": None,
                             "implementation": refs,
                             "question": "%s: %s; the implementation uses %s."
                                         % (where, said, ", ".join("`%s`" % x for x in refs))})

    if args.json:
        print(json.dumps(findings, indent=2))
        return
    if not findings:
        print("\nevidence: the implementation neither contradicts nor adds to the tree.")
        return
    print("\nevidence: %d question(s) — the implementation disagrees with, or adds to, the tree."
          % len(findings))
    print("Nothing is changed. For each: is the CONTRACT wrong, the COMPONENT defective, "
          "or the TREE's own statement wrong?")
    for kind in ("contradicts", "adds"):
        sel = [f for f in findings if f["kind"] == kind]
        if sel:
            print("\n  %s (%d)" % (kind, len(sel)))
            for f in sel:
                print("  - " + f["question"])


if __name__ == "__main__":
    main()
