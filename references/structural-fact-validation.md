# Structural-fact validation — checking rendered output against §2.1, §2.2, and §6

Source of authority: none external — like `token-naming-validation.md`, this is a synthesized mechanism, not a citation. It exists because §2.1 (root element), §2.2's Order/Position, and §6.1–§6.3 (roles, attributes, keyboard, focus) are all facts the props schema (Phase 6's existing `.schema.json`) structurally cannot see — it validates a consumer-supplied instance's shape, and none of these are consumer-supplied values.

**Last verified:** 2026-09-06

## This checks rendered output. It never reads source code.

An earlier version of this file checked source text — grepping an implementation's `.kt`/`.js` file for a literal construct. That's wrong, for the same reason this skill's own "Native platform technology as the stated level" section already states elsewhere: **we don't control how a component is built, only what it needs to produce.** A contract is satisfied by React, vanilla JS, SwiftUI, UIKit, or a framework nobody's invented yet, as long as the *outcome* matches — and outcome lives in the rendered DOM or the runtime accessibility tree, never in source text. Checking source assumes a specific implementation shape the contract explicitly refuses to require, and it breaks on anything the contract is actually supposed to tolerate: a different framework, a minified bundle, different internal naming, a vendored component with no visible source at all. It also proves less than it looks like it proves even when source *is* available — matching text doesn't confirm a conditional branch didn't route around it at runtime.

So every check below runs against a live, running instance of the component — the same real device/simulator/browser artifact this skill's blind-implementation testing already produces — never against a file on disk.

## Step 1 — extract the expected fact list directly from the contract

Unchanged from before: §2.1 (root Tag/Control), §2.2 (Order/Position), §6.1–§6.3 (roles, attributes, keyboard triggers, focus targets) already state the exact, platform-standard construct expected, derived from HIG/Material/WAI-ARIA references in Phase 3/4 — not invented per design system, so there's nothing to detect or lock the way token-name validation needed. This produces `[Component].[Platform].structure.json`, generated from the contract the same way the props schema is:

```json
{
  "rootElement": { "expect": "tag=dialog" },
  "order": [
    { "zone": "icon" },
    { "zone": "title" }
  ],
  "accessibility": [
    { "fact": "title is a heading", "expect": "role=heading" },
    { "fact": "close control has an accessible name", "expect": "accessibleName=Close" }
  ]
}
```

No regex patterns this time — the expectations are role/attribute/tag facts about a tree, not string shapes to match in a file.

## Step 2 — obtain the real rendered tree, per platform

| Platform | How to get a real tree to check |
|---|---|
| Web | The live DOM, from an actual running instance in a real or headless browser — `document.querySelector(...)`, `getAttribute(...)`, computed ARIA role. Framework-agnostic by construction: React, Vue, or hand-written JS all end up as the same DOM once rendered, and this reads what's actually there, not what produced it. |
| Android | The real on-screen accessibility node tree, from a booted emulator/device running the actual built app — `adb shell uiautomator dump` (an XML snapshot: class, content-desc, and the on-screen child order). Never Kotlin source. |
| iOS | The real accessibility hierarchy, from a booted simulator/device running the actual built app — XCUITest's `app.debugDescription` (a full accessibility-tree dump) or the Accessibility Inspector's underlying snapshot. Never Swift source. |

This is real infrastructure, not a file read — the app has to actually be running. That cost is inherent to the thing being verified, not a shortcut this file is skipping: there is no way to know what a component's outcome is without producing that outcome at least once.

