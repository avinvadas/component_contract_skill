# System policy (L1) — excerpt

Cross-cutting decisions, written once, inherited by every contract.

| id | statement | observe | kind | scope |
|---|---|---|---|---|
| POL-01 | Every value that can resolve through a design token does; no literal is used where a token slot exists. | token | state | all |
| POL-02 | A focused control renders a focus indicator distinguishable from its unfocused appearance. | state | state | all |
| POL-03 | Interactive controls meet the platform's minimum touch-target size on touch-capable platforms. | layout | state | all |
| POL-04 | No literal value appears in a contract-relevant style property; any exception carries a recorded exemption and reason. | token | state | all |

POL-04 is deliberately **deny-by-default**. POL-01 can only catch a literal where a token
slot was declared to compare against — so an appearance decision nobody thought to specify
is invisible to it. POL-04 inverts that: the extractor flags every literal in the declared
property set (background, foreground, border, radius, spacing, opacity), and a literal is a
failure unless something authorises it. Exemptions are allowed and carry a reason, the same
rule that governs `scope` and divergences.

POL-02 and POL-03 are realised for button-archetype components by BTN-07 and BTN-11;
the policy is what makes them non-negotiable across *all* archetypes.
