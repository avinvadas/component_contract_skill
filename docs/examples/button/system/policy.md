# System policy (L1) — excerpt

Cross-cutting decisions, written once, inherited by every contract.

| id | statement | observe | kind | scope |
|---|---|---|---|---|
| POL-01 | Every value that can resolve through a design token does; no literal is used where a token slot exists. | token | state | all |
| POL-02 | A focused control renders a focus indicator distinguishable from its unfocused appearance. | state | state | all |
| POL-03 | Interactive controls meet the platform's minimum touch-target size on touch-capable platforms. | layout | state | all |

POL-02 and POL-03 are realised for button-archetype components by BTN-07 and BTN-11;
the policy is what makes them non-negotiable across *all* archetypes.
