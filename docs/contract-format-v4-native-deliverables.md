# v4 — one intent, native deliverables

**Status: proposal.** Replaces v3's manifest/adapter/schema-validator machinery.
Supersedes `contract-format-v3-proposal.md` from "How a manifest is produced" onward; v3's
layering (L0 archetypes, L1 policy, L2 contract, divergences, scope) is unchanged and still
the foundation.

## What changed, and why

v3 closed the compiled-app loop by inventing a manifest: the build emits JSON, a schema
validates it. That works, but **it is not how anyone validates a compiled app.** In iOS and
Android the assertion lives in test code and the runner's result *is* the result. Emit-then-
validate exists in those ecosystems only for *conclusions* — SARIF from a linter, JUnit XML
from a runner — never for raw observations someone else adjudicates.

So the manifest was a layer invented to make JSON Schema applicable, and JSON Schema was
never the goal. The goal was one intent, validated per platform.

> **v4: the contract resolves once, then each platform gets the artifact its own build
> already knows how to consume.**

Nothing uniform is imposed on anybody. The uniformity lives upstream, in the contract.

## The pipeline

```
Contract.md  +  archetype (L0)  +  policy (L1)
                      |
                      v
        RESOLVE  (once, platform-neutral)
        resolved requirement set + bindings
                      |
        +-------------+-------------+
        |             |             |
      EMIT          EMIT          EMIT
       web           iOS         Android
```

One resolver, three emitters. The emitters are templates over the same resolved set, so
adding a platform is a template, never a re-derivation of intent.

## What each platform gets

| Platform | API surface | Everything else | Consumed by |
|---|---|---|---|
| **Web** | `Button.schema.json` — JSON Schema | `Button.contract.spec.ts` — Playwright / Vitest + Testing Library | the test runner already in the repo |
| **iOS** | `ButtonContract.swift` — a protocol the component must conform to | `ButtonContractTests.swift` — XCTest / XCUITest | `xcodebuild test` |
| **Android** | `ButtonContract.kt` — an interface | `ButtonContractTest.kt` — JUnit + Compose test rule | `./gradlew test` |
| **macOS** | as iOS | as iOS | as iOS |

### The reframe that makes this simple

**JSON Schema is a web deliverable, not a universal one.** On a compiled platform the type
system *is* the schema, and it is strictly better: it fails at compile time, in the IDE,
with no extra tooling. Asking Swift to validate a JSON document describing its own API is
strictly worse than asking the Swift compiler to check a protocol conformance.

So v1's promise — "a JSON Schema per platform" — is answered by giving each platform its
own equivalent of one, not by giving every platform JSON.

## What a generated check looks like

Same requirement, three idioms, one source.

**BTN-10** — *when disabled, that state is conveyed to assistive technology.*

```ts
// Button.contract.spec.ts — GENERATED from Button.md v1.0. Do not edit.
test('BTN-10 · when disabled, that state is conveyed to assistive technology', async () => {
  const el = await render(<Button label="Save" disabled />);
  expect(await el.getAttribute('aria-disabled')).toBe('true');
});
```

```swift
// ButtonContractTests.swift — GENERATED from Button.md v1.0. Do not edit.
func test_BTN_10_whenDisabled_stateIsConveyedToAssistiveTechnology() throws {
    let view = ButtonView(label: "Save", disabled: true)
    let host = hostForAccessibility(view)
    XCTAssertTrue(host.accessibilityTraits.contains(.notEnabled),
                  "BTN-10 — when disabled, that state is conveyed to assistive technology")
}
```

```kotlin
// ButtonContractTest.kt — GENERATED from Button.md v1.0. Do not edit.
@Test fun BTN_10_whenDisabled_stateIsConveyedToAssistiveTechnology() {
    composeTestRule.setContent { Button(label = "Save", disabled = true) }
    composeTestRule.onNodeWithTag("root").assertIsNotEnabled()
}
```

The requirement id is in the test name, so a CI failure already reads as
`BTN-10 · when disabled, that state is conveyed to assistive technology` with no custom
reporter resolving schema paths back to sentences.

## Three-state results come free

v3 built `unverified` by hand. Every one of these runners already has it.

| v3 concept | Native form |
|---|---|
| pass | test passes |
| fail | test fails |
| unverified — method unavailable | `XCTSkipUnless(...)` · JUnit `Assume.assumeTrue(...)` · Playwright `test.skip()` |
| n/a — scoped or diverged | a **skipped test carrying the reason** |

**Invariant: every requirement emits exactly one test on every platform in scope.** A
requirement that does not bind is emitted as a skipped test whose message is its reason —
never omitted. So the test count is identical across platforms, and alignment is checked by
counting rather than by a bespoke linter. A platform cannot shrink its own bar by
omission, because omission is not expressible.

```
BTN-13 — SKIPPED: n/a — no platform-level form model exists off the web
BTN-05 — SKIPPED: unverified — no hardware keyboard attached
```

Both appear in xcresult, in JUnit XML, in every CI dashboard, with reasons.

## The one honest fork: tokens

Everything above is a test. Token data-flow is not naturally a test — "no literal appears in
a contract-relevant style property" is a **lint rule**, and lint is where each ecosystem
already puts exactly this kind of check.

| Platform | Idiomatic home |
|---|---|
| Web | stylelint config, or a generated ESLint rule |
| iOS | SwiftLint custom rule |
| Android | detekt or Android Lint rule |

A value-comparison test is not a substitute: reading a rendered view's resolved colour and
comparing it to the token's value passes a literal that happens to coincide, which is
exactly the `.opacity(0.4)` case. Source scanning is the right mechanism, and lint is its
native home.

Recommendation: emit lint configuration where the ecosystem supports rule config as data
(stylelint), and a generated test using the platform's syntax library where it does not, with
the lint rule as the stated end state. This is the one place v4 does not yet land cleanly,
and saying so is better than forcing it.

## What this deletes

- the manifest format
- one adapter per platform
- the schema-as-validator, and the reporter mapping schema paths to requirement ids
- the scenario-capture matrix (`captures` keyed by prop configuration × state × condition)
  — a generated test just sets up its own scenario, which is what tests do
- the four manifest sections as a public concept; routing is now an internal emitter detail

## What survives from v3

- L0 archetypes with bundles and per-platform bindings — **bindings are now what the
  emitters read**, and they carry more weight than before
- L1 system policy
- L2 contract, divergences with mandatory reasons, `scope` with the referent rule
- conformance levels, now expressed as which generated suites a repo runs
- the three validation moments — lint, compile, mounted/driven — unchanged; only the
  artifact changed

## The flow, end to end

1. **User answers the interview.**
2. **Generated:** `Button.md`, plus per platform a test suite, an API artifact (schema on
   web, protocol/interface on native), and lint configuration for tokens.
3. **Dropped into the existing test target.** No new runner, no adapter, no new format.
4. **The platform's own runner reports** pass / fail / skipped-with-reason, into the CI
   reporting the team already has.

Cross-platform reporting, if wanted, aggregates xcresult and JUnit XML — which most CI
already does — rather than requiring a bespoke format from everyone.

## Open

1. **Emitter fidelity.** Generated tests must read as idiomatic or they will be rewritten by
   hand, and then drift is back. This is the main risk and it is a craft problem, not an
   architectural one.
2. **Generated code in the repo.** Same discipline as generated schemas: generated-only,
   header says so, CI regenerates and diffs.
3. **Test harness assumptions.** The emitter must know how a component is mounted in this
   repo — a Storybook story, a preview, a factory. That is per-repo configuration, probably
   in `.claude/design-system-context.yml`.
4. **Does the interview change?** No.
