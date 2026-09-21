# Using the skill, beginning to end

A practical walkthrough for someone contracting a component for the first time. It follows
what actually happens when the skill runs, in order, and says what you are expected to do at
each point.

For *why* it is built this way, read [ARCHITECTURE.md](../ARCHITECTURE.md). For what is and is
not finished, read [STATUS.md](../STATUS.md). This file is the operator's manual.

---

## Before you start

**You need three things.** None of them has to be perfect, and the skill will tell you which
are missing rather than guessing.

| | What it is | If you don't have it |
|---|---|---|
| A **token tree** | the design system's tokens — DTCG JSON, Style Dictionary, CSS custom properties, or Tailwind `@theme` | the contract still resolves; every token slot comes back as a gap addressed to whoever owns the tree |
| A **component in mind** | a name, a purpose, and how people interact with it | this is the interview's subject; there is nothing to do without it |
| Somewhere for the output to live | a directory for contracts in the design system's own repo | you are asked once, and the answer is recorded so no later component asks again |

**You do not need** to know HTML, ARIA, native accessibility APIs, or any platform's
interaction conventions. Those are derived, not asked. If you find yourself being asked a
technical question about markup or ARIA, that is a defect.

**Run it from the design system's repository**, not from the skill's. The skill works *on* a
repo from wherever it is installed; it reads `.claude/design-system-context.yml` and the token
tree relative to your working directory.

---

## The shape of a run

```
Phase 0   pre-flight        mostly automatic — reference freshness, design-system facts, file locations
Phase 1   interview         10 questions, one at a time
Phase 2   token extraction  from a Figma link, a coded reference, or your description
Phase 3   derive structure  internal — never asked
Phase 4   derive a11y       internal — never asked
Phase 5   write contract    the six-chapter .md and its bindings
Phase 6   resolve           canonical documents, the resolved view, and the questions that remain
```

Phases 3 and 4 are where the skill earns its keep: everything technical is derived from plain
answers about purpose and interaction.

---

## Phase 0 — pre-flight

Three checks run before anything is asked. All are cheap; occasionally one does real work.

**0A — reference freshness.** Every file under `references/` carries a `Last verified:` date.
Anything 90 days or older is re-checked against the standard it cites, *if* web access is
available. If a spec has materially changed, the run stops and tells you which file is
affected before the interview starts. This check never blocks you — a skipped or inconclusive
check is always a reason to proceed.

**0B — design-system facts.** The skill looks for `.claude/design-system-context.yml`.

- **It exists** → loaded silently. Its facts seed defaults for everything that follows.
- **It doesn't** → the skill *detects first*: it scans for a token file, platform manifests,
  and existing contracts, then runs `detect_tokens.py` on whatever tree it found. It proposes
  tiers (from the direction aliases point, not from group names) and naming patterns (from the
  observed shapes of paths), each with its evidence. **You confirm; it never guesses silently.**
  Anything left over is asked in one batched question, up to four at a time.

What you may be asked here: token file format and prefix, whether token values are ever
hand-typed in components or strictly generated downstream, the per-platform framework
(SwiftUI vs. UIKit, Compose vs. Views), naming casing, and RTL support.

What you will *never* be asked here: the naming convention's separator, case or prefix. That
is detected empirically from a real generated name the first time it is needed, then locked.

**0C — where this design system's files live.** The contracts directory and the policy file.
Asked once, recorded, never asked again.

> The context file belongs in the design system's repo and should be committed. It is shared
> team context, not scratch state.

---

## Phase 1 — the interview

Ten questions, one at a time, each waiting for your answer. Conditional follow-ups don't count
toward the ten. The order goes general → specific, matching the contract's own chapter order.

| | Question | Feeds |
|---|---|---|
| **Q1** | What's it called, and what problem does it solve? | ch. 1 Intent |
| **Q2** | Which platforms? (Web · iOS · Android · macOS) | scope — how many rows every later table needs |
| **Q3** | What does it do? | role derivation (with Q4) |
| **Q4** | How do people interact with it? | role derivation (with Q3); the one path that feeds ch. 5 directly |
| **Q5** | Does it stand alone, or hold other components? | ch. 3 Composition |
| **Q6** | What are its visible parts, and what is each for? | ch. 3 Zones |
| **Q7** | Which visual styles does it have? | ch. 4.3 Visual variants |
| **Q8** | Can its layout change? | ch. 2.3 Layout props |
| **Q9** | Which extra states does it have? Do you have tokens for it? | ch. 4 Appearance |
| **Q10** | Want a JSON props schema alongside the contract? | output |

