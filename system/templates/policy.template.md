# System policy (L1) — TEMPLATE

**Copy this, fill it, own it.** These are your design system's decisions, not the skill's.
Every row ships blank on purpose: an unfilled policy is a visible gap, the same rule as a
pending token. Delete a row only if you have decided it does not apply, and say why.

The decision list is drawn from T1's G5 and G6 — the cross-cutting facts that kept appearing
as "under-specified component requirements" because there was no system layer to hold them.

| id | decision | statement | observe | kind | required |
|---|---|---|---|---|---|
| POL-01 | token discipline | *(e.g. every value that can resolve through a token does)* | token | state | always |
| POL-02 | focus indicator | | state | state | always |
| POL-03 | touch-target floor | | layout | state | when:touch_input |
| POL-04 | literal denial | *(deny-by-default across a declared property set)* | token | state | always |
| POL-05 | reduced motion | | state | state | when:reduced_motion |
| POL-06 | announcement politeness | | announcement | behavior | always |
| POL-07 | validation timing | | event | behavior | always |
| POL-08 | loading convention | | state | state | always |
| POL-09 | empty-state convention | | state | state | always |
| POL-10 | error convention | | state | state | always |

## Declared property set for POL-04

The properties a literal is denied in. Anything outside this set is unchecked, so widening it
is how the policy gets stronger.

```
background · foreground · border · radius · spacing · opacity · elevation · duration
```

## Exemptions

A literal is a failure unless something authorises it. Exemptions carry a reason, the same
rule that governs `scope` and divergences.

| property | value | where | reason |
|---|---|---|---|
