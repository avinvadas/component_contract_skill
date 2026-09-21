#!/usr/bin/env python3
"""Logic checks for the skill's own reasoning. Standard library only.

    python3 scripts/test_scripts.py

Each check hands a script a small input — a token tree, a contract — and asserts the CONCLUSION
it reaches: which tier a token is in, which token a slot binds, which question is asked. Nothing
is rendered and no value is compared; like everything in this project, it validates logic.
Each names the wrong conclusion it rules out, several of which the skill once reached.
"""
import re, contextlib, io, json, pathlib, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
PIPE = ROOT / "docs/examples/pipeline"
FIXTURE = ROOT / "evals/fixtures/tokens/design-tokens.json"
ALT = ROOT / "evals/fixtures/tokens/alt-naming.tokens.json"

results = []


def test(fn):
    try:
        fn()
        results.append(("PASS", fn.__name__, ""))
    except AssertionError as e:
        results.append(("FAIL", fn.__name__, str(e)))
    except Exception as e:  # noqa: BLE001 — a crash is a failure, reported as one
        results.append(("FAIL", fn.__name__, "%s: %s" % (type(e).__name__, e)))
    return fn


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


# ---- the move to scripts/ changed nothing ---------------------------------------------
@test
def pipeline_outputs_match_committed():
    """Guards: scripts moved out of docs/examples silently producing different output."""
    with tempfile.TemporaryDirectory() as out:
        for c in ("Button", "IconButton", "Combobox"):
            r = run(HERE / "resolve.py", PIPE / "1-contract" / (c + ".md"), "--out", out)
            assert r.returncode == 0, "%s resolve failed:\n%s" % (c, r.stdout[-400:] + r.stderr[-400:])
            for f in pathlib.Path(out).glob(c + ".*.json"):
                committed = PIPE / "2-generated" / f.name
                assert f.read_text() == committed.read_text(), "%s differs from committed" % f.name
            view = pathlib.Path(out) / (c + ".spec.md")
            r = run(HERE / "resolve_view.py", PIPE / "1-contract" / (c + ".md"), "--out", view)
            assert r.returncode == 0, "%s view failed: %s" % (c, r.stderr[-400:])
            assert view.read_text() == (PIPE / "2-generated" / (c + ".spec.md")).read_text(), \
                "%s view differs" % c


@test
def archetype_comes_from_the_contract():
    """Guards: resolve.py once hardcoded button.md, and Combobox would have inherited Button."""
    with tempfile.TemporaryDirectory() as out:
        run(HERE / "resolve.py", PIPE / "1-contract/Combobox.md", "--out", out)
        doc = json.loads((pathlib.Path(out) / "Combobox.web.json").read_text())
        ids = {r["id"] for r in doc["requirements"]}
        assert "CBX-01" in ids and not any(i.startswith("BTN-") for i in ids), sorted(ids)


# ---- design-system facts ------------------------------------------------------------
ALT_CONTEXT = """\
tokens:
  source: tokens.json
  tiers:
    primitive: core
    semantic: semantic
    component: component
  patterns:
    component:
      - "component.{component}.{variant}.{property}.{state}"
      - "component.{component}.{property}"
    semantic:
      - "semantic.{*}.{property}.{*}"
  leaf_map:
    bgColor: background
    textColor: foreground
    cornerRadius: radius
    paddingX: padding-inline
    fg: foreground
    corner: radius
"""


def alt_design_system(context_text):
    """A throwaway design-system repo: the Button contract, the alt tree, a context file."""
    d = pathlib.Path(tempfile.mkdtemp())
    shutil.copytree(PIPE / "1-contract", d / "contracts")
    shutil.copy(ALT, d / "tokens.json")
    md = d / "contracts/Button.md"
    text = md.read_text()
    # The tree comes from the context now, and the radius pin names a token only the
    # original fixture has — both must be removed, or the test is not about the context.
    text = "\n".join(l for l in text.splitlines() if not l.startswith("tokens:")) + "\n"
    # The example contract states ITS tree's tokens, written back from it. Moved onto another
    # tree, it starts over: every cell `—`, as before any write-back — which is what this is about.
    text = re.sub(r"\| `[^`]+` \| (?:component|semantic|shared:[\w-]+) \|", "| — | — |", text)
    md.write_text(text)
    if context_text is not None:
        (d / ".claude").mkdir()
        (d / ".claude/design-system-context.yml").write_text(context_text)
    return d


def slots_of(repo):
    with tempfile.TemporaryDirectory() as out:
        r = run(HERE / "resolve.py", repo / "contracts/Button.md", "--out", out)
        doc = json.loads((pathlib.Path(out) / "Button.web.json").read_text())
    # Slots expand per variant now; these tests are about the default variant's resolution.
    reqs = {x["id"].replace("[variant=primary]", ""): x for x in doc["requirements"]
            if x["id"].startswith("APP-") and "[" not in x["id"].replace("[variant=primary]", "")}
    return r, reqs


@test
def facts_resolve_an_unfamiliar_naming_convention():
    """Guards: the resolver only ever working on the one fixture it was written against."""
    r, reqs = slots_of(alt_design_system(ALT_CONTEXT))
    assert "lint: 0 finding" in r.stdout, r.stdout[-600:]
    want = {"APP-01": "component.button.primary.bgColor.default",
            "APP-02": "component.button.primary.textColor.default",
            "APP-05": "component.button.cornerRadius",
            "APP-06": "component.button.paddingX",
            "APP-07": "component.button.primary.bgColor.hover"}
    for rid, token in want.items():
        assert reqs[rid].get("expect") == {"equals": token}, "%s: %s" % (rid, reqs[rid])
    assert reqs["APP-08"]["pending"]["reason"] == "dimension-unmet", reqs["APP-08"]


@test
def without_facts_nothing_is_bound_and_nothing_is_called_absent():
    """Guards: an unreadable tree telling its owner to ADD tokens that already exist."""
    # The realistic case: the design system points at its tree, but has not yet declared how
    # that tree is named. (No tree at all is a different failure, and lint-fails the parse.)
    _, reqs = slots_of(alt_design_system("tokens:\n  source: tokens.json\n"))
    for rid in ("APP-01", "APP-02", "APP-05", "APP-07"):
        assert "expect" not in reqs[rid], "%s bound without facts: %s" % (rid, reqs[rid])
        assert reqs[rid]["pending"]["reason"] == "unmapped-leaf", "%s: %s" % (rid, reqs[rid]["pending"])
        detail = reqs[rid]["pending"]["detail"]
        assert all(d.startswith("component.") for d in detail), \
            "detail must be example PATHS, never a guessed spelling like `default`: %s" % detail


@test
def a_wrong_fact_is_lint_not_silence():
    """Guards: a mistyped context mis-resolving every component without a word."""
    bad = ALT_CONTEXT.replace("bgColor: background", "bgColor: backgroud").replace(
        "primitive: core", "primitive: kore")
    r, _ = slots_of(alt_design_system(bad))
    assert r.returncode != 0, "a wrong fact must fail the parse"
    assert "backgroud" in r.stdout and "kore" in r.stdout, r.stdout[-600:]


