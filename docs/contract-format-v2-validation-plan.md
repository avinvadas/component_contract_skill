# Validating contract format v2 before adopting it

**Status: plan.** Companion to `contract-format-v2-proposal.md`.

v2's own summary of itself is the reason this plan has to be thorough: *strictly better if the requirements are complete, strictly worse if they are lazy.* That is not a format you can accept on the strength of one convincing example. A single converted component will always look fine, because whoever converts it is carrying the missing requirements in their head.

So the question this plan answers is not "does v2 look right?" It is **"what would v2 fail to catch, and can we find that out on paper before betting the skill on it?"**

## What can actually go wrong

Seven failure modes. Each test below targets a specific one; the plan is only as good as this list, so it is stated first and separately.

| # | Failure | Why it is plausible |
|---|---|---|
| F1 | **Incompleteness** — a requirement set omits something v1 got implicitly | v1's `<button>` was one word standing for Enter *and* Space activation, pre-scripting operability, focus reachability, form participation. None was written down, so none is obviously missing. |
| F2 | **Platform leakage** — a requirement reads as neutral but encodes one platform's model | "focus moves to the first interactive element" presumes a focus model. "Reading order" presumes linearity. Both are Web habits. |
| F3 | **Unbindability** — a requirement sounds testable but has no observable on some platform | Only discovered by trying to write the binding. |
| F4 | **Non-discrimination** — a requirement both correct and incorrect implementations satisfy | "The component is accessible." Decoration that inflates the count without testing anything. |
| F5 | **Vocabulary gaps** — an archetype whose role is not in the closed set | The set was drafted from a handful of components. |
| F6 | **Overlap or seams** — two requirements overlapping, or a gap hiding between them | A defect reported twice looks worse than it is; a defect in the seam is reported not at all. |
| F7 | **Lost implementer guidance** — v2 tells you what must be true, not what to build | Acknowledged in the proposal. Unmeasured. |

## The tests

Five of the six are paper exercises with no generation cost. That is deliberate — the expensive test runs last, once the cheap ones have stopped finding things.

### T1 — Coverage regression *(targets F1)*

**The core test, and the one with a systematic method rather than a judgment call.**

v1's implicit bundle has a traceable source: every native element it names carries behaviour the platform provides for free. So what v2 owes is enumerable rather than guessable.

1. For every native element or control v1 names across the corpus, list what that platform gives free: keyboard activation and *which* keys, focus participation, pre-scripting operability, form participation, platform gesture handling, text scaling, assistive-technology navigation affordances.
2. Every item on that list must map to at least one v2 requirement id.
3. Anything unmapped is either a genuine gap, or a deliberate drop that must be written down **with its reason**, not quietly omitted.

**Pass:** 100% of enumerated implicit facts have a v2 home or a recorded justification.
**This is the test that decides whether v2 ships.** F1 is the failure that makes v2 worse than v1, and this is the only test that measures it directly.

### T2 — Bindability *(targets F3)*

For each requirement, attempt a binding on all four platforms.