**Two things worth knowing while answering.**

*Use your own vocabulary.* Every question with system-internal language (variant names, state
names) lets you rename any option by typing the correct name. The contract should read in your
design system's words, not in the skill's.

*There is no question about behaviour or accessibility.* That is the whole premise. Chapters 5
and 6 are derived from Q3 and Q4 in Phases 3 and 4. If the derivation is wrong, you correct it
in Phase 5, but you are never asked to specify ARIA.

---

## Phase 2 — token extraction

Three paths, depending on what you gave at Q9:

| Path | Input | What happens |
|---|---|---|
| **A** | a Figma URL | tokens read from the file's variables and normalised against the recorded naming pattern |
| **B** | a coded reference — Storybook, CSS, a tokens file | read and normalised the same way |
| **C** | a description only | slots are written as `—` and resolved from the tree in Phase 6 |

Path C is not a lesser path. `—` means *resolve it from the tree*, which is what you want in
most cases: the tree is the authority, and writing a token name by hand is how invented names
enter a design system.

---

## Phases 3 and 4 — derived, not asked

Nothing is asked here. The skill derives:

- the **role-archetype** (`button`, `link`, `combobox`, `heading`, `text`) from Q3 + Q4 — which
  brings in what every platform already guarantees for that role, so the contract never
  restates it;
- **which element carries the role** on each platform (ch. 2.4);
- **ARIA roles and attributes**, keyboard navigation, focus management, and screen-reader
  expectations (ch. 6).

If a platform convention is cited, it is cited and confirmed — never applied as a silent
default.

---

## Phase 5 — the contract is written

You get a six-chapter markdown file plus a `.bindings.json`.

| | Chapter | Holds |
|---|---|---|
| 1 | Intent | what it is, what need it solves |
| 2 | Structure | what the thing is, the space it occupies, and **which element carries the role** (2.4) |
| 3 | Composition | what it contains, and on what terms |
| 4 | Appearance | token slots (4.1), interaction states (4.2), visual variants (4.3), platform tokens (4.4) |
| 5 | Behavior | events, props, and the state machine if it owns moving state |
| 6 | Accessibility | semantic exposure, reviewable as an aspect in its own right |

**What to check when you read it:**

- **Nothing inherited is restated.** If a requirement is true of every component with this
  role, it belongs in the archetype; if true of every component in the system, it is policy.
  A local id colliding with an inherited one fails the parse.
- **2.4 and 4.2 are never empty** when the component has a role with interaction states. They
  are where every platform's element and every valid state are answered.
- **`—` in a token slot means "resolve from the tree."** Write an explicit token only to pin
  one deliberately — and a pinned name not in the tree is a parse failure, by design.
- **A slot covers every variant** unless it says otherwise. One row becomes one case per
  variant value. To make one variant differ, add a row for that value only.
- **A property that doesn't change in a state keeps its rest token.** `nothing` is refused,
  because it meant three different things in three different places.

---

## Phase 6 — resolve

Four commands, in this order, once per component:

```bash
python3 <skill>/scripts/resolve.py      Button/Button.md --out Button/canonical
python3 <skill>/scripts/writeback.py    Button/Button.md
python3 <skill>/scripts/resolve.py      Button/Button.md --out Button/canonical
python3 <skill>/scripts/resolve_view.py Button/Button.md
```

The tree is the authority, so what it answers goes into the contract without asking:
`writeback.py` replaces each `—` the tree answers with the token — or, where each variant has
its own, with the pattern they share (`component.button.{kind}-hover`) plus an override row for
every value that breaks it — and fills each row's `scope`. It never touches a pinned token or
an `n/a`. **A finished contract shows its real tokens; a remaining `—` is always a gap.**

### Three kinds of output, and they are not the same