**Verified by hand against Modal's real Android implementation — `uiautomator dump`'s real ceiling, not a hypothetical one.** Run for real against a booted emulator showing the Full variation: presence and order came through cleanly — every `content-desc` in the tree was empty (correctly confirming Android's superseded no-close-button fact), and the icon (`"ℹ"`) and title (`"Update available"`) TextViews appeared as index 0 and 1 of the same parent, in that order, read directly with no ambiguity. Two things did not come through:
- **§6.1 heading semantics has no representation in this dump format at all.** Compose's `Modifier.semantics { heading() }` doesn't surface as any attribute on any node in `uiautomator dump`'s XML schema — not a value to check, an attribute that plain doesn't exist there. Confirming this fact for Android needs Compose's own `onRoot().printToLog()` semantics dump, which only runs from inside a real Espresso/Compose instrumented test — a genuinely bigger infrastructure lift than an `adb shell` command, not a tooling detail to paper over.
- **§2.1 root element didn't self-identify.** `dumpsys window windows` showed two windows, both attributed to the host `MainActivity` — consistent with a real Compose `Dialog` (its window is parented to the hosting Activity, not separately titled), but nothing in the output says "Dialog" outright. Confirming root-element identity on Android this way needs a before/after window-count comparison (one window with the modal closed, two with it open), not a single snapshot with a self-describing field.

**Verified by hand against Modal's real iOS implementation — a harder wall than a missing permission.** macOS's Accessibility API requires the calling process to be granted Accessibility permission (`AXIsProcessTrusted`) before it can inspect another app's UI at all — a real, one-time, human-only grant (System Settings → Privacy & Security → Accessibility), not something any amount of scripting works around. Once granted, though, a second and deeper wall showed up: walking the Simulator app's own `AXUIElement` window tree reaches only the *Simulator's own chrome* (its hardware-button representations, its toolbar) — the guest iOS app's actual screen renders as a single opaque `AXScrollArea` with zero children, confirmed two ways (a plain top-down child walk, and `AXUIElementCopyElementAtPosition` hit-testing directly into the screen area). This isn't a missing permission or a wrong query — Accessibility Inspector reaches this content through a separate, private protocol that isn't exposed through the public `AXUIElement` API this file's mechanism has access to. **Closing §2.1/§2.2/§6.1 for iOS for real needs actual XCUITest infrastructure** — `app.debugDescription`, which only exists inside a real Xcode UI-test target attached to the running app — not a cleverer command-line query. A hand-compiled `swiftc` binary with no Xcode project, the way this session's iOS test app was built, has no such target to attach to; this is the same category of gap as Android's instrumented-test requirement for heading semantics, just one level further out.

**This paid off immediately once built.** Generating a real `.xcodeproj` (via `xcodegen`, from a plain YAML spec — no hand-written `pbxproj`) with an app target and a UI-testing target, then running `xcodebuild test` against the booted simulator, surfaced a genuine accessibility regression in Modal's own SwiftUI source that no amount of visual or screenshot checking this whole session had caught: the sheet's container had `.accessibilityLabel(title)` applied without `.accessibilityElement(children: .contain)` to scope it, so the label bled down to every descendant lacking a stronger label of its own. The real, running tree showed it plainly — the close button, "Cancel", and "Save" all reported `label: 'Update available'` (the modal's *title*) instead of their own names. Visually, all three buttons looked completely correct (✕, "Cancel", "Save" all rendered as expected) — this defect only exists in the accessibility tree, invisible to sighted verification by construction, which is the whole reason this file's mechanism has to read that tree directly rather than infer accessibility correctness from how something looks. Scoping the container with `.accessibilityElement(children: .contain)` fixed it; the same real test run, re-executed, confirmed all three buttons back to their correct, distinct names.

## Step 3 — presence check, against the tree

For every entry outside `order`: does a node with the expected tag/role/attribute exist anywhere in the real tree? A miss is a direct, unambiguous finding — the contract states this is required, and the running component didn't produce it. No severity nuance needed — presence in the actual output is binary.

## Step 4 — order check, against the tree's real child order

For `order` entries: find the smallest common ancestor node containing all the listed zones in the real tree, and read its children's actual order directly — no reasoning about how that order was constructed is needed, because the tree already reflects the finished result. This is simpler than checking source ever could be: a real DOM has exactly one child order at any moment, however it got there (`appendChild`, `insertBefore`, a virtual-DOM diff, anything else) — there's nothing left to disambiguate. If the zones' real order doesn't match §2.2's stated order, that's a direct finding.

## What this deliberately does not check

This confirms the right node exists, with the right role/attribute, in the right position, in what actually rendered — it does not confirm a screen reader announces it in a way a user finds clear, or that a focus call visibly lands where a sighted user expects. Those stay qualitative, real-device judgment calls, not something a tree snapshot alone settles.

## Extending to §5.3/§5.4 and the declaration half of §6.2

The same tree-based principle extends to whether a contract-declared event actually fires and a key handler actually produces its effect — but note this is now a *stronger* claim than the presence check above, not the same one downgraded to source. Checking that `onDismiss` fires means actually triggering the dismissal path on the real running instance and observing the callback happen — exactly the tap-and-observe verification already used elsewhere in this skill's real-device testing, not a static check of any kind.