@test
def policy_location_is_a_recorded_fact():
    """Guards: every contract restating a relative path to the one policy file."""
    repo = alt_design_system(ALT_CONTEXT + "  \ncontracts:\n  policy: contracts/design-system/policy.md\n")
    md = repo / "contracts/Button.md"
    md.write_text("\n".join(l for l in md.read_text().splitlines() if not l.startswith("policy:")) + "\n")
    _, reqs = slots_of(repo)          # resolves at all == the contract parsed
    with tempfile.TemporaryDirectory() as out:
        r = run(HERE / "resolve.py", md, "--out", out)
        doc = json.loads((pathlib.Path(out) / "Button.web.json").read_text())
    assert "lint: 0 finding" in r.stdout, r.stdout[-400:]
    assert "POL-02" in {x["id"] for x in doc["requirements"]}, "policy not inherited from the context"


@test
def role_archetype_none_is_an_answer_not_a_gap():
    """Guards: a Card, which conveys no distinct role, having nowhere to say so."""
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "Card.md").write_text("""---
component: Card
version: 1.0
role-archetype: none
platforms: [web]
---

# Component Contract: Card

## 1. Intent

A surface that groups related content.

## 2. Structure

| when | statement | observe | kind | id |
|---|---|---|---|---|
| always | The surface does not exceed the inline size of its container. | layout | state | id-STR-01 |

## 3. Composition

## 4. Appearance

## 5. Behavior

## 6. Accessibility
""")
    (d / "Card.bindings.json").write_text(json.dumps(
        {"contract": "Card", "bindings": {"STR-01": {"web": {"expect": {"max_ratio": 1.0}}}}}))
    with tempfile.TemporaryDirectory() as out:
        r = run(HERE / "resolve.py", d / "Card.md", "--out", out)
        assert r.returncode == 0, r.stdout[-500:] + r.stderr[-500:]
        doc = json.loads((pathlib.Path(out) / "Card.web.json").read_text())
        assert doc["role-archetype"] == "none", doc["role-archetype"]
        assert {x["id"] for x in doc["requirements"]} == {"STR-01"}, doc["requirements"]
        v = run(HERE / "resolve_view.py", d / "Card.md", "--out", pathlib.Path(out) / "Card.spec.md")
        assert v.returncode == 0, v.stderr[-500:]


# ---- accumulation: the second component benefits from the first -------------------------
C = lambda v: {"$type": "color", "$value": v}  # noqa: E731
ACC_TREE = {
  "core": {"color": {"purple": {"$type": "color", "$value": "#4C00A8"},
                     "white":  {"$type": "color", "$value": "#FFFFFF"},
                     "gray":   {"$type": "color", "$value": "#E5E7EB"}}},
  "semantic": {"color": {"bg": {"strong": {"$type": "color", "$value": "{core.color.purple}"},
                                "subtle": {"$type": "color", "$value": "{core.color.gray}"}},
                         "fg": {"inverse": {"$type": "color", "$value": "{core.color.white}"}}}},
  "component": {
    "button": {"primary":   {"bgColor":   {"default": C("{semantic.color.bg.strong}")},
                             "textColor": {"default": C("{semantic.color.fg.inverse}")}},
               "secondary": {"bgColor":   {"default": C("{semantic.color.bg.subtle}")},
                             "textColor": {"default": C("{semantic.color.fg.inverse}")}}},
    "chip":   {"bgColor":   {"default": {"$type": "color", "$value": "{semantic.color.bg.subtle}"}},
               "textColor": {"default": {"$type": "color", "$value": "{semantic.color.fg.inverse}"}}}}}

ACC_CONTEXT = """\
tokens:
  source: tokens.json
  tiers:
    primitive: core
    semantic: semantic
    component: component
  patterns:
    component:
      - "component.{component}.{variant}.{property}.{state}"
      - "component.{component}.{property}.{state}"
contracts:
  policy: design-system/policy.md
"""


def acc_contract(name, archetype, extra=""):
    return """---
component: %s
version: 1.0
role-archetype: %s
platforms: [web, ios]
---

# Component Contract: %s

## 1. Intent

A test component.

## 2. Structure

%s
## 3. Composition

## 4. Appearance

### 4.1 Token slots

| when | property | token | id |
|---|---|---|---|
| always | background | — | id-APP-01 |
| always | foreground | — | id-APP-02 |
%s
## 5. Behavior

## 6. Accessibility
""" % (name, archetype, name, ACC_ELEMENT if archetype == "button" else "",
       extra + (ACC_STATES if archetype == "button" else ""))

ACC_ELEMENT = """| platform | element | id |
|---|---|---|
| web | `<button>` | id-STR-01 |
| ios | SwiftUI `Button` | id-STR-02 |
"""

ACC_STATES = """
### 4.2 Interaction states

| state | what changes | driven by |
|---|---|---|
| hover | — | platform |
| focus-visible | — | platform |
| pressed | — | platform |
| disabled | — | prop |
"""


def acc_resolve(repo, name):
    report = repo / ("%s.report.json" % name)
    with tempfile.TemporaryDirectory() as out:
        r = run(HERE / "resolve.py", repo / "contracts" / (name + ".md"), "--out", out,
                "--report", report)
    return r, json.loads(report.read_text())