| | Means | What to do |
|---|---|---|
| **lint** | the *document* is malformed — unknown condition, missing binding, pinned token not in the tree, a machine cell with two answers | **fix and re-run.** Exits non-zero. A contract that doesn't resolve isn't finished |
| **token gaps** | the document is fine; the *token tree* can't express something yet | report by kind and who fixes it. **Never** fix it by inventing a token name |
| **machine closure** | how many generated checks the state machine implies | nothing — information, not a finding |

The four gap kinds and who owns each:

| Gap | Owner | Fix |
|---|---|---|
| `absent-from-tree` | token tree owner | add a token |
| `dimension-unmet` | token tree owner | add a state or variant |
| `ambiguous` | contract author | pin one |
| `unmapped-leaf` | context file | add a `leaf_map` entry — **never a new token**, since one may exist under a spelling nobody mapped |

### Then act on the report

Run with `--report Button/.resolve-report.json` and work through it before finishing. This is
where the design system's own layer grows, one component at a time:

- **`shared_unconfirmed`** — a shared group has a token for a case this component left open.
  Membership is never assumed; you are asked, and on yes the component joins the group and the
  row resolves with `scope: shared:<group>`.
- **`policy_to_ask`** — policy rows this component *engages*. A Button raises token discipline,
  focus indicator and touch-target floor; it never raises loading conventions. Each is asked
  with **defer** as a real option. A deferred row is not re-asked, but stays visible in the
  report.
- **`unmapped-leaf` questions** — property spellings the resolver can't read, asked lazily
  because this component needs them.

Re-run until lint is zero and nothing is left to ask. Then:

```bash
python3 <skill>/scripts/learned.py diff
```

This reports what the run taught the design system — the facts, policy decisions and
archetypes every later component now inherits. **On the second component this list should be
short; by the tenth, usually empty. A run that re-asks what an earlier run settled is a
defect**, and it is tested.

---

## What you end up with

```
Button/
├── Button.md                          authored — commit this
├── Button.bindings.json               authored — commit this
└── generated/                         nothing here is edited by hand
    ├── Button.spec.md                 the artifact a person reads
    ├── Button.web.json                one per platform
    ├── Button.ios.json
    └── Button.web.schema.json         only if Q10 asked for one
```

The first two are source. The rest are generated, and regenerating must produce identical
files — **a diff after a re-run means the contract changed, not the tooling.**

`.resolve-report.json` and `.claude/.context-snapshot.json` are tool state. Add them to
`.gitignore` rather than committing them.

---

## Where the files go in your design system

**One rule: contracts live next to the tokens, not next to any platform's code.**

Tokens and contracts are the only two things in a design system that describe it *without*
picking a platform. They belong together, and they get distributed the same way.

**If your design system is a monorepo:**

```
packages/
├── tokens/                  the token tree
├── contracts/               ← contracts go here
│   ├── .claude/design-system-context.yml
│   ├── policy.md
│   └── Button/
├── react/                   consumes contracts/Button/generated/Button.web.json
└── ios/                     consumes contracts/Button/generated/Button.ios.json
```

**If your platforms are in separate repos:** put contracts in the tokens repo, and ship the
`generated/` files in the same release the built tokens ship in. Platform repos already know
how to consume a token release; the canonical documents ride along with it. Don't copy files
between repos by hand.

**Commit the generated files too.** Everything in `generated/` is build output, but committing
it makes the diff the review surface: a pull request shows exactly which requirements moved.
Re-running must produce identical files, so a diff nobody expected means the contract changed.

| File | Commit? | Who owns it |
|---|---|---|
| `Button.md`, `Button.bindings.json` | yes — source | the designer who ran the interview |
| `policy.md` | yes — source | the design system's lead, decided once |
| `.claude/design-system-context.yml` | yes — source | whoever owns the tokens |
| everything in `generated/` | yes — generated | nobody. Regenerated, never edited |
| `.resolve-report.json` | no | tool state |

**The verifier does not go here.** It lives in the platform's own repo, next to that
platform's tests, because it belongs to that platform's toolchain.

---

## How a designer uses them

Four files come out. Only one of them is for you:

| File | Who reads it |
|---|---|
| **`Button.spec.md`** | **you** — the full spec in plain language |
| `Button.md` | you, to make changes |
| `generated/*.json` | machines — the verifier and the engineer's build |
| `*.schema.json` | build tooling |

### 1. Read the resolved view and check the derivation

