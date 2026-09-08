"""Apply the invariants to every attributable stored generation.

Until this existed, the suites only ever examined fixtures written by hand for
the purpose — which verifies that the checkers work, not that the skill does.
This closes that: real output the skill produced is checked on every run of the
harness, so a regression in the skill surfaces the same way a regression in a
checker would.

Quarantined generations are skipped deliberately. They cannot be attributed to
an invocation, so a result derived from them is not a measurement — see
evals/generations/_quarantine/README.md.
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genstore
from invariants import check_contract, check_structure, check_output_shape


def component_of(rundir):
    """The contract file names the component; find it wherever it landed."""
    for dirpath, _, names in os.walk(rundir):
        for n in names:
            if n.endswith(".md") and not n.startswith("."):
                return n[:-3], os.path.join(dirpath, n)
    return None, None


def check_run(rundir):
    v = []
    comp, md = component_of(rundir)
    if comp is None:
        return [("no contract", f"{rundir} contains no .md contract")]
    v += [(x.invariant, x.detail) for x in check_output_shape(rundir, comp)]
    v += [(x.invariant, x.detail) for x in check_contract(md)]
    for dirpath, _, names in os.walk(rundir):
        for n in names:
            if n.endswith(".structure.json"):
                v += [(x.invariant, x.detail) for x in check_structure(os.path.join(dirpath, n))]
    return v


if __name__ == "__main__":
    rows = genstore.stored()
    if not rows:
        print("no attributable generations stored — nothing to check.")
        print("This passes vacuously; it is not evidence the skill works.")
        sys.exit(0)

    cur, total, unattributed = genstore.skill_hash(), 0, 0
    print(f"current skill hash: {cur}\n")
    for case, h, run, path in rows:
        prov = os.path.join(path, "provenance.json")
        ident = {}
        if os.path.isfile(prov):
            ident = json.load(open(prov)).get("invocation") or {}
        tag = "" if ident else "  [no invocation recorded — pre-dates attribution fix]"
        if not ident:
            unattributed += 1
        v = check_run(path)
        total += len(v)
        state = "stale" if h != cur else "current"
        print(f"{case}/{run}  ({state}){tag}")
        print(f"  {len(v)} violation(s)")
        for inv, detail in v:
            print(f"    {inv}: {detail}")

    print(f"\n{len(rows)} generation(s), {total} violation(s), "
          f"{unattributed} without recorded invocation")
    # Violations in real output are findings about the skill, reported not
    # failed — the harness's job here is to surface them, not to gate on them.
    sys.exit(0)