@test
def the_second_component_asks_nothing_the_first_settled():
    """Guards: the design system's layer not accumulating — every component re-asking
    the same spellings and the same policy decisions, forever."""
    repo = pathlib.Path(tempfile.mkdtemp())
    (repo / "contracts").mkdir()
    (repo / "design-system").mkdir()
    (repo / ".claude").mkdir()
    (repo / "tokens.json").write_text(json.dumps(ACC_TREE))
    (repo / ".claude/design-system-context.yml").write_text(ACC_CONTEXT)
    # Phase 0C: the policy is scaffolded from the shipped template, every row undecided.
    shutil.copy(ROOT / "system/templates/policy.template.md", repo / "design-system/policy.md")
    variant = ("\n### 4.3 Visual variants\n\n| prop | type | required | default | description |\n"
               "|---|---|---|---|---|\n| `variant` | enum:primary,secondary | no | `primary` | emphasis |\n")
    (repo / "contracts/Button.md").write_text(acc_contract("Button", "button", variant))
    (repo / "contracts/Chip.md").write_text(acc_contract("Chip", "none"))

    run(HERE / "learned.py", "snapshot", "--context", repo / ".claude/design-system-context.yml")

    # ---- component A: the first contact with this design system -------------------
    r, a = acc_resolve(repo, "Button")
    assert not a["lint"], "a scaffolded, undecided policy must not break a contract: %s" % a["lint"]
    unmapped = {g["property"] for g in a["token_gaps"] if g["status"] == "unmapped-leaf"}
    assert unmapped == {"background", "foreground"}, a["token_gaps"]
    asked = {e["id"] for e in a["policy_to_ask"]}
    assert asked == {"POL-01", "POL-02", "POL-03", "POL-04"}, \
        "a Button on web+ios engages token discipline, focus, touch target, literal denial: %s" % asked

    # ---- the person answers; the skill records each answer where it belongs --------
    ctxf = repo / ".claude/design-system-context.yml"
    ctxf.write_text(ctxf.read_text().replace("contracts:",
        "  leaf_map:\n    bgColor: background\n    textColor: foreground\ncontracts:"))
    pol = repo / "design-system/policy.md"
    text = pol.read_text()
    for rid, decision, statement in (
            ("POL-01", "token discipline", "Every value that can resolve through a token does."),
            ("POL-02", "focus indicator", "A focused control renders a visible focus indicator."),
            ("POL-03", "touch-target floor", "Every touch target meets the platform minimum."),
            ("POL-04", "literal denial", "deferred — 2026-09-18")):
        old_row = next(l for l in text.splitlines() if l.endswith("id-%s |" % rid))
        cells = [c.strip() for c in old_row.strip().strip("|").split("|")]
        cells[2] = statement
        text = text.replace(old_row, "| " + " | ".join(cells) + " |")
    pol.write_text(text)
    (repo / "design-system/policy.bindings.json").write_text(json.dumps({"bindings": {
        rid: {p: {"expect": {"equals": True}} for p in ("web", "ios")}
        for rid in ("POL-01", "POL-02", "POL-03")}}))

    # ---- component B: a different component, a different token scope ----------------
    r, b = acc_resolve(repo, "Chip")
    assert not b["lint"], b["lint"]
    still_unmapped = [g for g in b["token_gaps"] if g["status"] == "unmapped-leaf"]
    assert not still_unmapped, "spellings mapped for Button were asked again for Chip: %s" % still_unmapped
    assert not b["policy_to_ask"], "decided policy asked again: %s" % b["policy_to_ask"]
    assert [e["id"] for e in b["policy_deferred"]] == ["POL-04"], \
        "a deferred row must stay visible without being re-asked: %s" % b["policy_deferred"]

    # ---- and the run can say what it learned ------------------------------------------
    d = run(HERE / "learned.py", "diff", "--context", ctxf)
    for expected in ("tokens.leaf_map.bgColor = background", "POL-01", "POL-03",
                     "POL-04 literal denial: deferred"):
        assert expected in d.stdout, "learned.py did not report %r:\n%s" % (expected, d.stdout)


# ---- a real design system's shape: Carbon ---------------------------------------------
@test
def carbon_shaped_tree_reads_correctly_and_never_binds_across_variants():
    """Guards four failures the lab found on @carbon/themes, each invisible on the fixtures:
    tiers split across files; component values that exist only per THEME; names that carry
    no property; and — worst — a primary button's text colour bound to the tertiary button's,
    because narrowing by variant once fell back to the un-narrowed list when it came up empty."""
    from tokens import Tree
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "palette.json").write_text(json.dumps({
        "blue": {"60": {"$type": "color",
                        "$value": {"colorSpace": "srgb", "components": [0, 0.4, 1], "hex": "#0f62fe"}}},
        "gray": {"30": {"$type": "color", "$value": "#c6c6c6"}}}))
    (d / "theme.json").write_text(json.dumps({
        "text-on-color": {"$type": "color", "$value": "{gray.30}"}}))
    (d / "button.json").write_text(json.dumps({"button": {
        "primary":  {"$type": "color", "$extensions": {"carbon.themes": {"white": "{blue.60}"}}},
        "tertiary": {"$type": "color", "$extensions": {"carbon.themes": {"white": "{blue.60}"}}},
        "disabled": {"$type": "color", "$extensions": {"carbon.themes": {"white": "{gray.30}"}}}}}))
    facts = {"sources": {"primitive": ["palette.json"], "semantic": ["theme.json"],
                         "component": ["button.json"]},
             "theme": {"name": "white", "value_path": ["$extensions", "carbon.themes", "{theme}"]},
             "readings": {"component.button.primary":  {"property": "background", "variant": "primary"},
                          "component.button.tertiary": {"property": "foreground", "variant": "tertiary"},
                          "component.button.disabled": {"property": "background", "state": "disabled"}}}
    t = Tree(str(d), facts)
    assert not t.problems, t.problems
    # tiers from files; themed values read; aliases rewritten across files
    assert t.tokens["component.button.primary"]["value"] == "{primitive.blue.60}", \
        t.tokens["component.button.primary"]
    # a DTCG 2025 colour object is a value, never an alias
    assert "primitive.blue.60" not in t.alias, "a colour object was read as an alias"
    assert t.resolve("background", \
        "button", {"variant": "primary"})[:2] == ("component.button.primary", "bound")
    assert t.resolve("background", "button", {"variant": "primary"}, "disabled")[:2] == \
        ("component.button.disabled", "bound"), "a token for every variant must stay eligible"
    tok, status, _ = t.resolve("foreground", "button", {"variant": "primary"})
    assert tok != "component.button.tertiary", "bound a primary button's text to the TERTIARY button's"


# ---- a real design system's shape: Primer ---------------------------------------------
@test
def primer_shaped_tree_asks_per_spelling_and_per_component():
    """Guards what @primer/primitives exposed: 358 per-token questions where ~10 spelling
    questions belonged; a Carbon-style fused name (`background-blue`) mistaken for a pure
    spelling; a state repeated across one token family counted as vocabulary; `accent` read
    as a property because the first of two same-depth templates won; and every component's
    naming questions asked at setup, when only one component is being documented."""
    import detect_tokens
    from tokens import pure_property_spelling, Tree
    assert pure_property_spelling("bgColor", "color") and pure_property_spelling("fgColor", "color")
    assert not pure_property_spelling("background-blue", \
        "color"), "fused property+variant is a reading, not a spelling"

    d = pathlib.Path(tempfile.mkdtemp())
    tok = lambda v: {"$type": "color", "$value": v}
    (d / "p.json").write_text(json.dumps({"base": {"blue": tok("#00f"), "gray": tok("#888")}}))
    (d / "s.json").write_text(json.dumps({"control": {"bg": tok("{base.gray}")}}))
    (d / "c.json").write_text(json.dumps({
        "button": {v: {"bgColor": {"rest": tok("{control.bg}"), "hover": tok("{base.blue}")},
                       "iconColor": {"rest": tok("{base.gray}")}} for v in ("default", "primary", "danger")},
        "progressBar": {"track": {"bgColor": tok("{base.gray}")},
                        "bgColor": {"accent": tok("{base.blue}"), "danger": tok("{base.blue}")}},
        "notification": {"action-hover": tok("{base.blue}"), "action-active": tok("{base.blue}"),
                         "action": tok("{base.blue}")}}))
    ctx = {"tokens": {"sources": {"primitive": ["p.json"], "semantic": ["s.json"], "component": ["c.json"]}}}
    out = detect_tokens.detect(str(d), ctx)
    leaf = {q["about"] for q in out["questions"] if q["about"].startswith("leaf_map.")}
    assert "leaf_map.bgColor" in leaf and "leaf_map.iconColor" in leaf, leaf
    per_token = [q for q in out["questions"] if q["about"].startswith("readings.component.button")]
    assert not per_token, "a recurring spelling became a question per token: %s" % per_token
    assert "leaf_map.action" not in leaf, "one token family in three states is not vocabulary"
    assert all(q["components"] is not None for q in out["questions"] if q["about"].startswith("patterns")), \
        "a pattern about one component must be asked when that component is contracted, not at setup"

    t = Tree(str(d), dict(ctx["tokens"], patterns={"component": [
        "component.progressBar.{*}.{property}", "component.progressBar.{property}.{*}"]}))
    assert t.base_state("component.progressBar.bgColor.accent")[0] == "bgColor", \
        "read `accent` as the property; the template whose property slot READS must win"