`Button.spec.md` is the spec. It has everything — including the requirements the archetype
and the policy contributed, which don't appear in `Button.md` at all. The **origin** column
tells you what is yours to change:

| origin | means |
|---|---|
| *this component* | you decided it in the interview. Change it freely |
| *archetype* | a fact about what platforms give you free. Changing it means a platform changed |
| *policy* | your design system's cross-cutting commitment |

Read it before anyone builds anything. You are checking that the derivation was right: is the
role correct, are all the states there, do the variants match your Figma file? **This is the
cheapest moment to catch a mistake.**

### 2. Work the gap table

The Token gaps section is your to-do list, and most of it is design work, not engineering:

| Gap | What it means | Who decides |
|---|---|---|
| `absent-from-tree` | the tree has no token for this | **a designer** — what *is* the ghost variant's hover colour? |
| `dimension-unmet` | the token exists but not for this state or variant | **a designer** |
| `ambiguous` | more than one token could fit | **you** — pin one |
| `unmapped-leaf` | the resolver can't read a spelling your tree uses | whoever owns the context file, once |

A clean contract says *None. Every declared property resolves.* Until it does, the gaps are
real holes in your token system that the tool just found for you. **Never close a gap by
typing a token name that doesn't exist** — that is how invented names get into a design system.

### 3. Hand off

Give the engineer the canonical file for their platform and the token artifact. That's it.
**The document is the handoff** — there is nothing to explain in a meeting, and if there is,
the contract is missing something and should be fixed instead.

### 4. Answer the questions after it's built

Once a verifier has run against the real component:

```bash
python3 <skill>/scripts/evidence.py Button/Button.md results.json
```

It lists where the built component **disagrees** with the token tree. **Change nothing
automatically.** Each one is a question for you, with three possible answers:

- the **contract** is wrong → edit it
- the **component** is defective → report it to the engineer
- the **tree's** own statement is wrong → fix it in the tree

An implementation is evidence. Only the tree and you are authority.

### What not to do

- **Don't edit `Button.spec.md` or anything in `generated/`.** They're regenerated; your
  edits vanish.
- **Don't invent a token name** to make a gap go away.
- **Don't hand-write ARIA or markup into the contract.** It's derived. If it's wrong, the
  derivation is wrong, and that's worth fixing at the source.

### One thing this does not do

Nothing checks your Figma file against the contract. The resolved view is readable enough to
review a design against by eye, but that comparison is manual, and always will be.

---

## What a verifier can and cannot tell you

The skill's output ends at the canonical document. Verification belongs to whoever owns that
platform's toolchain, and how much it can actually check differs sharply by platform:

- **Web** — the whole contract, including every token row, because a browser keeps
  `var(--token)` references alive at runtime.
- **Compiled native (iOS, Android, macOS)** — the accessibility and behaviour half only. A
  compiled app keeps no token references, so the Appearance chapter travels to native as
  intent, not as a check.

A verifier declares its own limits, and anything it cannot observe is reported `unverified` by
name — never passed. See [STATUS.md](../STATUS.md) for the measured numbers.

---

## The second component, and the tenth

The point of the design-system layer is that it accumulates. By the time you contract your
tenth component:

- Phase 0B asks nothing — the facts are recorded.
- Policy rows are mostly decided; only genuinely new ones are raised.
- `leaf_map` covers the spellings your tree uses.
- Shared groups know their members.
- `learned.py diff` prints little or nothing.

If that is not what you see, something is failing to write back, and it is worth chasing
rather than working around.

---

## Known limits

Stated plainly so nobody is surprised:

- **Role-archetypes are tier 1 only** — button, link, combobox, heading, text. Dialog, list,
  checkbox, tab and the rest are unbuilt.
- **Windows and Linux are not supported.** Their reference material is sound but isn't wired
  into the interview, because there is no verified way to obtain a real rendered tree for
  either — a contract targeting them could be written but never checked.
- **iOS, Android and macOS verifiers are sketches**, not runnable tools.
- **There is no conformance suite for verifiers** — nothing yet proves a new verifier is honest
  about its own declared limits.
- **The skill has not been run end to end against a real design system since the format
  rewrite.** The resolver and the format are exercised heavily; the interview path is written
  but unproven.
