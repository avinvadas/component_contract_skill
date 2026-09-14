---
archetype: text
version: 1.0
platforms: [web, ios, android, macos]
kind: native-backed
---

# Archetype: text

Content read as text. The thinnest archetype in the library, and deliberately so.

| id | statement | observe | kind | required | source |
|---|---|---|---|---|---|
| TXT-01 | The content is available to assistive technology as text. | name | state | always | catalogue:Web/text · catalogue:iOS/Text |
| TXT-02 | The content scales with the platform's user text-size setting. | state | state | always | catalogue:iOS/Button |

## A near-empty bundle is a valid outcome

Two requirements. That is not an oversight — text genuinely gets almost nothing free beyond
being read, and the scope rule forbids padding a bundle with things that merely seem
important.

The temptation here is to add truncation behaviour, line-height, contrast, or maximum
measure. **None of those is provided automatically by any platform**, so none belongs in an
archetype. They are either system policy — contrast and measure usually are — or
component-local facts. Putting them here would turn a factual inventory into a house style,
which is the failure mode the scope rule exists to prevent.