# ---- token logic, as the rendered page applies it ------------------------------------------
@test
def css_variables_are_a_token_tree_and_a_theme_overrides_root():
    """Guards shadcn: tokens that exist only as CSS custom properties, and a `.dark` theme that
    redefines some names and inherits the rest from `:root`."""
    from tokens import Tree
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "index.css").write_text(":root {\n  --primary: oklch(0.2 0 0);\n  --ring: var(--primary);\n"
                                 "  --radius: 0.625rem;\n}\n.dark {\n  --primary: oklch(0.9 0 0);\n}\n")
    light = Tree(str(d), {"sources": {"semantic": ["index.css"]}, "theme": {"selector": ":root"}})
    dark = Tree(str(d), {"sources": {"semantic": ["index.css"]}, "theme": {"selector": ".dark"}})
    assert light.tokens["semantic.primary"]["value"] == "oklch(0.2 0 0)"
    assert light.tokens["semantic.primary"]["type"] == "color"
    assert light.tokens["semantic.ring"]["value"] == "{semantic.primary}", "var(--x) must read as an alias"
    assert dark.tokens["semantic.primary"]["value"] == "oklch(0.9 0 0)"
    assert dark.tokens["semantic.radius"]["value"] == "0.625rem", \
        ".dark must inherit what it does not redefine"


@test
def tailwind_declares_its_tokens_in_at_theme_not_root():
    """Rules out: calling a token absent that the tree declares — Tailwind v4 (and shadcn on top
    of it) puts radius, type and spacing in `@theme`, and only colours in `:root`."""
    from tokens import load_css
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "t.css").write_text("""@import "tailwindcss";
@theme inline {
  --radius-md: calc(var(--radius) * 0.8);
  --text-sm: 0.875rem;
}
:root { --radius: 0.625rem; --primary: oklch(0.2 0 0); }
.dark { --primary: oklch(0.9 0 0); }
""")
    light = load_css(str(d / "t.css"))
    assert set(light) == {"radius-md", "text-sm", "radius", "primary"}, sorted(light)
    assert light["text-sm"]["$type"] == "dimension" and light["primary"]["$type"] == "color"
    dark = load_css(str(d / "t.css"), ".dark")
    assert dark["primary"]["$value"] != light["primary"]["$value"], "a theme selector overrides :root"
    assert "radius-md" in dark, "a theme inherits what it does not redefine"


@test
def token_slots_are_non_overlapping_cases_with_web_names_and_stated_transforms():
    """Guards two things a real verifier exposed on Carbon and shadcn: a default token slot
    that also claimed the disabled and hovered instance (and so failed exactly where the page
    was right), and a canonical document too platform-neutral to be checked in a browser — no
    web variable name, and no way to state `primary at 80%`."""
    import resolve
    conv = {"row": "kebab", "prefix": "--cds-", "scope_depth": 1}
    assert resolve.platform_name("component.button.primary-hover", conv) == "--cds-button-primary-hover"
    assert resolve.platform_name("semantic.primary-foreground", \
        {"prefix": "--", "scope_depth": 1}) == "--primary-foreground"
    assert resolve.parse_transform("alpha 80%", "X") == {"alpha": 80.0}
    resolve.lint.clear(); resolve.parse_transform("80 percent", "X")
    assert resolve.lint, "a transform outside the grammar must be lint"
    slots = [{"id": "A", "when": "always", "property": "background", "state": None},
             {"id": "H", "when": "when:hover", "property": "background", "state": "hover"},
             {"id": "D", "when": "when:disabled", "property": "background", "state": "disabled"}]
    resolve.lint.clear()
    default = resolve.slot_scenario(slots[0], slots)
    assert default == {"props": {"disabled": False}, "state": {"hover": False}}, default
    assert resolve.slot_scenario(slots[1], \
        slots)["props"] == {"disabled": False}, "hover applies only while enabled"
    assert resolve.slot_scenario(slots[2], slots) == {"props": {"disabled": True}}


# ---- interaction states, variants and the element ------------------------------------
STATES_TREE = {"core": {"blue": {"$type": "color", "$value": "#0f62fe"}},
               "component": {"button": {
                   "primary":        {"$type": "color", "$value": "{core.blue}"},
                   "primary-hover":  {"$type": "color", "$value": "{core.blue}"},
                   "primary-active": {"$type": "color", "$value": "{core.blue}"},
                   "ghost":          {"$type": "color", "$value": "{core.blue}"},
                   "ghost-hover":    {"$type": "color", "$value": "{core.blue}"},
                   "ghost-active":   {"$type": "color", "$value": "{core.blue}"},
                   "disabled":       {"$type": "color", "$value": "{core.blue}"}}}}
STATES_CONTEXT = """\
tokens:
  source: tokens.json
  tiers:
    primitive: core
    component: component
  prop_axes:
    kind: variant
  readings:
""" + "".join("""    component.button.%s:
      property: background
%s%s""" % (n, "      variant: %s\n" % n.split("-")[0] if n != "disabled" else "",
           "      state: %s\n" % n.split("-")[1] if "-" in n else
           ("      state: disabled\n" if n == "disabled" else ""))
    for n in ("primary", "primary-hover", "primary-active", "ghost", "ghost-hover",
              "ghost-active", "disabled"))

STATES_CONTRACT = """---
component: Button
version: 1.0
role-archetype: button
platforms: [web]
---

# Component Contract: Button

## 1. Intent

A test.

## 2. Structure

%(element)s
## 3. Composition

## 4. Appearance

### 4.1 Token slots

| when | property | token | id |
|---|---|---|---|
%(slots)s
%(states)s
### 4.3 Visual variants

| prop | type | required | default | description |
|---|---|---|---|---|
| `kind` | enum:primary,ghost | no | `primary` | emphasis |

## 5. Behavior

### 5.3 Behavioral props

| prop | type | required | default | description |
|---|---|---|---|---|
| `disabled` | boolean | no | `false` | blocks activation |

## 6. Accessibility
"""
ELEMENT_OK = "| platform | element | id |\n|---|---|---|\n| web | `<button>` | id-STR-01 |\n"
SLOTS_OK = ("| always | background | — | id-APP-01 |\n| when:hover | background | — | id-APP-02 |\n"
            "| when:pressed | background | — | id-APP-03 |\n| when:disabled | background | — | id-APP-04 |\n")
STATES_OK = ("### 4.2 Interaction states\n\n| state | what changes | driven by |\n|---|---|---|\n"
             "| hover | background | platform |\n| focus-visible | — | platform |\n"
             "| pressed | background | platform |\n| disabled | background | prop |\n")


