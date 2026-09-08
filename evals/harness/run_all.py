"""Run every self-verifying check in the harness. Exit non-zero if any fails."""
import subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = [("generation store freshness", "genstore.py"),
          ("token lock rules (Steps 4-5)", "tokenlock.py"),
          ("token validation end-to-end", "run_token_validation.py"),
          ("contract invariants", "invariants.py"),
          ("stored generations", "check_generations.py")]
fail = []
for label, script in CHECKS:
    r = subprocess.run([sys.executable, os.path.join(HERE, script)], capture_output=True, text=True)
    print(f"{'PASS' if r.returncode == 0 else 'FAIL'}  {label}")
    if r.returncode != 0:
        fail.append(label); print(r.stdout[-1500:] or r.stderr[-1500:])
print(f"\n{len(CHECKS) - len(fail)}/{len(CHECKS)} suites passing")
sys.exit(1 if fail else 0)
