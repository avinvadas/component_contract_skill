# Verifier results — the format, and what a verifier must echo

Status: **proposed**. No verifier implements this yet.

A verifier reads a per-platform document and reports what it observed. This specifies what it
writes back, so that **compliance becomes a fact about a version rather than a fact about a
moment**.

---

## The problem this solves

Today a results file says:

```json
{ "verifier": "web-chrome", "contract": "Button", "platform": "web", "results": [ … ] }
```

Component name and platform. **No version.** So nothing anywhere records *"this build was
compliant with Button v1.2 on web"* — only that something called Button passed something, once.
For a design system versioning a component across product environments, that is not a usable
claim: a product cannot say which contract it satisfies, and the design system cannot tell which
products a change would break.

## A compliance claim has four parts

All four are required. Drop any one and the claim stops being checkable later.

| | Answers | Supplied by |
|---|---|---|
| **the document** | compliant with *what* | the canonical document |
| **the subject** | *what* was observed | the verifier's runner |
| **the verifier** | observed *how*, and what it could not see | the verifier |
| **the moment** | *when* | the verifier |

### The document, not just the contract version

`contract_version` alone does **not** identify a requirement set. A document is the contract
*plus* its archetype, its policy and its token tree, and a contract does not pin its archetype
version — deliberately, because an archetype states what a platform provides for free, and if
the platform changed you want the new fact. So two documents can both say `1.0` and hold
different requirements.

Therefore a result carries **both**: `contract_version` for people, and `document_digest` for
machines. The digest is exact, cannot be forgotten to bump, and is what tells you later whether
the document that was verified is the document you now hold.

---

## The format

```json
{
  "format_version": "1.0",

  "contract": "Button",
  "platform": "web",
  "contract_version": "1.0",
  "document_digest": "sha256:9f2c…",
  "generated_from": "Button.md v1.0 + archetype button v1.0 + system policy. Do not edit.",

  "subject": {
    "name": "@fluentui/react-components",
    "version": "9.54.0",
    "ref": "git:4a91c2e"
  },

  "verifier": {
    "name": "web-chrome",
    "version": "1.0",
    "strategies": ["witness"],
    "cannot_observe": {
      "announcement": "does not capture what a screen reader would speak",
      "name-provenance": "reads the computed name, not which node supplied it"
    }
  },

  "produced_at": "2026-09-21T14:03:11Z",

  "summary": { "pass": 236, "fail": 0, "unverified": 2, "n_a": 4 },

  "results": [
    { "id": "STR-02", "status": "PASS", "statement": "…", "detail": "…" },
    { "id": "BTN-11", "status": "UNVERIFIED", "statement": "…",
      "detail": "headless Chrome cannot establish touch_input" }
  ]
}
```

### Field by field

| Field | Required | Notes |
|---|---|---|
| `format_version` | yes | this spec's version, so a consumer can refuse what it cannot read |
| `contract`, `platform` | yes | unchanged from today |
| `contract_version` | yes | copied from the document's `contract_version` |
| `document_digest` | yes | `sha256:` of the canonical document file, as bytes, unmodified |
| `generated_from` | yes | copied verbatim from the document. Readable provenance, names the archetype version |
| `subject` | yes | what was observed. `name` required; `version` and `ref` strongly encouraged — a claim about an unidentified build is not much of a claim |
| `verifier.name`, `.version` | yes | which tool, which revision of it |
| `verifier.cannot_observe` | yes | copied from its `capability.json`. **A result from a weak verifier and a strong one are not the same claim**, and this is what makes the difference legible |
| `verifier.strategies` | yes | `witness` / `construct` |
| `produced_at` | yes | ISO 8601, UTC. A compliance claim with no date ages badly |
| `summary` | yes | all four counts. See below |
| `results` | yes | unchanged. `observed` stays as it is — `evidence.py` reads it |

Everything already present keeps its meaning. This is **additive**: a consumer reading only
`results` is unaffected.

---

## There is no `compliant: true`

Deliberately, and this is the part most likely to be "simplified" later.

A single boolean would have to be derived from the counts, and the only honest derivation is
*no failures* — which makes a verifier that observes almost nothing report the same green as one
that checks everything. That is the exact failure the whole project is built to prevent:
**unobservable is said out loud, never passed.**

So a claim is the counts, and any sentence a tool writes from them must carry the unverified
number with it:

> compliant with **Button v1.0** on **web** — 236 checked, 0 failed, **2 unverified**
> (touch target, user text-size), verified by web-chrome 1.0 against @fluentui/react-components 9.54.0

The same rule that governs a verifier's own report governs the summary of it.

---

## What each verifier has to do

Six things, all cheap. Five of the six come from files it already opens.

1. Copy `contract_version` and `generated_from` from the document it is already reading.
2. Hash the document file's bytes → `document_digest`.
3. Copy `cannot_observe` and `strategies` from its own `capability.json`.
4. Name itself and its own version.
5. Stamp `produced_at`.
6. **Accept a `subject`** — the one genuinely new input. A verifier cannot discover what it is
   driving; its runner must be told, from a package version, a git ref, a build id.

Nothing here requires reading the contract, the token tree, or anything the verifier does not
already have.

---

## What the skill does with it

`scripts/evidence.py` turns observations into questions. Those questions are only meaningful
against the document the run actually observed, so it gains a provenance check:

- **digest matches** the current document → proceed as today.
- **digest differs** → refuse. The questions would be derived from a document that no longer
  exists, and answering them would edit a contract on the strength of a stale run.
- **no digest** (a pre-format-1.0 file) → warn once, proceed. Migration, not a wall.

**Implemented.** Exit 2 on a refusal — not 1, so a caller cannot mistake a refused run for a
report it can act on. `--force` overrides, for when the difference provably cannot affect what
was observed.

That check is the reason to adopt this at all: without it, nothing stops an old results file
producing confident, wrong questions.

---

## What this does not do

- **It does not decide whether a change is breaking.** That is answerable from two documents
  rather than from results — `check_generated.py`'s `summarise()` already computes added and
  removed requirement ids, which is the input such a rule needs. Requirements **added** mean
  implementations that passed may now fail; requirements **removed** loosen. Related, separate.
- **It does not make a native run mean more than it does.** A compiled app still cannot report
  token references, so its `unverified` count stays large and honest, and `cannot_observe` says
  why in the verifier's own words.
- **It does not store history.** Where these files live, and for how long, belongs to whoever
  runs the verifier.