def states_repo(element=ELEMENT_OK, slots=SLOTS_OK, states=STATES_OK):
    repo = pathlib.Path(tempfile.mkdtemp())
    (repo / ".claude").mkdir()
    (repo / "tokens.json").write_text(json.dumps(STATES_TREE))
    (repo / ".claude/design-system-context.yml").write_text(STATES_CONTEXT)
    (repo / "Button.md").write_text(STATES_CONTRACT % {"element": element, "slots": slots, "states": states})
    report = repo / "report.json"
    with tempfile.TemporaryDirectory() as out:
        r = run(HERE / "resolve.py", repo / "Button.md", "--out", out, "--report", report)
        doc = json.loads((pathlib.Path(out) / "Button.web.json").read_text()) \
            if (pathlib.Path(out) / "Button.web.json").is_file() else None
    assert report.is_file(), "resolve.py crashed:\n" + r.stderr[-1200:]
    return r, json.loads(report.read_text()), doc


@test
def every_valid_interaction_state_is_answered():
    """Guards: a contract that styles hover and disabled and says nothing about pressed or the
    focus indicator — which is how the first lab Buttons were written, and nothing noticed."""
    r, rep, doc = states_repo()
    assert not rep["lint"], rep["lint"]
    assert rep["interaction_states"]["valid"] == ["hover", "focus-visible", "pressed", "disabled"]

    _, rep, _ = states_repo(states="")
    for st in ("hover", "focus-visible", "pressed", "disabled"):
        assert any("interaction state %r" % st in l and "not addressed" in l for l in rep["lint"]), \
            (st, rep["lint"])

    # `nothing` meant different things in different places; it is no longer an answer
    said_nothing = STATES_OK.replace("| focus-visible | — |", "| focus-visible | nothing — policy |")
    _, rep, _ = states_repo(states=said_nothing)
    assert any("`nothing` is not an answer" in l for l in rep["lint"]), rep["lint"]

    # 4.2 and 4.1 must agree, in both directions, and a changed property needs a rest case
    unslotted = STATES_OK.replace("| pressed | background |", "| pressed | background, foreground |")
    _, rep, _ = states_repo(states=unslotted)
    assert any("no slot for foreground@pressed" in l for l in rep["lint"]), rep["lint"]
    assert any("no rest (`always`) slot for foreground" in l for l in rep["lint"]), rep["lint"]
    unlisted = STATES_OK.replace("| pressed | background |", "| pressed | — |")
    _, rep, _ = states_repo(states=unlisted)
    assert any("does not list background as changing in pressed" in l for l in rep["lint"]), rep["lint"]


@test
def an_unchanged_state_keeps_its_rest_token_as_a_checkable_alias():
    """Guards: `nothing` as an answer. A property that does not change in a state keeps its rest
    token — stated per variant, forced and checked like any other case."""
    _, rep, doc = states_repo()
    by = {x["id"]: x for x in doc["requirements"] if x["id"].startswith("APP-")}
    a = by["APP-01@focus-visible[kind=ghost]"]
    assert a["expect"] == {"equals": "component.button.ghost"} and a["alias_of"] == "APP-01[kind=ghost]", a
    assert a["scenario"]["state"] == {"focus-visible": True}, a
    assert a["scenario"]["props"]["disabled"] is False, a
    assert "keeps its rest token" in a["statement"], a
    # explicit cases are never shadowed by an alias
    assert "APP-01@hover[kind=ghost]" not in by and "APP-02[kind=ghost]" in by
    # the rest case now excludes every state that has a case of its own
    assert by["APP-01[kind=ghost]"]["scenario"]["state"] == \
        {"hover": False, "focus-visible": False, "pressed": False}, by["APP-01[kind=ghost]"]["scenario"]
    assert not rep["state_token_unused"], rep["state_token_unused"]

    # the tree has pressed tokens, and the contract says background does not change in pressed
    _, rep, doc = states_repo(slots=SLOTS_OK.replace("| when:pressed | background | — | id-APP-03 |\n", ""),
                              states=STATES_OK.replace("| pressed | background |", "| pressed | — |"))
    assert not rep["lint"], rep["lint"]
    flagged = {(n["id"], n["tree_token"]) for n in rep["state_token_unused"]}
    assert ("APP-01@pressed[kind=ghost]", "component.button.ghost-active") in flagged, flagged


@test
def a_slot_applies_to_every_variant_and_a_specific_row_overrides():
    """Guards: token slots silently describing only the default variant."""
    _, rep, doc = states_repo()
    by = {x["id"]: x for x in doc["requirements"] if x["id"].startswith("APP-")}
    assert by["APP-02[kind=primary]"]["expect"] == {"equals": "component.button.primary-hover"}
    assert by["APP-02[kind=ghost]"]["expect"] == {"equals": "component.button.ghost-hover"}
    assert by["APP-02[kind=ghost]"]["scenario"]["props"] == {"kind": "ghost", "disabled": False}
    # `pressed` found under the tree's own spelling, `active`
    assert by["APP-03[kind=ghost]"]["expect"] == {"equals": "component.button.ghost-active"}
    # one token for every variant stays eligible for each
    assert by["APP-04[kind=ghost]"]["expect"] == {"equals": "component.button.disabled"}

    ghost_na = "| when:hover,kind=ghost | background | n/a — ghost has no hover fill | id-APP-05 |\n"
    specific = SLOTS_OK + ghost_na
    _, rep, doc = states_repo(slots=specific)
    ids = {x["id"] for x in doc["requirements"]}
    assert "APP-05" in ids and "APP-02[kind=ghost]" not in ids and "APP-02[kind=primary]" in ids, ids

    only_ghost = SLOTS_OK.replace("| when:hover | background |", "| when:hover,kind=ghost | background |")
    _, rep, _ = states_repo(slots=only_ghost)
    assert any("background@hover is not addressed for kind=primary" in l for l in rep["lint"]), rep["lint"]
    _, rep, _ = states_repo(slots=SLOTS_OK + "| when:hover,kind=tertiary | background | — | id-APP-09 |\n")
    assert any("'tertiary' is not a value of `kind`" in l for l in rep["lint"]), rep["lint"]


@test
def a_table_that_lost_its_header_is_a_finding_not_a_silence():
    """Rules out: rows appended after a blank line becoming a table of their own, read by
    nothing. Nine token slots were added to a lab contract that way and simply did not exist."""
    stray = SLOTS_OK + "\n| always | radius | `component.button.primary` | id-APP-09 |\n"
    _, rep, _ = states_repo(slots=stray)
    assert any("no header" in l for l in rep["lint"]), rep["lint"]


