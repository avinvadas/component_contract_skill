# Native event and callback models

Sources of authority: Apple's [Swift](https://developer.apple.com/documentation/swift/) and [Combine](https://developer.apple.com/documentation/combine) documentation (iOS/macOS), Android's [Kotlin](https://kotlinlang.org/docs/lambdas.html) and [Jetpack Compose](https://developer.android.com/jetpack/compose) documentation plus [Kotlin Flow](https://kotlinlang.org/docs/flow.html), Microsoft's [.NET events](https://learn.microsoft.com/en-us/dotnet/standard/events/) and [WinUI routed events](https://learn.microsoft.com/en-us/windows/apps/develop/base-controls/events) documentation, and GNOME's [GObject Signals](https://docs.gtk.org/gobject/concepts.html#signals) alongside Qt's [Signals & Slots](https://doc.qt.io/qt-6/signalsandslots.html) documentation.

**Last verified:** 2026-08-26

This is the native-platform counterpart to `references/web/dom-events-model.md` — how §5.3 Events Emitted / §5.4 Events Received are grounded for iOS, Android, macOS, Windows, and Linux. It differs from that file in one important way: the DOM has exactly one event model. Every platform below has **more than one live idiom**, and none of them has a single canonical spec the way `CustomEvent` does — these are documented language/framework conventions, not one standard. Don't pick a favorite and present it as *the* answer; name the idiom actually in use, or document the fork explicitly, the same way `references/linux/linux-atspi-accessibility.md` refuses to pick GTK or Qt as canonical.

Consult this file from **Phase 5** whenever a §5.3/§5.4 row is for a platform other than Web.

---

## iOS / macOS (shared — both are Apple platforms, both commonly built in SwiftUI)

- **Closures** — a callback passed as a parameter (`Button(action: {})`, a completion handler `(Result<T, Error>) -> Void`). The default idiom for SwiftUI-first components; if the contract's target is SwiftUI, describe emitted events as a named closure parameter with its argument type.
- **Delegate protocols** — a protocol the parent conforms to (`UITableViewDelegate`-style, or a custom `protocol ModalDelegate: AnyObject { func modalDidDismiss() }`). The long-standing UIKit/AppKit idiom; use this when the target is UIKit (iOS) or AppKit (macOS), not SwiftUI.
- **`NotificationCenter`** — broadcast, decoupled, one-to-many. Appropriate only for events that genuinely have no single owning parent to call back — most component-level events aren't this; don't reach for it by default.
- **Combine publishers** (`@Published`, `PassthroughSubject`) — for a continuous stream of values rather than a single discrete event (e.g., a live-updating value as the user drags a slider, not just its final committed value).
- **macOS only — target-action** (`NSButton.target` / `.action`, a `Selector`) — an older Cocoa convention, AppKit-specific, with no iOS equivalent. Only relevant for AppKit components, not SwiftUI ones.

For a component contract: state which idiom applies given the target framework (SwiftUI vs. UIKit/AppKit) — don't assume SwiftUI by default without checking, since a design system's iOS/macOS implementation may still be UIKit/AppKit-based.

## Android

- **Lambda callbacks** — a function-typed parameter (`onClick: () -> Unit`, `onValueChange: (String) -> Unit`). The default idiom for Compose; if the contract's target is Compose, describe emitted events as a named lambda parameter with its argument type.
- **Listener interfaces** (`View.OnClickListener`, a custom `interface OnDismissListener { fun onDismiss() }`) — the View-system idiom, predates Compose. Use this when the target is the classic View system, not Compose.
- **`Flow`** — for a continuous stream of values (analogous to Combine on Apple platforms) rather than a single discrete event.
- **`LiveData`** — an older lifecycle-aware reactive holder, still common in View-system codebases; being superseded by `Flow` in Compose-first code but still worth naming if that's what a target codebase actually uses.

## Windows

- **Routed events** (`RoutedEventHandler`, e.g. `Click`) — XAML-specific, and unlike a plain .NET event, these bubble or tunnel through the visual tree, so a parent can listen without the child wiring anything explicitly for it. This is the default idiom for a WinUI/XAML component contract, consistent with the routed, tree-aware behavior already assumed elsewhere in `references/windows/windows-ui-automation.md`.
- **Classic .NET events** (`event EventHandler<T> SomethingHappened`, subscribed via `+=`) — the plain CLR idiom, no visual-tree bubbling. Use this only if the target isn't XAML (a non-UI .NET library component, for instance) — most component contracts on this platform should default to routed events instead.

## Linux (GTK vs. Qt — no cross-toolkit standard, same fork as the rest of the Linux reference material)

- **GTK: GObject signals** — `g_signal_connect()` in C, or a language binding's equivalent (e.g. PyGObject's `widget.connect("clicked", callback)`). A signal is emitted by name and any number of listeners can connect to it.
- **Qt: signals and slots** — `connect(button, &QPushButton::clicked, receiver, &Receiver::onClicked)` (or `object.clicked.connect(slot)` in PyQt/PySide). Compile-time (C++) or duck-typed (Python binding) connection between a signal and a slot method.

Document whichever toolkit the target implementation actually uses — same rule as the rest of the Linux reference file: don't imply a unified answer where the ecosystem genuinely forked.

---

## Writing the §5.3/§5.4 row

Whichever idiom applies, state it in plain language with the concrete signature/name — not DOM vocabulary borrowed from the Web row, and not a generic "the component emits an event" that doesn't say how. For example, an Android/Compose row for a dismiss event: `onDismiss: () -> Unit` — a lambda parameter, called with no arguments when the component is dismissed. That's the same level of concreteness the Web row gets from being grounded in `CustomEvent`, just expressed in this platform's own idiom instead.
