"""Generation runner — invoke the real skill headlessly and store the output.

Uses `claude -p` rather than the API directly, deliberately: the skill's
behaviour *includes* which reference files it chooses to read, and inlining
those into an API prompt would both change that behaviour and cost ~34K tokens
per run instead of ~8K. This is the production path, so what it measures is
what a user actually gets.

Nothing here runs automatically. Generation is ~100% of the harness's cost
(~37K in / 14K out per run), so a sweep is always an explicit command.

    python3 generate.py --list
    python3 generate.py --case badge --runs 1            # one case, one run
    python3 generate.py --case badge --runs 3 --baseline # + a no-skill control
    python3 generate.py --all --runs 3                   # full sweep (costly)

`--baseline` reruns the same prompt with the skill suppressed. That answers a
question the invariants cannot: whether the skill actually beats no-skill. If a
naive run produces a comparable contract, that is the most important finding
available and no amount of invariant-passing would reveal it.
"""
import argparse, json, os, subprocess, sys, time, shutil, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import genstore

EVALS = os.path.join(ROOT, "evals", "evals.json")

# Two different measurements, not one with a parameter:
#
#   claude-sonnet-5  production reality — what a user of this skill actually gets.
#                    This is the default, because that is the honest number.
#   claude-opus-5    quality ceiling — isolates skill defects from model limits.
#                    A failure here is the skill's fault, not the model's.
#
# The GAP between them is itself a finding. This skill's stated accountability
# includes "nothing left implicit that an implementer would need to ask about";
# if it holds on Opus but degrades on Sonnet, the skill is leaning on model
# capability to fill gaps it should have stated outright. Generations are keyed
# by model so the two never overwrite each other.
DEFAULT_MODEL = "claude-sonnet-5"


def preflight():
    """The CLI needs its own credentials — a subprocess does not inherit the
    desktop app's session. Check once, cheaply, rather than discovering it
    after burning a run per case."""
    if not shutil.which("claude"):
        return "the `claude` CLI is not on PATH"
    r = subprocess.run(["claude", "-p", "reply with: ok", "--output-format", "json"],
                       capture_output=True, text=True, timeout=120)
    try:
        j = json.loads(r.stdout)
    except Exception:
        return f"could not parse CLI output: {r.stdout[:200]}"
    if j.get("is_error"):
        return f"CLI reports: {j.get('result', 'unknown error')}"
    return None


def load_cases():
    d = json.load(open(EVALS))
    out = {}
    for e in d["evals"]:
        slug = re.split(r"\s|—", e["name"])[0].strip().lower()
        out[slug] = e
    return out


def build_prompt(case, outdir, with_skill):
    prompt = case["prompt"].replace("/tmp/contracts/", outdir.rstrip("/") + "/")
    if with_skill:
        return (f"Use the component-contract skill to do the following.\n\n{prompt}")
    # Baseline: same task, skill explicitly suppressed, so the comparison is
    # about the skill's contribution rather than about prompt wording.
    return ("Do the following WITHOUT using any skill — work from your own knowledge. "
            f"Do not invoke the component-contract skill.\n\n{prompt}")


def run_one(case, slug, run_idx, with_skill=True, model=None, timeout=1800):
    kind = "with_skill" if with_skill else "baseline"
    outdir = genstore.generation_dir(f"{slug}/{kind}" if not with_skill else slug,
                                     run_idx, model=model or DEFAULT_MODEL)
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)

    cmd = ["claude", "-p", build_prompt(case, outdir, with_skill),
           "--output-format", "json", "--permission-mode", "acceptEdits",
           "--model", model or DEFAULT_MODEL]

    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=timeout)
    dt = time.time() - t0

    meta = {}
    try:
        j = json.loads(r.stdout)
        meta = {"total_cost_usd": j.get("total_cost_usd"),
                "usage": j.get("usage"),
                "num_turns": j.get("num_turns"),
                "session_id": j.get("session_id")}
    except Exception:
        meta = {"parse_error": True, "stdout_tail": r.stdout[-800:]}

    genstore.write_provenance(f"{slug}/{kind}" if not with_skill else slug, run_idx,
                              model=model or DEFAULT_MODEL,
                              extra={"duration_seconds": round(dt, 1),
                                     "exit_code": r.returncode,
                                     "with_skill": with_skill, **meta})
    produced = [f for f in os.listdir(outdir) if f != "provenance.json"]
    print(f"  {kind:10} run-{run_idx}: exit {r.returncode}, {dt:.0f}s, "
          f"{len(produced)} file(s) — {outdir.replace(ROOT + '/', '')}")
    if r.returncode != 0:
        print(f"    stderr: {r.stderr[-300:]}")
    return outdir


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--case")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--baseline", action="store_true", help="also run without the skill")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    a = ap.parse_args()
    cases = load_cases()

    if a.list or not (a.case or a.all):
        print(f"skill hash: {genstore.skill_hash()}\ncases:")
        for slug, c in cases.items():
            print(f"  {slug:12} {c['name']}")
        print("\nNothing runs without --case or --all. Generation is the expensive step.")
        sys.exit(0)

    problem = preflight()
    if problem:
        print(f"cannot generate — {problem}\n")
        print("The CLI authenticates separately from the desktop app. To enable this\n"
              "harness, run `claude` once in your own terminal and complete /login there,\n"
              "or set an API key in your shell environment. Both are one-time actions only\n"
              "you can perform; nothing here should handle your credentials.\n")
        sys.exit(2)

    todo = list(cases.items()) if a.all else [(a.case, cases[a.case])]
    est = len(todo) * a.runs * (2 if a.baseline else 1)
    print(f"skill hash: {genstore.skill_hash()}")
    print(f"model: {a.model}")
    print(f"{est} generation(s) — roughly {est * 37}K in / {est * 14}K out\n")
    for slug, case in todo:
        print(f"{case['name']}")
        for i in range(1, a.runs + 1):
            run_one(case, slug, i, True, a.model)
            if a.baseline:
                run_one(case, slug, i, False, a.model)