@test
def the_element_carrying_the_role_is_structure():
    """Guards: `<button>` living only in an archetype table the contract never showed, checked
    as a side-note of an accessibility row."""
    _, rep, doc = states_repo()
    first = doc["requirements"][0]
    assert first["id"] == "STR-01" and first["observe"] == "element", first
    assert first["expect"] == {"one_of": ["button"]} and first["needs"] == ["identity"], first
    _, rep, _ = states_repo(element="")
    assert any("no element row for web" in l for l in rep["lint"]), rep["lint"]
    _, rep, _ = states_repo(element=ELEMENT_OK.replace("`<button>`", "`<div>`"))
    assert any("not a native backing" in l for l in rep["lint"]), rep["lint"]
    custom = ELEMENT_OK.replace("`<button>`", "custom — `<div>` with the button pattern")
    _, rep, _ = states_repo(element=custom)
    assert not rep["lint"], rep["lint"]


# ---- specificity, write-back, evidence ----------------------------------------------
def states_contract_repo(slots=SLOTS_OK, context_extra=""):
    repo = pathlib.Path(tempfile.mkdtemp())
    (repo / ".claude").mkdir()
    tree = json.loads(json.dumps(STATES_TREE))
    tree["component"]["control"] = {"radius": {"$type": "dimension", "$value": "4px"}}
    (repo / "tokens.json").write_text(json.dumps(tree))
    (repo / ".claude/design-system-context.yml").write_text(STATES_CONTEXT + context_extra)
    (repo / "Button.md").write_text(STATES_CONTRACT % {"element": ELEMENT_OK, "slots": slots,
                                                       "states": STATES_OK})
    return repo


def resolved(repo):
    report = repo / "report.json"
    with tempfile.TemporaryDirectory() as out:
        r = run(HERE / "resolve.py", repo / "Button.md", "--out", out, "--report", report)
        assert report.is_file(), r.stderr[-800:]
        doc = json.loads((pathlib.Path(out) / "Button.web.json").read_text())
    return r, json.loads(report.read_text()), {x["id"]: x for x in doc["requirements"]}


@test
def a_platform_that_reaches_for_another_token_states_it_in_4_4():
    """Rules out: one cross-platform tree being unusable because two platforms disagree on a
    token, and the disagreement having nowhere to live but a second tree. Spelling is the
    naming convention's job; a DIFFERENT token is a stated row, for that platform only."""
    repo = states_contract_repo()
    md = (repo / "Button.md").read_text()
    md = md.replace("platforms: [web]", "platforms: [web, ios]")
    md = md.replace("| web | `<button>` | id-STR-01 |",
                    "| web | `<button>` | id-STR-01 |\n| ios | `UIButton` | id-STR-02 |")
    md = md.replace("\n### 4.2 Interaction states", """
### 4.4 Platform tokens

| platform | when | property | token | id |
|---|---|---|---|---|
| ios | when:kind=ghost | background | `component.button.disabled` | id-APP-20 |

### 4.2 Interaction states""", 1)
    (repo / "Button.md").write_text(md)
    r, rep, by = resolved(repo)
    assert not rep["lint"], rep["lint"]
    assert by["APP-01[kind=ghost]"]["expect"] == {"equals": "component.button.ghost"}, by["APP-01[kind=ghost]"]
    with tempfile.TemporaryDirectory() as out:
        run(HERE / "resolve.py", repo / "Button.md", "--out", out)
        ios = {x["id"]: x for x in json.loads(
            (pathlib.Path(out) / "Button.ios.json").read_text())["requirements"]}
    # iOS states its own token for that case, and states it ONCE
    assert ios["APP-20"]["expect"] == {"equals": "component.button.disabled"}, ios["APP-20"]
    assert "APP-01[kind=ghost]" not in ios, "the neutral case must not survive beside the platform's own"
    assert ios["APP-01[kind=primary]"]["expect"] == {"equals": "component.button.primary"}, \
        "a case the platform does not answer stays as stated for every platform"
    # a platform the contract does not target is a finding
    (repo / "Button.md").write_text(md.replace("| ios | when:kind=ghost", "| android | when:kind=ghost"))
    _, rep, _ = resolved(repo)
    assert any("does not target" in ln for ln in rep["lint"]), rep["lint"]


@test
def a_shared_group_is_searched_only_for_its_members_and_named_by_scope():
    """Guards: a pattern token (`control.radius`, used by several components) being either
    invisible to the lookup or mistaken for this component's own."""
    radius = SLOTS_OK + "| always | radius | — | id-APP-09 |\n"
    member = "  shared:\n    control: [button, segmented-control]\n"
    _, rep, by = resolved(states_contract_repo(radius, member))
    assert by["APP-09"]["expect"] == {"equals": "component.control.radius"}, by["APP-09"]
    assert by["APP-09"]["scope"] == "shared:control" and by["APP-01[kind=ghost]"]["scope"] == "component"
    assert rep["specificity"] == {"component": 8, "shared:control": 1}, rep["specificity"]
    # button is not a member: the group is not searched, and the resolver asks instead
    _, rep, by = resolved(states_contract_repo(radius, "  shared:\n    control: [segmented-control]\n"))
    assert "expect" not in by["APP-09"], by["APP-09"]
    assert [(n["id"], n["group"]) for n in rep["shared_unconfirmed"]] == [("APP-09", "control")], rep


@test
def writeback_states_what_the_tree_answers_as_patterns_and_nothing_else():
    """Guards: contracts that show no tokens at all when the tree answered every one of them —
    and a write-back that decides anything the tree did not."""
    slots = SLOTS_OK.replace("| always | background | — | id-APP-01 |",
                             "| always | background | `component.button.primary` | id-APP-01 |") \
        + "| always | foreground | — | id-APP-09 |\n"
    repo = states_contract_repo(slots)
    r = run(HERE / "writeback.py", repo / "Button.md")
    assert r.returncode == 0, r.stderr
    text = (repo / "Button.md").read_text()
    assert "| when:hover | background | `component.button.{kind}-hover` | component | id-APP-02 |" in text, \
        text
    assert "| when:pressed | background | `component.button.{kind}-active` | component | id-APP-03 |" in text
    assert "| when:disabled | background | `component.button.disabled` | component | id-APP-04 |" in text
    # a pin is never replaced — only its scope is filled
    assert "| always | background | `component.button.primary` | component | id-APP-01 |" in text
    # the tree has no foreground: the cell stays a gap
    assert "| always | foreground | — | — | id-APP-09 |" in text
    again = run(HERE / "writeback.py", repo / "Button.md")
    assert "nothing to write" in again.stdout, "write-back is not idempotent: " + again.stdout
    _, rep, by = resolved(repo)
    assert by["APP-02[kind=ghost]"]["expect"] == {"equals": "component.button.ghost-hover"}
    # a pattern the tree cannot fill for some value is a finding, naming the value
    bad = text.replace("`component.button.{kind}-hover`", "`component.button.{kind}-over`")
    (repo / "Button.md").write_text(bad)
    _, rep, _ = resolved(repo)
    assert any("gives 'component.button.primary-over' for kind=primary" in l for l in rep["lint"]), \
        rep["lint"]
    # a scope the tree contradicts is a finding
    (repo / "Button.md").write_text(text.replace("`component.button.disabled` | component",
                                                 "`component.button.disabled` | semantic"))
    _, rep, _ = resolved(repo)
    assert any("scope says 'semantic', the tree says 'component'" in l for l in rep["lint"]), rep["lint"]