**Pass:** every requirement either binds on every platform, or is marked `unverified` with a *named* method gap (per the proposal's method table). A requirement that cannot be bound anywhere is written at the wrong level and must be rewritten.

Cheap, and it front-loads discovery that would otherwise arrive during implementation.

### T3 — Mutation / discrimination *(targets F4, and F1 again empirically)*

**The centrepiece, because it is the only empirical test here rather than a judgment.** The method is already proven three times in this repo: build the failing case alongside the passing one, and the failing case finds the bugs.

For each requirement, construct an implementation that violates *only that requirement*. Then:

- Does the binding **fail** it? A requirement no mutation can fail is decoration — delete it or sharpen it.
- Does the clean implementation **pass** every requirement? Any spurious failure is a defective requirement, not a defective implementation.

Then the harder direction, which is what actually tests F1: **construct implementations that are wrong in ways v1 would have caught, and check whether v2 catches them.** The canonical set:

| Mutation | v1 caught it via | v2 must catch via |
|---|---|---|
| `<div role="button" tabindex="0">` with Enter-only handler | named element | rendered identity, *and* a Space-activation requirement |
| control unreachable without scripting | named element | an explicit pre-scripting requirement |
| heading rendered as styled text with a heading role | named element | identity + role, separately |
| link implemented as a button that calls `navigate()` | named element | a requirement that it exposes link semantics and supports open-in-new |
| native control replaced by a generic view exposing correct traits | named element | whatever the requirements *explicitly* demand — this is the honest test of whether the bundle was captured |

**Pass:** every mutation is caught by a named requirement, or the miss is recorded as a known limit with its reason.

### T4 — Adversarial neutrality read *(targets F2)*

Read every requirement asking only: *does this presuppose a platform's model?* Fixed probes, applied to each:

- Does it assume focus exists as a movable singleton?
- Does it assume a linear reading order?
- Does it assume a pointer? a keyboard? a hover state?
- Does it assume a declarative property rather than an action taken at a moment?
- Would it read as strange to someone who only knows iOS?

The last probe is the useful one, and it is best run by a reader whose default is *not* the Web — the leakage is invisible to whoever wrote it.

**Pass:** zero requirements containing platform vocabulary, and no hidden assumption surviving the probes.

### T5 — Archetype spread *(targets F5, F6)*

Convert a set chosen to span the decision space, not a convenient sample. Minimum:

| Component | Why it is in the set |
|---|---|
| Badge | trivial baseline — a floor, not evidence |
| Modal | composition, focus containment, dismissal, delegation |
| Tabs / SegmentedControl | selection, panel association, roving focus |
| RadioGroup | compound pattern where children are part of the root's identity |
| Toast / status | the announcement asymmetry — the case that started this |
| Link / navigation | the one archetype whose Web resolution is unconditional |
| Combobox | a pattern deliberately absent from the condensed tables |
| Drag-to-reorder list | operability with no pointer; the hardest keyboard story |

**Pass:** the closed role vocabulary covers all of them with no additions invented mid-conversion. Additions found here are fine — additions found *after* adoption are the failure.

Run T4 across the whole set at once, not per component: F6 seams only appear when requirements from different components sit side by side.

### T6 — Implementer differential *(targets F7)*

The only test needing generation, and the only measure of v2's acknowledged cost.

Give one agent a v1 contract, another the v2 contract plus its bindings, for the same component. Both build it. Compare: how many clarifying questions each needed, and whether each result passes the same checks.

**Pass:** v2's implementer asks no more questions than v1's. If it asks more, the bindings are not yet serving as the implementer's reference — which the proposal predicted might happen and left unresolved.

Cost: ~4 runs at roughly $1 each on Opus, per component. Run it on two components, not eight.

## Sequence

T1 → T2 → T4 → T5 → T3 → T6.

Coverage first, because it is the one that can kill the format outright and there is no point polishing something that fails it. Bindability next, since it is cheap and reshapes requirements. Neutrality and spread before mutation, because mutation is only meaningful against a stable requirement set. T6 last: it is the only one that costs money, and it answers a question that only matters if everything above passed.

## Acceptance bar

v2 is adopted only if **all** of these hold:

1. **Coverage:** every implicit v1 fact has a v2 requirement, or a written justification for dropping it.
2. **Bindability:** every requirement binds on every applicable platform, or is `unverified` with a named method gap.
3. **Discrimination:** every requirement is failed by at least one mutation. No decoration.
4. **Neutrality:** no requirement contains platform vocabulary; the adversarial read finds no hidden assumptions.
5. **Vocabulary:** the closed role set covers the full archetype spread without mid-flight additions.
6. **Guidance:** v2's implementer asks no more questions than v1's.

Failing any one is a reason to fix v2, not to lower the bar. Failing 1 or 3 after fixes is a reason not to adopt it.

## What this plan does not test

It does not test whether the *skill* can reliably produce a good v2 contract from an interview. That is a separate question, answered by the existing Generation suite once the format is fixed. Deciding the format and measuring the skill's fidelity to it are different problems, and conflating them would make both harder to reason about.
