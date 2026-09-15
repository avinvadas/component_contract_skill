---
archetype: text
version: 1.0
platforms: [web, ios, android, macos]
kind: native-backed
---

# Archetype: text

Content read as text. The thinnest archetype in the library, and deliberately so.
## Native backing

What each platform provides. `none` means every implementation builds the semantics by hand — the requirements below still bind.

| Platform | Native backing |
|---|---|
| web | any text-bearing element |
| ios | SwiftUI `Text` · `UILabel` |
| android | Compose `Text` · `TextView` |
| macos | SwiftUI `Text` · `NSTextField` |


| when | statement | observe | kind | chapter | source | id |
|---|---|---|---|---|---|---|
| always | The content is available to assistive technology as text. | name | state | Accessibility | catalogue:Web/text · catalogue:iOS/Text | id-TXT-01 |
| always | The content scales with the platform's user text-size setting. | state | state | Appearance | catalogue:iOS/Button | id-TXT-02 |

## A near-empty bundle is a valid outcome

Two requirements. That is not an oversight — text genuinely gets almost nothing free beyond
being read, and the scope rule forbids padding a bundle with things that merely seem
important.

The temptation here is to add truncation behaviour, line-height, contrast, or maximum
measure. **None of those is provided automatically by any platform**, so none belongs in an
archetype. They are either system policy — contrast and measure usually are — or
component-local facts. Putting them here would turn a factual inventory into a house style,
which is the failure mode the scope rule exists to prevent.