@test
def implementation_evidence_becomes_questions_never_edits():
    """Guards: an implementation's choice silently becoming the contract's."""
    repo = states_contract_repo()
    before = (repo / "Button.md").read_text()
    results = {"platform": "web", "results": [
        {"id": "APP-02[kind=ghost]", "status": "FAIL", "observed": {"witness": "ghost", "css": [
            {"css": "background-color", "value": "var(--x)", "references": ["--other"]}]}},
        {"id": "APP-01[kind=ghost]", "status": "FAIL", "observed": {"witness": "ghost", "css": [
            {"css": "background-color", "value": "transparent", "references": []}]}},
        {"id": "APP-01@focus-visible[kind=ghost]", "status": "FAIL", "observed": {"witness": "ghost", "css": [
            {"css": "background-color", "value": "transparent", "references": []}]}}]}
    (repo / "results.json").write_text(json.dumps(results))
    r = run(HERE / "evidence.py", repo / "Button.md", repo / "results.json", "--json")
    found = {f["id"]: f for f in json.loads(r.stdout)}
    assert found["APP-02[kind=ghost]"]["kind"] == "contradicts" and \
        found["APP-02[kind=ghost]"]["tree"] == "component.button.ghost-hover", found
    assert found["APP-01[kind=ghost]"]["implementation"] == ["transparent"], found
    assert "APP-01@focus-visible[kind=ghost]" not in found, "an alias repeating its rest case is one question"
    assert (repo / "Button.md").read_text() == before, "evidence must never edit the contract"


# ---- detection ----------------------------------------------------------------------
def naming_tree(flat):
    """Button and chip tokens named property, state, variant — with or without a namespace."""
    c = lambda v: {"$type": "color", "$value": v}  # noqa: E731
    comp = {prop: {st: {v: c("{semantic.x}") for v in ("primary", "secondary")}
                   for st in ("default", "hover", "active")} for prop in ("background", "text")}
    tree = {"core": {"blue": c("#00f")}, "semantic": {"x": c("{core.blue}")}}
    tree.update({"button": comp, "chip": comp} if flat else {"component": {"button": comp, "chip": comp}})
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "t.json").write_text(json.dumps(tree))
    return d / "t.json"


@test
def a_component_tier_without_a_namespace_is_read_never_called_absent():
    """Rules out: `button.*` beside `semantic.*` in one file, invisible to every lookup — and the
    lookup then telling the tree's owner to ADD tokens that already exist."""
    from tokens import Tree
    import detect_tokens
    path = naming_tree(flat=True)
    assert detect_tokens.detect(str(path))["tiers"]["proposed"]["component"] == "*"
    pattern = {"component": ["component.{component}.{property}.{state}.{variant}"]}
    t = Tree(str(path), {"tiers": {"primitive": "core", "semantic": "semantic", "component": "*"},
                         "patterns": pattern})
    assert not t.problems, t.problems
    assert t.resolve("background", "button", {"variant": "secondary"}, "hover")[:2] == \
        ("component.button.background.hover.secondary", "bound")
    # tiers declared, the component groups left unclaimed: a named problem, not a silent miss
    t = Tree(str(path), {"tiers": {"primitive": "core", "semantic": "semantic"}, "patterns": pattern})
    assert any("no tier claims the top-level group(s) button, chip" in p for p in t.problems), t.problems


@test
def detection_reads_which_position_holds_the_property_in_any_order():
    """Rules out: assuming the property is the last segment — which read `primary` as a
    property and asked what property it names, an answer that would corrupt every lookup."""
    import detect_tokens
    for flat in (False, True):
        d = detect_tokens.detect(str(naming_tree(flat)))
        assert [p["template"] for p in d["patterns"]] == ["component.{component}.{property}.{state}.{?}"], \
            d["patterns"]
        asked = [q["question"] for q in d["questions"]]
        assert not any(q.startswith("Which property does `primary`") for q in asked), asked
        assert any("segment 5 vary by? It takes the values primary, secondary" in q for q in asked), asked

@test
def detection_reads_tiers_from_alias_direction_not_names():
    import detect_tokens
    d = detect_tokens.detect(str(ALT))
    assert d["tiers"]["proposed"] == {"primitive": "core", "semantic": "semantic",
                                      "component": "component"}, d["tiers"]["proposed"]


@test
def detection_never_asks_a_poisoning_question():
    """Guards: asking what property `lg` or `primary` names — answering would corrupt leaf_map."""
    import detect_tokens
    for tree, forbidden in ((FIXTURE, ["`lg`", "`md`", "`sm`", "`primary`", "`ghost`", "`error`", "`info`"]),
                            (ALT, ["`default`", "`hover`", "`primary`"])):
        qs = [q["question"] for q in detect_tokens.detect(str(tree))["questions"]
              if q["about"].startswith("leaf_map")]
        bad = [q for q in qs if any(q.startswith("Which property does " + f) for f in forbidden)]
        assert not bad, bad


@test
def detection_splits_an_unknown_that_means_different_things_per_component():
    import detect_tokens
    tpls = {p["template"] for p in detect_tokens.detect(str(FIXTURE))["patterns"]}
    assert "component.badge.{property}.{?}" in tpls and "component.toast.{property}.{?}" in tpls, tpls
    assert "component.{component}.variant.{variant}.{property}" in tpls, tpls


@test
def suggestions_match_whole_words_only():
    """Guards: `icon-color` suggested as on-color because `iconcolor` contains `oncolor`."""
    import detect_tokens
    assert detect_tokens.suggest_property("icon-color", "color") == []
    assert detect_tokens.suggest_property("bgColor", "color") == ["background"]


# ---- context file --------------------------------------------------------------------
@test
def context_reader_refuses_what_it_cannot_read():
    import context
    f = pathlib.Path(tempfile.mkdtemp()) / "c.yml"
    for text in ("a: &x 1", "a: |\n  t", "a: {b: 1}", "a:\n  - b: 1", "a:\n\tb: 1"):
        f.write_text(text)
        try:
            context._load_subset(text, "c.yml")
        except context.ContextError:
            continue
        raise AssertionError("not refused: %r" % text)


@test
def context_reader_reads_the_shipped_template():
    import context
    d = context._load_subset((ROOT / "system/templates/context.template.yml").read_text(), "t")
    assert "tokens" in d and isinstance(d["tokens"], dict), d


# ---- machine ---------------------------------------------------------------------------
@test
def machine_lint_catches_each_modelling_error():
    import machine as sm
    cases = {
        "child state": [{"from": "a", "event": "e", "to": "day.selected", "id": "1"}],
        "zone as state": [{"from": "a", "event": "e", "to": "list", "id": "2"}],
        "nondeterministic": [{"from": "a", "event": "e", "to": "b", "id": "3"},
                             {"from": "a", "event": "e", "to": "c", "id": "4"}],
        "self-transition": [{"from": "a", "event": "e", "to": "a", "id": "5"}],
        "reasonless n/a": [{"from": "a", "event": "e", "to": "b", "id": "6"},
                           {"from": "b", "event": "e", "to": "n/a", "id": "—"}],
    }
    missed = [n for n, rows in cases.items() if not sm.build(rows, zones={"list"})[1]]
    assert not missed, missed


