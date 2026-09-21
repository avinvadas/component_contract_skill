# Component Contract

A Claude skill for design systems.

You answer questions about a component in plain language. It writes a **contract** — a single
document saying what that component *is*, for every platform at once. Then each platform can
check its own build against it.

You never need to know HTML, ARIA, or any platform's accessibility API. That part is derived.

---

## Which one are you?

| | Start here |
|---|---|
| **I own a design system.** I want to write contracts for our components. | [Part 1 →](#part-1--creating-a-contract) |
| **I'm building a component** from a design system that already has contracts, and I want to check my work. | [Part 2 →](#part-2--implementing-and-checking-a-component) |

Read the next two sections first. They're short, and both parts assume them.

---

## The idea

A design system says what a component is **once**. Every platform checks its own
implementation against that one statement, using its own test tools.

```
   Button.md                    you write this (with the skill's help)
       │
       │  resolve
       ▼
   generated/Button.web.json    one per platform
   generated/Button.ios.json
       │
       │  read by whoever owns that platform's tests
       ▼
   pass · fail · unverified · n/a
```

A requirement is written once, in plain language, and never mentions a platform:

> *"The control is reachable by the platform's sequential focus navigation."*

That it means `Tab` on web and a swipe gesture on iOS is a **binding**, kept separately. This
is why one document can serve four platforms without a column for each.

**The skill stops at those generated documents.** It describes; it never runs tests. Running
them belongs to whoever owns that platform's toolchain.

---

## The files

After a run, one component looks like this:

```
Button/                              ← the contract
├── Button.md                        ← you write this
├── Button.bindings.json             ← you write this
└── generated/                       ← nothing in here is edited by hand
    ├── Button.spec.md               ← THE FILE PEOPLE READ
    ├── Button.web.json              ← for web tooling
    ├── Button.ios.json              ← for iOS tooling
    └── Button.web.schema.json       ← optional, only if you asked
```

**Two questions are answered by where a file sits.** Top level means *you own it*; inside
`generated/` means *it is rebuilt every run and your edits will vanish*. And `.md` means a
person reads it, `.json` means a machine does.

| File | What it is | Who touches it |
|---|---|---|
| `Button.md` | The contract, in six chapters. Short, because it never repeats what it inherits | You, via the skill |
| `Button.bindings.json` | Per-platform detail — what "focusable" means on iOS | Mostly generated; you rarely edit it |
| `generated/Button.spec.md` | **The readable spec.** Everything above plus everything inherited, resolved in | Nobody edits it. Everybody reads it |
| `generated/Button.<platform>.json` | One machine-readable description per platform | Nobody. Generated |
| `generated/*.schema.json` | Validates props someone passes to your component | Build tooling |

**`Button.md` vs `Button.spec.md` is the distinction to get straight.** The contract is
short because it inherits: one line, `role-archetype: button`, brings in twelve requirements
every platform already guarantees for buttons, and your design system's policy brings in more.
None of that appears in `Button.md`. **It all appears in `Button.spec.md`.**

So: edit the first, read the second.

### The six chapters

| | | |
|---|---|---|
| 1 | **Intent** | what it is, what problem it solves |
| 2 | **Structure** | what the thing is, and which element carries the role |
| 3 | **Composition** | what it contains |
| 4 | **Appearance** | which properties use tokens, and what varies |
| 5 | **Behavior** | what it does, emits, receives |
| 6 | **Accessibility** | how it's exposed to assistive technology |

---

# Part 1 — Creating a contract

*For the design system owner.*

## What you need

| | | If you don't have it |
|---|---|---|
| A **token tree** | DTCG JSON, Style Dictionary, CSS custom properties, or Tailwind `@theme` | It still works. Every token comes back as a gap, addressed to whoever owns the tree |
| A **component in mind** | a name, a purpose, how people interact with it | Nothing to do without it |

Run it from **your design system's repository**, not from the skill's.

## Step 1 — Start it

In Claude, say any of:

- *"Create a component contract for the Badge component"*
- *"Document this component"*
- *"Add Button to the design system contracts"*

First run only, the skill looks around your repo for a token file and proposes what it found —
which groups are your primitive/semantic/component tiers, what shape your token names take. You
confirm. It saves the answers to `.claude/design-system-context.yml` so no later component asks
again.

You can see what that detection looks like on any token file:

```bash
python3 ~/.claude/skills/component-contract/scripts/detect_tokens.py path/to/tokens.json
```

```
## Tiers

- `component` → **component** — 8 tokens, 8 aliased, pointing into `semantic` (7), `core` (1)
- `core` → **primitive** — 8 tokens, 0 aliased
- `semantic` → **semantic** — 7 tokens, 7 aliased, pointing into `core` (7)

## Naming patterns

- `component.{component}.{?}.{property}.{state}`  **needs an answer**
- `component.{component}.{property}` — e.g. `component.button.cornerRadius`

## Questions (5)

- In `component.{component}.{?}.{property}.{state}`, what does segment 3 vary by?
  It takes the values primary, secondary.
- Which property does `bgColor` (color) name? — suggested: **background**
```

It writes nothing. It only proposes, with its evidence.

## Step 2 — Answer ten questions

One at a time. About fifteen minutes.

| | Question | Fills in |
|---|---|---|
| 1 | What's it called, and what problem does it solve? | Intent |
| 2 | Which platforms? | scope |
| 3 | What does it do? | the role |
| 4 | How do people interact with it? | the role |
| 5 | Does it stand alone, or hold other components? | Composition |
| 6 | What are its visible parts? | Composition |
| 7 | Which visual styles does it have? | Appearance |
| 8 | Can its layout change? | Structure |
| 9 | Which extra states? Do you have tokens? | Appearance |
| 10 | Want a props schema too? | output |

**Use your own words.** Every question lets you rename an option by typing your system's name
for it.

**You are never asked about accessibility or behaviour.** Those are derived from questions 3
and 4. If you find yourself being asked about ARIA, something is wrong.

**Leave tokens alone.** When asked about tokens, it's fine to say you have a tree and nothing
more. Token slots get written as `—`, which means *look it up in the tree* — and that's better
than naming one from memory.

## Step 3 — Resolve

```bash
python3 ~/.claude/skills/component-contract/scripts/resolve.py Button/Button.md
```

Real output:

```
  web      83 requirements, 78 binding, 5 n/a
  ios      83 requirements, 77 binding, 6 n/a
  android  83 requirements, 77 binding, 6 n/a

interaction states: hover (background) · focus-visible (rest tokens) · pressed (background) · disabled (background)

token slots: 65 cases from 10 row(s) (43 keep their rest token), 44 bound, 5 n/a, 8 gap(s)
  - APP-04                    absent-from-tree  border-width
  - APP-06                    ambiguous         padding-inline
  - APP-10[variant=primary]   dimension-unmet   background@pressed [variant=primary]
  - APP-08[variant=ghost]     dimension-unmet   background@disabled [variant=ghost]
specificity: 13 component

lint: 0 finding(s)
```

### How to read that

**`65 cases from 10 row(s)`** — you wrote ten rows; it expanded them to sixty-five real cases,
one per variant per state. You write a rule once; it covers every combination.

**Three kinds of output come back, and they mean different things.**

---

### Output A — `lint`: the document is broken

```
lint: 2 finding(s)
  - APP-07: unknown condition 'hoverr' — not in the closed vocabulary
  - §4.2 says hover changes background, and §4.1 has no slot for background@hover
```

**Exit code 1.** A contract that doesn't resolve isn't finished.

**How to respond:** fix it and re-run. These are always typos or genuine contradictions —
here, a misspelled condition, and a chapter 4.2 that promises something chapter 4.1 doesn't
deliver.

---

### Output B — `gap(s)`: the document is fine, the token tree can't answer yet

Four kinds. **Each has a different owner.**

| Gap | Means | Who fixes it | How |
|---|---|---|---|
| `absent-from-tree` | no token exists for this | **token tree owner** | add a token. *Someone has to decide what colour this is* |
| `dimension-unmet` | the token exists, but not for this state or variant | **token tree owner** | add the missing state |
| `ambiguous` | more than one token could fit | **you** | pin one explicitly in the contract |
| `unmapped-leaf` | the resolver can't read a name your tree uses | **you, once** | add a `leaf_map` entry to the context file |

**How to respond:** treat them as a to-do list. Most are real holes in your token system that
the tool just found.

> **Never close a gap by typing a token name that doesn't exist.** A pinned name that isn't in
> the tree fails lint on purpose — it's the one way invented token names get into a design
> system.

---

### Output C — `states`: a question, not a problem

```
states: 3 case(s) keep their rest token, while the tree has this component's own token
for that state — confirm which is intended:
  - APP-01@hover[variant=primary] rest `component.button.variant.primary.background`,
    tree has `component.button.variant.primary.background-hover`
```

Your contract says the background doesn't change on hover. Your token tree has a hover token
for it. One of them is wrong.

**How to respond:** decide which. Either the contract should say hover changes the background,
or that token in the tree is unused and should go.

---

## Step 4 — Write back what the tree answered

```bash
python3 ~/.claude/skills/component-contract/scripts/writeback.py Button/Button.md
```

This fills every `—` the tree could answer, so your contract shows its real tokens:

```
Button.md: nothing to write — every token the tree answers is already stated
```

It never overwrites a token you pinned by hand, and it leaves `—` wherever the tree stayed
silent — those are your gaps.

**Then resolve once more**, so the canonical documents include what was just written:

```bash
python3 ~/.claude/skills/component-contract/scripts/resolve.py Button/Button.md
```

## Step 5 — Generate the readable spec

```bash
python3 ~/.claude/skills/component-contract/scripts/resolve_view.py Button/Button.md
```

Writes `generated/Button.spec.md` — **the file everyone else reads.** It has an *origin* column:

| origin | means |
|---|---|
| *this component* | you decided it. Change it freely |
| *archetype* | a fact about what platforms give free. Changing it means a platform changed |
| *policy* | your design system's cross-cutting commitment |

Read it now. You're checking that the derivation was right: correct role, all the states
present, variants matching your design file. **This is the cheapest moment to catch a mistake.**

## Step 6 — Check what the run taught the system

```bash
python3 ~/.claude/skills/component-contract/scripts/learned.py diff
```

Lists the facts and decisions every later component now inherits.

**On your second component this should be short. By the tenth, usually empty.** A run that
re-asks what an earlier run settled is a bug worth chasing.

## Where to put the files

**Contracts live next to your tokens, not next to any platform's code.** They're the only two
things in a design system that describe it without picking a platform.

```
packages/
├── tokens/
├── contracts/                              ← here
│   ├── .claude/design-system-context.yml
│   ├── policy.md
│   └── Button/
├── react/     consumes contracts/Button/generated/Button.web.json
└── ios/       consumes contracts/Button/generated/Button.ios.json
```

**Separate repos per platform?** Put contracts in the tokens repo and ship `generated/` in the
same release your built tokens ship in. Platform repos already know how to consume that.

**Commit the generated files too.** Re-running must produce identical files, so a pull request
shows exactly which requirements moved — that diff is your review surface.

Don't commit `.resolve-report.json` or `.claude/.context-snapshot.json`. They're tool state.

---

# Part 2 — Implementing and checking a component

*For whoever builds the component.*

## What you were handed

Two things:

1. `generated/Button.spec.md` — the spec, in plain language
2. `generated/Button.<your platform>.json` — the same thing, machine-readable

Plus your design system's token artifact, which you already use.

## Step 1 — Read the resolved view, not the JSON

`Button.spec.md` is written for people. It contains **more** than the contract file does —
everything inherited is resolved into it.

Check the **Token gaps** section first:

```
### Token gaps

*None. Every declared property resolves.*
```

If it says that, every appearance requirement has a real token behind it. If it lists gaps,
those properties are genuinely undecided — ask the design system owner rather than picking
something.

## Step 2 — Build it

Build against the tokens the spec names. Nothing here requires a particular framework — the
contract deliberately refuses to specify one, because what gets checked is what your component
*produces*, not how you produced it.

## Step 3 — Check it

**You need a verifier for your platform.** One is not shipped with the skill, and that's
deliberate: the canonical document is designed so that whoever owns a platform's test tooling
can write a small reader for it.

A verifier does three things:

1. reads `Button.<platform>.json`
2. finds or builds an instance matching each scenario, and observes it
3. declares, in its own `capability.json`, what it **cannot** observe

A worked example lives in [`docs/examples/pipeline/3-verifiers/`](docs/examples/pipeline/3-verifiers/)
— web, iOS and Android. The web one runs today:

```bash
python3 docs/examples/pipeline/3-verifiers/web/verify.py
```

### The four verdicts, and how to respond

```
web-stdlib-static  —  strategy: witness
5 pass / 3 fail / 70 unverified / 5 n-a
================================================================
  FAIL   STR-02   The element carrying the role is <button>.
                  -> Default: carried by <div>, expected <button>
  PASS   BTN-01   The control is exposed to assistive technology as a button.
  PASS   BTN-02   The control has a non-empty accessible name.
  UNVER  BTN-04   Activating by the platform's primary non-pointer input performs the action.
                  -> cannot drive input without a browser
  N/A    APP-09   elevation is not tokenised.
                  -> a Button sits in the content plane
```

| Verdict | Means | What to do |
|---|---|---|
| **PASS** | checked, and it matched | nothing |
| **FAIL** | checked, and it didn't | **fix your component** — or, if you think the contract is wrong, go to Step 4 |
| **UNVER** | *nobody checked this.* The verifier said so in its own words | read the reason. Either it's a real limit of the platform, or your verifier needs to be better |
| **N/A** | this requirement has no meaning here, with a stated reason | nothing |

> **`UNVER` is not a pass.** The whole design exists so that unobservable things are named out
> loud rather than quietly counted as success. A verifier that reports all-green is the bug.

In the example above, `FAIL STR-02` is real: the demo is a `<div role="button">` where the
contract says `<button>`.

## Step 4 — When you disagree with the contract

Sometimes your component is right and the contract is wrong. Run:

```bash
python3 ~/.claude/skills/component-contract/scripts/evidence.py Button/Button.md results.json
```

`results.json` is your verifier's own report. Real output:

```
evidence: 27 question(s) — the implementation disagrees with, or adds to, the tree.
Nothing is changed. For each: is the CONTRACT wrong, the COMPONENT defective, or the
TREE's own statement wrong?

  contradicts (27)
  - foreground@hover [appearance=secondary]: the tree gives `semantic.colorNeutralForeground1`;
    the implementation uses `semantic.colorNeutralForeground1Hover`.
  - border-color [appearance=primary]: the tree gives `semantic.colorTransparentStroke`;
    the implementation uses a literal (transparent).
```

**It changes nothing.** Every line is a question with exactly three possible answers:

| Answer | Means | Who acts |
|---|---|---|
| **contract** | the spec is wrong | design system owner edits the contract |
| **component** | you built it wrong | you fix it |
| **tree** | the token's own description is wrong | token tree owner fixes the tree |

An implementation is **evidence**. Only the token tree and a person are **authority**.

## What your platform can actually check

This differs a lot, and it's better to know before you invest:

| | What a verifier can check |
|---|---|
| **Web** | **everything**, tokens included. A browser keeps `var(--token)` references alive at runtime, so which token a property uses is readable |
| **iOS · Android · macOS** | **accessibility and behaviour only.** A compiled app keeps no token references — a token becomes a colour when the view is drawn. The Appearance chapter reaches native as intent, not as a check |

On a compiled app that means roughly six checkable things: exposed as a button, has an
accessible name, disabled state conveyed, disabled performs no action, label scales with text
size, and meets the minimum touch target. Everything else is reported `unverified`, by name.

---

## Every command, in one place

```bash
S=~/.claude/skills/component-contract

python3 $S/scripts/detect_tokens.py tokens.json            # propose facts about a token tree
python3 $S/scripts/resolve.py     Button/Button.md         # → Button/generated/*.json
python3 $S/scripts/writeback.py   Button/Button.md         # fill in what the tree answered
python3 $S/scripts/resolve.py     Button/Button.md         # again, to pick up the write-back
python3 $S/scripts/resolve_view.py Button/Button.md        # → Button/generated/Button.spec.md
python3 $S/scripts/schema.py      Button/Button.md         # props schema, if you asked for one
python3 $S/scripts/check_generated.py                      # are all contracts still up to date?
python3 $S/scripts/learned.py     diff                     # what this run taught the system
python3 $S/scripts/evidence.py    Button/Button.md results.json
```

Python 3, no dependencies. Everything is written to `Button/generated/`; pass `--out` only if
you want it somewhere else.

---

## Supported platforms

**Web, iOS, Android, macOS.**

**Windows and Linux are not supported.** Their reference material is researched and kept, but
neither is offered by the interview. The reason is specific: there's no verified way to get a
real rendered tree on either, so a contract targeting them could be written but never checked.

## Limits, stated plainly

- **Roles covered so far:** button, link, combobox, heading, text. Dialog, list, checkbox, tab
  and the rest are unbuilt.
- **No verifier ships with the skill.** The examples in `docs/examples/pipeline/3-verifiers/`
  are worked examples; the web one is deliberately weak, and the iOS and Android ones are
  sketches.
- **Nothing checks your design file.** No comparison between Figma and the contract exists, and
  that gap is permanent for now.
- **Nothing does visual regression.** That's a separate field. This checks logic only — which
  element, which token, which state — never a rendered colour or a pixel.
- **The interview path is written but unproven.** The format and the resolver are exercised
  heavily against real design systems; the full run from interview to contract has not been
  done end to end since the format changed.

## More

| | |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | why it's built this way — the six layers, and what each one owns |
| [STATUS.md](STATUS.md) | what works today, with measured numbers |
| [docs/contract-md-format-spec.md](docs/contract-md-format-spec.md) | the contract format, in full |
| [docs/verifier-results-format.md](docs/verifier-results-format.md) | what a verifier writes back, so compliance is a fact about a version (proposed) |
| `references/` | the external standards every derivation is grounded in — WAI-ARIA, WCAG, four HIGs, DTCG |
