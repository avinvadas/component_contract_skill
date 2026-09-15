# System policy (L1) — TEMPLATE

**Copy this, fill it, own it.** These are your design system's decisions, not the skill's.
Every row ships blank on purpose: an unfilled policy is a visible gap, the same rule as a
pending token. Delete a row only if you have decided it does not apply, and say why.

The decision list is drawn from T1's G5 and G6 — the cross-cutting facts that kept appearing
as "under-specified component requirements" because there was no system layer to hold them.

| when | decision | statement | observe | kind | id |
|---|---|---|---|---|---|
| always | token discipline | *(e.g. every value that can resolve through a token does)* | token | state | id-POL-01 |
| always | focus indicator |  | state | state | id-POL-02 |
| when:touch_input | touch-target floor |  | layout | state | id-POL-03 |
| always | literal denial | *(deny-by-default across a declared property set)* | token | state | id-POL-04 |
| when:reduced_motion | reduced motion |  | state | state | id-POL-05 |
| always | announcement politeness |  | announcement | behavior | id-POL-06 |
| always | validation timing |  | event | behavior | id-POL-07 |
| always | loading convention |  | state | state | id-POL-08 |
| always | empty-state convention |  | state | state | id-POL-09 |
| always | error convention |  | state | state | id-POL-10 |

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