@test
def web_verifier_scenario_must_be_established():
    """Guards: matches() once read only `props`, so every hover/zone/machine scenario matched."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("v", PIPE / "3-verifiers/web/verify.py")
    v = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            spec.loader.exec_module(v)
        except SystemExit:
            pass
    no_icon = {"name": "x", "props": {},
               "html": '<button data-zone="root"><span data-zone="label">S</span></button>'}
    assert not v.matches({"zones": {"icon": "present"}}, no_icon)
    assert not v.matches({"state": {"hover": True}}, v.WIT[0])
    assert not v.matches({"machine": {"state": "expanded"}}, v.WIT[0])
    assert v.matches({"zones": {"icon": "present"}}, v.WIT[0])


# ---- generated files vs their inputs ----------------------------------------------------
def _cg():
    import importlib.util
    spec = importlib.util.spec_from_file_location("cg", HERE / "check_generated.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def one_contract_repo():
    """A design system with a single contract, its generated/ written from its own inputs.

    The contract moves into its own directory, so its frontmatter's relative `policy:` path
    would no longer resolve — the policy's location becomes a recorded fact instead, which is
    what a real design system does once it has more than one contract.
    """
    d = alt_design_system(ALT_CONTEXT + "  \ncontracts:\n  path: contracts\n"
                          "  policy: contracts/design-system/policy.md\n")
    # The layout check_generated expects: <Name>/<Name>.md, with generated/ beside it.
    home = d / "contracts/Button"
    home.mkdir()
    (d / "contracts/Button.md").rename(home / "Button.md")
    (d / "contracts/Button.bindings.json").rename(home / "Button.bindings.json")
    md = home / "Button.md"
    md.write_text("\n".join(x for x in md.read_text().splitlines()
                            if not x.startswith("policy:")) + "\n")
    r = run(HERE / "resolve.py", md, "--out", home / "generated")
    assert r.returncode == 0, "fixture does not resolve:\n%s" % (r.stdout + r.stderr)[-500:]
    run(HERE / "resolve_view.py", md, "--out", home / "generated/Button.spec.md")
    return d, home


@test
def a_generated_file_matching_its_inputs_is_silent():
    """Guards: a check that reports drift on a freshly generated tree, and so is ignored."""
    cg = _cg()
    _, home = one_contract_repo()
    rep = cg.check_one(home / "Button.md")
    assert not [f for f in rep["findings"] if f["kind"] in cg.ACTIONABLE], rep


@test
def an_edited_generated_file_is_stale_and_says_what_moved():
    """Guards: reporting `differs` with no indication of what a shared change actually did."""
    cg = _cg()
    _, home = one_contract_repo()
    doc = json.loads((home / "generated/Button.web.json").read_text())
    doc["requirements"] = [r for r in doc["requirements"] if r.get("id") != "BTN-01"]
    (home / "generated/Button.web.json").write_text(json.dumps(doc, indent=2) + "\n")
    stale = [f for f in cg.check_one(home / "Button.md")["findings"] if f["kind"] == "stale"]
    assert stale and "BTN-01" in stale[0]["detail"], stale


@test
def a_document_nothing_produces_is_an_orphan_and_fix_never_deletes_it():
    """Guards: a dropped platform's document staying committed, read by someone, unnoticed.

    And the other half: `--fix` quietly deleting it. Whether a file is genuinely dead is a
    conclusion for a person; regeneration not producing it is not the same claim.
    """
    cg = _cg()
    _, home = one_contract_repo()
    (home / "generated/Button.macos.json").write_text("{}\n")
    kinds = {f["file"]: f["kind"] for f in cg.check_one(home / "Button.md")["findings"]}
    assert kinds.get("Button.macos.json") == "orphan", kinds
    cg.check_one(home / "Button.md", fix=True)
    assert (home / "generated/Button.macos.json").is_file(), "--fix must never delete"


@test
def a_contract_that_does_not_resolve_is_never_reported_up_to_date():
    """Guards: the one failure this check exists to rule out — silence over an unreadable
    contract, which would read as `ok` and let real drift hide behind a lint error."""
    cg = _cg()
    _, home = one_contract_repo()
    md = home / "Button.md"
    md.write_text(md.read_text().replace("when:hover ", "when:hoverr "))
    kinds = {f["kind"] for f in cg.check_one(md)["findings"]}
    assert kinds == {"unresolvable"}, kinds


@test
def a_schema_is_named_unverifiable_never_orphan_and_never_passed():
    """Guards: `*.schema.json` — written by the skill, not by any script — being called an
    orphan and deleted, or quietly counted as up to date."""
    cg = _cg()
    _, home = one_contract_repo()
    (home / "generated/Button.web.schema.json").write_text("{}\n")
    kinds = {f["file"]: f["kind"] for f in cg.check_one(home / "Button.md")["findings"]}
    assert kinds.get("Button.web.schema.json") == "unverifiable", kinds
    assert "unverifiable" not in cg.ACTIONABLE, "unverifiable must not fail the check"


# ---- reference freshness ---------------------------------------------------------------
@test
def a_reference_with_no_date_can_never_come_due_so_it_is_a_finding():
    """Guards: a file with no `Last verified:` line silently never being checked again."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("cr", HERE / "check_references.py")
    cr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cr)

    import datetime
    due, fresh, broken = cr.survey(90, today=datetime.date(2026, 9, 21))
    assert not broken, "every shipped reference must carry a date: %s" % broken
    assert due or fresh, "no reference files were read at all"

    # The wrong conclusion this rules out: treating a dateless file as fresh. Age is
    # unknowable without a date, so it can never be older than the threshold, and a check
    # that only compares dates would pass it forever.
    with tempfile.TemporaryDirectory() as d:
        undated = pathlib.Path(d) / "undated.md"
        undated.write_text("# No date\n\nSource of authority: https://example.org/\n")
        r = cr.read(undated)
        assert r["verified"] is None, r


@test
def a_reference_citing_no_url_is_checked_differently_not_skipped():
    """Guards: `platform-differences.md` reported as citing nothing, or quietly dropped.

    It aggregates the other files rather than citing an external URL, so checking it means
    confirming it still agrees with them — a different job, not an absent one.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("cr", HERE / "check_references.py")
    cr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cr)

    how = {r["file"]: r["how"] for r in cr.survey(0)[0]}
    assert how["references/platform-differences.md"] == "agrees-with-others", how
    assert how["references/web/wcag-mapping.md"] == "fetch", how
    # A source named in prose is read by a person, never fetched and never called absent.
    assert how["references/figma-variables-model.md"] == "read", how
    assert set(how.values()) <= {"fetch", "read", "agrees-with-others"}, how


if __name__ == "__main__":
    for status, name, why in results:
        print("%s  %s%s" % (status, name, ("\n      " + why.replace("\n", "\n      ")) if why else ""))
    failed = sum(1 for r in results if r[0] == "FAIL")
    print("\n%d passed, %d failed" % (len(results) - failed, failed))
    sys.exit(1 if failed else 0)
