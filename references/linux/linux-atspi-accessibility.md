# Linux desktop accessibility and interaction reference

Source of authority: [AT-SPI (Assistive Technology Service Provider Interface)](https://www.freedesktop.org/wiki/Accessibility/AT-SPI2/), the toolkit-agnostic accessibility bus used across the Linux desktop.

**Last verified:** 2026-08-25

**Read this caveat before anything else in the file.** Unlike the other four platforms, "Linux" is not one platform with one component/interaction model — there is no single toolkit or design guidance layer analogous to UIKit+HIG or WinUI+UIA. Two toolkit ecosystems dominate (GTK/libadwaita and Qt/KDE), each with its own component conventions and its own adaptive-layout mechanism, and neither is canonical the way this skill avoids treating Fluent or Material as canonical for their platforms. This file anchors on AT-SPI — the one thing both ecosystems actually implement — and documents the toolkit split explicitly rather than picking a side.

Consulted by SKILL.md's Phase 3 ("Component / structure resolution" section) and Phase 4 ("Accessibility API" section) whenever Q8 includes Linux.

---

## Accessibility API

AT-SPI exposes roles, states, and actions to assistive technology (primarily the Orca screen reader) over D-Bus, independent of which toolkit built the application:
- **Roles** (`ATSPI_ROLE_PUSH_BUTTON`, `ATSPI_ROLE_CHECK_BOX`, `ATSPI_ROLE_RADIO_BUTTON`, `ATSPI_ROLE_TAB`, `ATSPI_ROLE_MENU_ITEM`, etc.) — AT-SPI's role taxonomy predates and closely parallels ARIA's, since both drew on the same accessibility API lineage.
- **States** (`ATSPI_STATE_CHECKED`, `ATSPI_STATE_EXPANDED`, `ATSPI_STATE_SELECTED`, `ATSPI_STATE_SENSITIVE` — the enabled/disabled equivalent) — the state-attribute equivalent of `aria-checked`/`aria-expanded`/`aria-selected`/`aria-disabled`.
- **Accessible name/description** — every interactive element needs one, same "name, role, value" requirement as every other platform in this set.
- Both GTK (natively) and Qt (via the `qt-at-spi` bridge) implement this interface, so a component contract's accessibility requirements (§6) translate to AT-SPI roles/states regardless of which toolkit the target implementation uses.

## Component / structure resolution — toolkit-dependent

Resolve Q2 (action) + Q7 (interaction) to the *AT-SPI role/state the implementation must expose*, same principle as the Windows file resolving to a control pattern rather than a specific XAML class — this keeps the resolution toolkit-agnostic even though the concrete widget differs:

| Action / interaction | Required AT-SPI role | GTK4/libadwaita widget | Qt/KDE widget |
|---|---|---|---|
| Triggers an action | `PUSH_BUTTON` | `GtkButton` | `QPushButton` |
| Toggles a setting | `TOGGLE_BUTTON` / `CHECK_BOX` | `GtkSwitch` / `AdwSwitchRow` | `QCheckBox` |
| Choose one, always visible | `RADIO_BUTTON` | `GtkCheckButton` (radio mode) | `QRadioButton` |
| Choose one, opens on demand | `COMBO_BOX` | `GtkDropDown` | `QComboBox` |
| Opens/closes something, contextual | `DIALOG` | `AdwDialog` / `GtkPopover` | `QDialog` / `QMenu` |

If the target implementation's toolkit isn't known, leave the concrete widget unspecified — the accessibility contract holds regardless of which toolkit ultimately implements it.

**Mapping onto a component contract's §2.1 vs. §6.1:** put the AT-SPI role in §2.1's Role column (e.g. `PUSH_BUTTON`), and the toolkit widget(s) from the table above in §2.1's Tag/Control column — both toolkits side by side (e.g. `GTK: GtkButton / Qt: QPushButton`), or `unspecified — toolkit not known` if it isn't. The AT-SPI role reappears in §6.1's Role/Tag column (that repetition is expected, same as every other platform), where the actual accessible-name/description wiring for whichever toolkit is targeted belongs — that's the part that's genuinely new information in §6.1, not the role itself.

## Layout adaptation (feeds §2.3 Adaptive Layout) — fragmented, document per toolkit

- **GTK/libadwaita**: `AdwBreakpoint` — named, condition-based layout switches tied to the window's width, the closest of the two ecosystems to a container-query-style model.
- **Qt/KDE**: layout managers (`QVBoxLayout`/`QGridLayout`/etc.) combined with manual size-based logic, or QML's anchor-based adaptive layouts — no single named-breakpoint primitive as standardized as `AdwBreakpoint`.

There is no cross-toolkit standard here — if the target implementation's toolkit is known, document adaptive conditions against that toolkit's actual mechanism rather than implying a unified Linux answer.

## RTL (feeds §2.2 Order)

Both toolkits support bidi mirroring natively:
- **GTK4**: layout is direction-aware by default (`gtk_widget_set_direction`), and GTK4's alignment/margin properties use start/end semantics, same logical-vs-physical principle as CSS and Android.
- **Qt**: `QGuiApplication::setLayoutDirection` / `Qt::LayoutDirection`, with Qt Widgets and QML both supporting direction-aware anchoring.

Record §2.2 Order in start/end (logical) terms regardless of toolkit — both resolve it correctly.

## Motion (feeds §4 Appearance)

No single cross-desktop standard: GNOME exposes `org.gnome.desktop.interface enable-animations` via GSettings; KDE Plasma has its own animation-speed setting. The [XDG Settings Portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.impl.portal.Settings.html) is an emerging cross-desktop-environment mechanism sandboxed apps can query instead of reading a specific desktop environment's settings directly — prefer it when targeting Flatpak/sandboxed distribution; fall back to the desktop-specific setting otherwise.
