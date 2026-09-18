# System policy (L1) — TEMPLATE

**Copy this into your own repository, fill it, own it.** These are your design system's
decisions, not the skill's. The copy lives with your contracts — record its path as
`contracts.policy` in `.claude/design-system-context.yml` — and **never inside the skill's
own `system/` directory**, which ships blank and is replaced wholesale on the next update.
Every row ships blank on purpose: an unfilled policy is a visible gap, the same rule as a
pending token. Delete a row only if you have decided it does not apply, and say why.

**A row with no statement is undecided, not a requirement.** It binds nothing and fails nothing.
It is asked the first time a component *engages* it — `engaged-by` says when that is — so a
Button never raises the loading convention, and the touch-target floor waits for the first
component targeting a touch platform. The skill asks it then, once, and every later component
inherits the answer.

| `engaged-by` | engaged when the component being resolved… |
|---|---|
| `any` | exists — the first component of all |
| `observe:<type>` | has any requirement, inherited or its own, observing that type |
| `platform:touch` | targets `ios` or `android` |
| `token:<property>` | declares a token slot for that property |
| `state:<name>` | has a behavioral prop or a machine state of that name |

**Deferring is a decision too.** Write `deferred — YYYY-MM-DD` in the statement, and the row is not
asked again until someone clears it. Without that, a deferred row would be re-asked on every
component, and a question asked every time stops being read.

**Deciding a row means writing its statement AND its bindings** — per platform, in the policy's
`.bindings.json`, exactly like a contract's. A decided row with no binding fails the parse.

The decision list is drawn from T1's G5 and G6 — the cross-cutting facts that kept appearing
as "under-specified component requirements" because there was no system layer to hold them.

| when | decision | statement | observe | kind | engaged-by | id |
|---|---|---|---|---|---|---|
| always | token discipline | | token | state | any | id-POL-01 |
| always | focus indicator | | state | state | observe:focus | id-POL-02 |
| when:touch_input | touch-target floor | | layout | state | platform:touch | id-POL-03 |
| always | literal denial | | token | state | any | id-POL-04 |
| when:reduced_motion | reduced motion | | state | state | token:duration | id-POL-05 |
| always | announcement politeness | | announcement | behavior | observe:announcement | id-POL-06 |
| always | validation timing | | event | behavior | state:invalid | id-POL-07 |
| always | loading convention | | state | state | state:loading | id-POL-08 |
| always | empty-state convention | | state | state | state:empty | id-POL-09 |
| always | error convention | | state | state | state:error | id-POL-10 |

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
