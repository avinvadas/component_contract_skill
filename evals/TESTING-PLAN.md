# Testing environment — plan

> **Rebuilt for the six-chapter format.** `fixtures/contracts/good.md` is a contract in the
> current format with its bindings; `broken.md` carries one deliberate violation of each
> invariant; `harness/invariants.py` checks document shape and delegates everything the
> resolver can decide to `scripts/resolve.py`, rather than reimplementing those rules and
> drifting from them. **The stored generations under `generations/` predate this and are
> stale by construction** — they were produced by a different skill hash, which the store
> already treats as non-comparable; they are kept as a record, not as a baseline.

The purpose of this environment is to battle-test the skill against the four things it claims to be accountable for (see the README's "What this skill is accountable for"). It is deliberately built as three separate suites, because those four claims are not testable by the same mechanism, at the same cost, or at the same frequency — and running them as one undifferentiated pass is the main way this kind of harness ends up expensive and uninformative.

## Three suites

Named, not numbered — `tier` is already this repo's word for the primitive/semantic/component axis and a slot in `naming-pattern`, and `layer` is already Phase 5's intent/manifestation distinction.

| Suite | Question it answers | Input → output | Accountability axis | Cost |
|---|---|---|---|---|
| **Generation** | Does it produce the right contract? | interview transcript → `.md` + json | derivation, provenance | cheap; run on every change |
| **Sufficiency** | Is the contract sufficient to build from? | contract **only** → an implementation | sufficiency | expensive; run per release |
| **Validation** | Do the checks catch real defects? | implementation → findings | validation | medium; needs fixtures |

**The Sufficiency suite is the one that tests the actual promise.** An agent that has never seen the interview receives only the contract and builds the component. The instrument is *how many questions it has to ask* — that number is a direct measurement of "nothing in it is inferred or left implicit that an implementer would need to ask about." No other test measures that claim, and no amount of Generation passing implies it.

## Two classes of assertion

Keeping these apart is what stops corpus growth from being linear in effort.

**Invariants** hold for every contract this skill will ever produce, and are derivable directly from SKILL.md. They are written once and applied to every case:

- every treatment-2 section has exactly one row per platform listed in `platforms:`
- no contract contains "same as Web" or any equivalent cross-reference in place of a value
- every unresolved value is explicitly flagged pending; none is left blank or invented
- Design Intent is one sentence and carries no ownership/delegation paragraph
- no Title zone names a fixed heading level (`<h2>` and friends)
- §3.1 is omitted when Q8 answered "none of the above"
- every `.structure.json` `rootElement.expect` is tree-observable per the mapping in `references/structural-fact-validation.md`, or explicitly `unresolved`

**Case regressions** are the one specific mistake a case exists to catch — Drawer's "convention, not interception"; Toast's "3 rows, not 6". The current `evals.json` already names these well; they are the part that must be authored per case.

## Storing generations

Generation is ~100% of the harness's cost — **measured, not estimated: one Badge run on Opus took 263s over 19 turns, reading 763K cached tokens and writing 19K, at $0.98** — while assertions are free local Python. So generations are produced once and asserted against many times, and **only a change to the skill invalidates them**. Iterating on assertions costs nothing, which matters because assertions get iterated on a lot.

`harness/genstore.py` keys each stored output on a content hash of **SKILL.md plus every reference file** — a reference change can alter output just as much as a SKILL.md change can. Any generation whose hash differs from the current skill is stale by construction, and the harness says so rather than leaving someone to notice. That is the specific failure the old `contracts/` directory had: outputs with no record of what produced them, indistinguishable from current ones without reading both.

That measured figure corrects an earlier estimate here of "37K in / 14K out", which assumed a single inference. The skill runs as an agentic loop — 19 turns for the *simplest* case — so context is re-read each turn and cache reads dominate. Plan sweeps on roughly **$1/run on Opus**: the full corpus at N=3 with baselines is 30 runs, so ~$30. Sonnet is the cheaper default for exactly this reason.

Run-1 of each case is committed as the reviewable reference, so a diff shows what a skill change actually did to real output. Runs 2+ are gitignored — they exist only to measure variance and would be noise in review.

## Determinism

Contract prose legitimately varies between correct runs, so **assertions are property-based, never diff-based**. For prose-shaped expectations an LLM judge with one specific named regression is more robust than regexing markdown tables; it is also noisier, which is what variance handles.

**Every case runs N times and variance is a first-class output.** A case passing 3/5 is a finding about skill reliability, not noise to be suppressed by rerunning until green.

## What the current evals cannot reach

The evals hand-feed all ten answers in a single prompt. That exercises Phases 2–6 and bypasses Phase 1 entirely, along with Phase 0A (freshness) and 0B (context detection and creation). So nothing currently tests whether Q7's options are derived sensibly from Q1, whether a question is asked that shouldn't be, or whether `design-system-context.yml` is detected, written, and honored.

Closing that needs a **simulated respondent** — an agent playing the designer from a persona sheet, answering `AskUserQuestion` calls as they arrive. Worth building at Milestone 3; worth knowing we don't have it before then.

## Corpus

The existing five cases were chosen well and each names its own regression: Badge (minimal), Modal (composite + adaptive + `$ref`), Toast (multi-platform divergence), RadioGroup (compound pattern, follow-up fired but correctly produced no Platform column), Drawer (named actions vs. undifferentiated slot).

Known coverage gaps, to fill as the corpus grows:

- **macOS has no case at all** (only the uncommitted SegmentedControl touches it)
- no link/navigation root (`<a href>` — the one row in the Web decision table marked "always")
- no drag-to-reorder, no URL-based tab routing
- Phase 2 Path A (Figma) is never exercised
- `generated_downstream: true` is never exercised end to end, so the token check has no case

## Sequencing

### Milestone 0 — prerequisites *(in progress)*

Nothing here is harness work; it is removing things that would make a harness test a moving or broken target.

- [x] **Run the token-name algorithm for the first time.** Done against the 162-token fixture via `harness/tokencheck.py`. Core algorithm confirmed sound — every documented worked example passes, reordered and substituted names fail at every row and depth. Three defects found and fixed in the spec: silent wrong-lock, row ambiguity, depth non-injectivity.
- [x] **Implement Steps 4-5 in the harness.** `harness/tokenlock.py`, with self-tests that exercise each of the three fixed defects. Surfaced one further spec gap: the two blocking conditions are independent and must both be reported.
- [x] **Resolve the `rootElement` translation gap.** §2.1 names a native construct; native trees never contain that string. Mapping now specified per platform, with `unresolved` as the honest output when it isn't known.
- [x] **Exercise `generated_downstream: true` end to end.** `harness/run_token_validation.py` against real generated fixtures for two platforms on different conventions: 324 correct names produce zero findings, 5 injected defects are all caught with none extra. First negative control in the repo.
- [x] **Retarget the two platform-blocked eval cases.** Toast to Web/Android/macOS (preserves its regression and closes the macOS gap), RadioGroup to Web/iOS; the Windows and Linux regressions are parked in `evals.json` with what unblocks them.
- [ ] **Regenerate SegmentedControl** under current spec as a baseline; the committed one predates several spec changes.
- [ ] Decide whether `contracts/` and its build artifacts belong in the repo.

### Milestone 1 — the Generation suite *(in progress)*

- [x] **Invariants implemented** — `harness/invariants.py`, seven properties derived from SKILL.md, verified against a conforming fixture (zero violations) and a fixture violating each one (all six categories caught). Building the negative control alongside found two bugs in the checker itself that a positive-only test would have missed.
- [x] **Unified runner** — `harness/run_all.py`; 3/3 suites passing.
- [ ] Convert each case's prose `expected_output` into invariants + one named regression.
- [ ] Execute a case N times and report pass rate per assertion (needs a way to invoke the skill programmatically).

`skill-creator` could not be inspected from disk — it loads on demand — so whether its runner fits is still open. The invariants are ours regardless; the execution layer is kept thin so another runner can be substituted rather than rewritten.

### Milestone 2 — the Validation suite, Web only

Web's tree is free via a headless browser; native needs simulators, XCUITest, and Compose instrumented tests. Building the entire loop on Web first costs roughly a tenth as much and everything learned transfers.

Needs: one known-good Web implementation per corpus component, a structure-file executor (read DOM, evaluate expectations, emit findings), and a **mutation set**.

**Fault injection is the core of this suite.** One mutation, one expected finding:

| Mutation | Expected finding |
|---|---|
| `<button>` → `<div onclick>` | §2.1 root element miss |
| remove `aria-labelledby` | §6.1 accessibility miss |
| swap icon/label order | §2.2 order violation |
| rename a token to a valid-but-different canonical path | structural mismatch |
| rename a token to a *plausible* wrong one | passes visual regression; must be caught here |

This yields **sensitivity** (does it catch?) and **specificity** (does it stay silent on the clean build?). Without negative controls, a green run only proves the checker didn't crash. The last row is the case that justifies the Validation suite existing at all — a defect that renders acceptably and passes screenshot tests.

### Milestone 3 — the Sufficiency suite (blind implementation)

An agent receives the contract only and builds the component; Milestone 2's executor grades the result. Add the simulated respondent here to bring the skill's own Phases 0 and 1 under test.

### Milestone 4 — native

iOS via `xcodegen` + XCUITest — proven once by hand in this repo, needs to become a repeatable script. Android via Compose instrumented tests for the semantics `uiautomator dump` cannot see. Both ceilings are documented in `references/structural-fact-validation.md`; neither is a tooling detail to paper over.

## skill-creator: evaluated, does not replace this — but contributed two things

Checked before building the runner. It does **not** cover what this harness needs:

- **No run-to-run variance.** It spawns one with-skill and one baseline run per case per iteration. The `mean ± stddev` in its benchmark is computed across *different evals*, not across repeated runs of the same eval. The only place it repeats a query is description optimization, which runs each 3× to measure *triggering*, not output stability.
- **Assertions are LLM-judged**, represented as text strings graded into `{text, passed, evidence}`. It does advise writing scripts for programmatically-checkable assertions, so `invariants.py` could feed it through an adapter — but that is integration work, not a plug-in point.
- **Different shape of loop.** Its cycle is human-in-the-loop skill *development* — draft, run, review in a browser, improve. This harness is automated regression detection. Both are useful; neither substitutes for the other.

Two things from it are worth adopting:

**Baseline comparison, and this was a genuine gap.** It runs every case both with and without the skill. That answers a question nothing here asked: *does the skill actually beat no-skill?* All four accountability axes assume it adds value, and no invariant can detect that it doesn't — a naive run producing a comparable contract would pass every check we have. `harness/generate.py --baseline` now supports this.

**Triggering is untested.** `run_loop.py` optimizes a skill's description against should-trigger / should-not-trigger queries. Whether this skill fires when it should — and stays quiet when it shouldn't — has never been measured, and its description is long and deliberately pushy. Worth running once the skill itself is stable.

## Before building the Generation runner

---

## Open proposal — classify each manifestation row as state or behavior

**Status: proposed, not implemented.** Raised 2026-09-08; recorded here so it is not lost.

SKILL.md's treatment-2 fidelity rule currently frames a platform's difference as a deficiency — *"can't fully carry what the intent requires... or is only approximated."* That is the wrong lens when a platform meets the same intent by a different mechanism rather than a weaker one. iOS has no declarative live region; it posts an announcement when a value changes. That fully achieves "the user is informed without focus moving" — it is a different axis, not an inferior match, and recording it as approximate is inaccurate.

The proposal is to have each manifestation row declare what **kind** of fact it is:

- **State** — a property present in the tree at rest (`aria-live="polite"`, `liveRegion = Polite`). Verifiable by snapshot.
- **Behavior** — something that must happen at a moment (iOS posting an announcement). Verifiable only by triggering and observing.

Three consequences, each fixing a current defect:

1. Fidelity is measured against the intent, not against the other rows' shape — so a different-mechanism match records cleanly, and "only approximated" is reserved for genuine shortfalls.
2. `structure.json` stops implying a node exists where none can. Its presence check looks for a node in a snapshot; a behavioral row has none, and today would be either silently omitted or written as an expectation that always fails.
3. Specificity is bounded by the platform rather than levelled across platforms. "Post an announcement when the value changes" is the complete requirement on iOS, not a vaguer version of the Web one.

This is general rather than an iOS special case, and it tells the harness which rows it can verify from a snapshot at all — a distinction Milestone 2 needs regardless.

Touches: treatment 2's fidelity paragraph in SKILL.md, the §2.1/§6.1 template notes, and `structural-fact-validation.md`'s extraction rules.
