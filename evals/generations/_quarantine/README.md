# Quarantine — generations that cannot be attributed

These runs exist, ran to completion, and produce real invariant results. What
they lack is a traceable origin: `provenance.json` recorded what the runner
believed (case, model, skill hash) but nothing about who invoked it, and by the
time anyone looked, nobody could say how they were produced or under which code
state.

They are held here rather than deleted, because they are the only evidence of
one genuine observation — the same case produced output in three different
directory shapes across runs (nested, flat, and both at once), which suggests
the Output rule's placement is *unstable* rather than consistently wrong. That
is worth re-testing deliberately.

They are held here rather than left in the store, because a comparison was
built on them and reported as an Opus/Sonnet finding before the attribution
gap was noticed. The observation was real; the attribution was not. Data
nobody can trace should not sit where it looks authoritative.

`genstore.invocation_identity()` now records argv, pid/ppid, user, host and the
harness commit, so this class of mystery does not recur. Nothing in quarantine
should be cited as a measurement.
