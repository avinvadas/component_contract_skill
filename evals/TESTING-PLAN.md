# Testing environment — plan

The purpose of this environment is to battle-test the skill against the four things it claims to be accountable for (see the README's "What this skill is accountable for"). It is deliberately built in tiers, because those four claims are not testable by the same mechanism, at the same cost, or at the same frequency — and running them as one suite is the main way this kind of harness ends up expensive and uninformative.

## Three tiers

| Tier | Question it answers | Input → output | Accountability axis | Cost |
|---|---|---|---|---|
| 1 | Does it produce the right contract? | interview transcript → `.md` + json | derivation, provenance | cheap; run on every change |
| 2 | Is the contract sufficient to build from? | contract **only** → an implementation | sufficiency | expensive; run per release |
| 3 | Do the checks catch real defects? | implementation → findings | validation | medium; needs fixtures |

**Tier 2 is the one that tests the actual promise.** An agent that has never seen the interview receives only the contract and builds the component. The instrument is *how many questions it has to ask* — that number is a direct measurement of "nothing in it is inferred or left implicit that an implementer would need to ask about." No other test measures that claim, and no amount of Tier 1 passing implies it.

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

## Determinism

Contract prose legitimately varies between correct runs, so **assertions are property-based, never diff-based**. For prose-shaped expectations an LLM judge with one specific named regression is more robust than regexing markdown tables; it is also noisier, which is what variance handles.

**Every case runs N times and variance is a first-class output.** A case passing 3/5 is a finding about skill reliability, not noise to be suppressed by rerunning until green.

## What the current evals cannot reach

The evals hand-feed all ten answers in a single prompt. That exercises Phases 2–6 and bypasses Phase 1 entirely, along with Phase 0A (freshness) and 0B (context detection and creation). So nothing currently tests whether Q7's options are derived sensibly from Q1, whether a question is asked that shouldn't be, or whether `design-system-context.yml` is detected, written, and honored.

Closing that needs a **simulated respondent** — an agent playing the designer from a persona sheet, answering `AskUserQuestion` calls as they arrive. Worth building in Phase 3; worth knowing we don't have it before then.

## Corpus

The existing five cases were chosen well and each names its own regression: Badge (minimal), Modal (composite + adaptive + `$ref`), Toast (multi-platform divergence), RadioGroup (compound pattern, follow-up fired but correctly produced no Platform column), Drawer (named actions vs. undifferentiated slot).

Known coverage gaps, to fill as the corpus grows:

- **macOS has no case at all** (only the uncommitted SegmentedControl touches it)
- no link/navigation root (`<a href>` — the one row in the Web decision table marked "always")
- no drag-to-reorder, no URL-based tab routing
- Phase 2 Path A (Figma) is never exercised
- `generated_downstream: true` is never exercised end to end, so the token check has no case

## Sequencing

### Phase 0 — prerequisites *(in progress)*

Nothing here is harness work; it is removing things that would make a harness test a moving or broken target.

- [x] **Run the token-name algorithm for the first time.** Done against the 162-token fixture via `harness/tokencheck.py`. Core algorithm confirmed sound — every documented worked example passes, reordered and substituted names fail at every row and depth. Three defects found and fixed in the spec: silent wrong-lock, row ambiguity, depth non-injectivity.
- [x] **Resolve the `rootElement` translation gap.** §2.1 names a native construct; native trees never contain that string. Mapping now specified per platform, with `unresolved` as the honest output when it isn't known.
- [ ] **Regenerate SegmentedControl** under current spec as a baseline; the committed one predates several spec changes.
- [ ] Decide whether `contracts/` and its build artifacts belong in the repo.

### Phase 1 — Tier 1 harness

Write the invariants once. Convert each case's prose `expected_output` into invariants + one named regression. Runner executes a case N times and reports pass rate per assertion.

### Phase 2 — Tier 3, Web only

Web's tree is free via a headless browser; native needs simulators, XCUITest, and Compose instrumented tests. Building the entire loop on Web first costs roughly a tenth as much and everything learned transfers.

Needs: one known-good Web implementation per corpus component, a structure-file executor (read DOM, evaluate expectations, emit findings), and a **mutation set**.

**Fault injection is the core of this tier.** One mutation, one expected finding:

| Mutation | Expected finding |
|---|---|
| `<button>` → `<div onclick>` | §2.1 root element miss |
| remove `aria-labelledby` | §6.1 accessibility miss |
| swap icon/label order | §2.2 order violation |
| rename a token to a valid-but-different canonical path | structural mismatch |
| rename a token to a *plausible* wrong one | passes visual regression; must be caught here |

This yields **sensitivity** (does it catch?) and **specificity** (does it stay silent on the clean build?). Without negative controls, a green run only proves the checker didn't crash. The last row is the case that justifies the validation layer existing at all — a defect that renders acceptably and passes screenshot tests.

### Phase 3 — Tier 2, blind implementation

An agent receives the contract only and builds the component; Phase 2's executor grades the result. Add the simulated respondent here to bring Phases 0–1 of the skill under test.

### Phase 4 — native

iOS via `xcodegen` + XCUITest — proven once by hand in this repo, needs to become a repeatable script. Android via Compose instrumented tests for the semantics `uiautomator dump` cannot see. Both ceilings are documented in `references/structural-fact-validation.md`; neither is a tooling detail to paper over.

## Before building the Tier 1 runner

Check whether `anthropic-skills:skill-creator` already covers it — it claims to run skill evals and benchmark performance with variance analysis. Worth twenty minutes before reinventing a runner.
