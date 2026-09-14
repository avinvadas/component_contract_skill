# The validation flow as it currently stands

**Status of this document: the design, not the implementation.** What is actually built is
listed at the bottom, and it is a short list.

## The flow

```
Interview
   |
   v
Contract.md  +  archetype (L0)  +  policy (L1)
   |
   v
RESOLVE  ->  requirement set + bindings        (once, platform-neutral)
   |
   +--> EMIT per platform, into two tiers:
        |
        |-- COMPILE tier  : an API artifact the compiler enforces
        |                   + source-level checks (tokens, wiring)
        |
        '-- MOUNTED tier  : a generated test suite in the platform's own
                            framework, plus one call to that platform's
                            first-party accessibility audit
   |
   v
The platform's own runner reports pass / fail / skipped-with-reason
```

Nothing uniform is imposed downstream. The uniformity is upstream, in the contract.

## Tier 1 — compile

Enforced by the compiler. No runner, no device, errors appear in the IDE.

| Platform | API artifact | Source-level checks |
|---|---|---|
| Web | `Button.schema.json` + TS types | stylelint config (POL-04); ESLint rule |
| iOS | `ButtonContract.swift` — a protocol | Swift macro, or a build-phase SwiftSyntax pass |
| Android | `ButtonContract.kt` — an interface | KSP processor, or detekt rule |
| macOS | as iOS | as iOS |
| **Windows** | `IButtonContract.cs` — a C# interface | **Roslyn analyzer** |

**Covers:** the API chapter entirely, the Appearance/tokens chapter entirely, and
necessary-condition proxies elsewhere — e.g. *a component declaring a `disabled` prop must
wire it to the platform's disabled mechanism*, which is what would have caught the
`.opacity(0.4)` defect before any test ran.

**Cannot cover:** anything depending on rendered output or elapsed time. A compiler sees
source. Nothing in Structure, Behaviour, or most of Accessibility is reachable.

**A limit worth stating precisely:** a source check confirms the *usual mechanism is
present*, not that the outcome holds. Applying `.disabled()` to the wrong subview satisfies
the check and fails the requirement. Tier 1 catches absence, not incorrectness.

Windows is the strongest tier-1 platform of the five: Roslyn analyzers are more mature than
Swift macros and ship as ordinary NuGet packages.

## Tier 2 — mounted

A generated suite in the platform's own framework, run by the platform's own runner.

| Platform | Runner | Mount in isolation | Driven / real app | First-party a11y audit |
|---|---|---|---|---|
| Web | Vitest / Playwright | jsdom *(no layout, no computed names)* or headless Chrome | Playwright | **axe-core** (`jest-axe`, `@axe-core/playwright`) |
| iOS | XCTest / XCUITest | `UIHostingController`, or ViewInspector — **untested here** | XCUITest, Simulator | **`app.performAccessibilityAudit()`** — Xcode 15+ |
| Android | JUnit + Compose test rule | Robolectric — JVM, no device | instrumented test | **ATF** via `AccessibilityChecks.enable()` |
| macOS | XCTest / XCUITest | `NSHostingView` | XCUITest | `performAccessibilityAudit()` — verify macOS availability |
| **Windows** | xUnit / NUnit / MSTest | WinUI test host — **least settled of the five** | FlaUI or Appium Windows driver over UIA | **Axe.Windows** (NuGet, scriptable) |

### Delegate generic accessibility to the platform audit

These audits are generic rule engines — "every element has a label", "contrast is
sufficient", "the hit target is big enough". They know nothing about a specific component,
but they already cover part of every archetype bundle:

| Archetype requirement | Already covered by |
|---|---|
| BTN-02 — non-empty accessible name | `.sufficientElementDescription` · ATF · axe · Axe.Windows |
| BTN-11 — minimum touch-target size | `.hitRegion` · ATF · axe |
| BTN-12 — label scales with user text size | `.dynamicType`, `.textClipped` |

Roughly a third of the `button` bundle. The binding should mark those `covered_by: audit`
and the emitter should call the audit once rather than writing three bespoke assertions that
are worse-maintained than the vendor's.

What the audits cannot know — the title is a heading, zones are in this order, this token
feeds this property, dismissal emits this event — is the generated suite's actual job.

## Windows, specifically

The repo currently scopes Windows out, on the grounds that there is *"no verified way to
obtain a real rendered tree."* Under this design that reason is weaker than it was:

- **UI Automation is a genuine normalization layer.** WinUI 3, WPF, WinForms and MAUI all
  speak it, so one adapter covers every stack. `AutomationId` is a first-class zone tag.
- **Axe.Windows exists** and is scriptable, so the generic-audit delegation works.
- **Roslyn gives the strongest tier 1 of any platform here.**

The real Windows risk is different from the one recorded: it is not tree access, it is that
the **driven-tier tooling is the least settled**. WinAppDriver was archived by Microsoft,
with Appium's Windows driver as the continuing path, and the WinUI in-process test-host story
is thinner than Compose's or SwiftUI's. So Windows could plausibly reach conformance level 1
and much of level 2 today, with level 3 the uncertain part — which is exactly the
partial-support shape the level model was built for.

**This should be re-verified before acting on it.** The original blocker was recorded from
hands-on work; this reassessment is not.

## Results

Every runner above already has three states, so nothing custom is needed:

| Meaning | Native form |
|---|---|
| pass | test passes |
| fail | test fails |
| unverified — method unavailable | `XCTSkipUnless` · JUnit `Assume` · Playwright `test.skip()` |
| n/a — scoped or diverged | a skipped test carrying its reason |

**Invariant:** every requirement emits exactly one test on every platform in scope. One that
does not bind is emitted as a skipped test with its reason, never omitted — so test counts
match across platforms, and a platform cannot shrink its own bar by omission.

---

## What is actually built

Almost none of the above.

| Built | Status |
|---|---|
| Token-naming validation harness | run for real; three defects found and fixed |
| Generation/eval harness with provenance | run for real, Opus vs Sonnet compared |
| Contract invariants | run; these lint generated artifacts, not implementations |
| Modal on Android — `uiautomator dump` | **run by hand once.** Presence and order worked; Compose semantics and root identity did not |
| Modal on iOS — XCUITest via a generated `.xcodeproj` | **run by hand once.** Found a real accessibility defect invisible to visual inspection |
| `docs/examples/button/` | runnable, but demonstrates the **superseded** v3 manifest architecture |

| Not built | |
|---|---|
| Any emitter, for any platform | — |
| Any generated test suite | — |
| Any protocol / interface / analyzer artifact | — |
| The resolver (parsing `Button.md` into a requirement set) | the example hand-transcribes it |
| Anything on macOS or Windows | — |

**Unverified assumptions this design rests on**, in rough order of how much depends on them:

1. `UIHostingController` / Robolectric can carry the `mounted` tier — never tried here.
2. `app.debugDescription` may or may not expose enough trait detail; if not, iOS needs two
   structure extractors.
3. Generated tests will read as idiomatic enough that nobody rewrites them by hand. This is
   the main risk in the whole design and it is a craft problem, not an architectural one.
4. The Windows reassessment above.
