---
archetype: heading
version: 1.0
platforms: [web, ios, android, macos]
kind: native-backed
---

# Archetype: heading

Text that labels the section following it, and that assistive technology can navigate between.

| id | statement | observe | kind | required | source |
|---|---|---|---|---|---|
| HDG-01 | The text is exposed to assistive technology as a heading. | role | state | always | catalogue:Web/headings · catalogue:iOS/header-trait · catalogue:Android/heading |
| HDG-02 | The text is reachable by the platform's heading navigation. | focus | state | always | catalogue:Web/headings |
| HDG-03 | The text has a non-empty accessible name. | name | state | always | catalogue:Web/headings |

## Level is deliberately not a requirement

This archetype states that something *is* a heading and never what level it is.

iOS's header trait is **binary** — there is no level concept to bind to. A requirement naming
a level would need `binds: false` on iOS for no gain, and a platform-shaped exclusion where a
neutral statement was available is a defect in the requirement, not an honest exclusion.

Level is also a property of the *document a component is mounted in*, which a component
contract cannot know. Platforms with no level concept satisfy HDG-01 **fully**, not
approximately.

This entry exists as the worked instance of the rule: *state a requirement at the abstraction
level where every platform has a referent.*

## Deliberate drops

| Free behaviour | Dropped because |
|---|---|
| contributes to the document outline | an outline is a property of a document, not of a component, and exists on no platform but the web. Scoping it to web would make it a requirement about the page rather than the component. |
