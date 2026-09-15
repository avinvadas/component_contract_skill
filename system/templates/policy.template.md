# System policy (L1) — TEMPLATE

**Copy this, fill it, own it.** These are your design system's decisions, not the skill's.
Every row ships blank on purpose: an unfilled policy is a visible gap, the same rule as a
pending token. Delete a row only if you have decided it does not apply, and say why.

The decision list is drawn from T1's G5 and G6 — the cross-cutting facts that kept appearing
as "under-specified component requirements" because there was no system layer to hold them.

| decision | statement | observe | kind | required | id |
|---|---|---|---|---|---|
| token discipline | *(e.g. every value that can resolve through a token does)* | token | state | always | <sub>id-POL-01</sub> |
| focus indicator |  | state | state | always | <sub>id-POL-02</sub> |
| touch-target floor |  | layout | state | when:touch_input | <sub>id-POL-03</sub> |
| literal denial | *(deny-by-default across a declared property set)* | token | state | always | <sub>id-POL-04</sub> |
| reduced motion |  | state | state | when:reduced_motion | <sub>id-POL-05</sub> |
| announcement politeness |  | announcement | behavior | always | <sub>id-POL-06</sub> |
| validation timing |  | event | behavior | always | <sub>id-POL-07</sub> |
| loading convention |  | state | state | always | <sub>id-POL-08</sub> |
| empty-state convention |  | state | state | always | <sub>id-POL-09</sub> |
| error convention |  | state | state | always | <sub>id-POL-10</sub> |

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
