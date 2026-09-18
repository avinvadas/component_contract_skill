#!/usr/bin/env python3
"""Regression tests for the skill's scripts. Standard library only.

    python3 scripts/test_scripts.py

Each test names the failure it guards against. Several of those failures shipped once.
"""
import contextlib, io, json, pathlib, shutil, subprocess, sys, tempfile

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
            for f in pathlib.Path(out).glob(c + ".*.canonical.json"):
                committed = PIPE / "2-canonical" / f.name
                assert f.read_text() == committed.read_text(), "%s differs from committed" % f.name
            view = pathlib.Path(out) / (c + ".resolved.md")
            r = run(HERE / "resolve_view.py", PIPE / "1-contract" / (c + ".md"), "--out", view)
            assert r.returncode == 0, "%s view failed: %s" % (c, r.stderr[-400:])
            assert view.read_text() == (PIPE / (c + ".resolved.md")).read_text(), "%s view differs" % c


@test
def archetype_comes_from_the_contract():
    """Guards: resolve.py once hardcoded button.md, and Combobox would have inherited Button."""
    with tempfile.TemporaryDirectory() as out:
        run(HERE / "resolve.py", PIPE / "1-contract/Combobox.md", "--out", out)
        doc = json.loads((pathlib.Path(out) / "Combobox.web.canonical.json").read_text())
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
    text = text.replace("| always | radius | `component.button.radius` | id-APP-05 |",
                        "| always | radius | — | id-APP-05 |")
    md.write_text(text)
    if context_text is not None:
        (d / ".claude").mkdir()
        (d / ".claude/design-system-context.yml").write_text(context_text)
    return d


def slots_of(repo):
    with tempfile.TemporaryDirectory() as out:
        r = run(HERE / "resolve.py", repo / "contracts/Button.md", "--out", out)
        doc = json.loads((pathlib.Path(out) / "Button.web.canonical.json").read_text())
    reqs = {x["id"]: x for x in doc["requirements"] if x["id"].startswith("APP-")}
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
        doc = json.loads((pathlib.Path(out) / "Button.web.canonical.json").read_text())
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
        doc = json.loads((pathlib.Path(out) / "Card.web.canonical.json").read_text())
        assert doc["role-archetype"] == "none", doc["role-archetype"]
        assert {x["id"] for x in doc["requirements"]} == {"STR-01"}, doc["requirements"]
        v = run(HERE / "resolve_view.py", d / "Card.md", "--out", pathlib.Path(out) / "Card.resolved.md")
        assert v.returncode == 0, v.stderr[-500:]


# ---- accumulation: the second component benefits from the first -------------------------
ACC_TREE = {
  "core": {"color": {"purple": {"$type": "color", "$value": "#4C00A8"},
                     "white":  {"$type": "color", "$value": "#FFFFFF"},
                     "gray":   {"$type": "color", "$value": "#E5E7EB"}}},
  "semantic": {"color": {"bg": {"strong": {"$type": "color", "$value": "{core.color.purple}"},
                                "subtle": {"$type": "color", "$value": "{core.color.gray}"}},
                         "fg": {"inverse": {"$type": "color", "$value": "{core.color.white}"}}}},
  "component": {
    "button": {"primary":   {"bgColor":   {"default": {"$type": "color", "$value": "{semantic.color.bg.strong}"}},
                             "textColor": {"default": {"$type": "color", "$value": "{semantic.color.fg.inverse}"}}},
               "secondary": {"bgColor":   {"default": {"$type": "color", "$value": "{semantic.color.bg.subtle}"}},
                             "textColor": {"default": {"$type": "color", "$value": "{semantic.color.fg.inverse}"}}}},
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
""" % (name, archetype, name, extra)


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
    for expected in ("tokens.leaf_map.bgColor = background", "POL-01", "POL-03", "POL-04 literal denial: deferred"):
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
        "blue": {"60": {"$type": "color", "$value": {"colorSpace": "srgb", "components": [0, 0.4, 1], "hex": "#0f62fe"}}},
        "gray": {"30": {"$type": "color", "$value": "#c6c6c6"}}}))
    (d / "theme.json").write_text(json.dumps({
        "text-on-color": {"$type": "color", "$value": "{gray.30}"}}))
    (d / "button.json").write_text(json.dumps({"button": {
        "primary":  {"$type": "color", "$extensions": {"carbon.themes": {"white": "{blue.60}"}}},
        "tertiary": {"$type": "color", "$extensions": {"carbon.themes": {"white": "{blue.60}"}}},
        "disabled": {"$type": "color", "$extensions": {"carbon.themes": {"white": "{gray.30}"}}}}}))
    facts = {"sources": {"primitive": ["palette.json"], "semantic": ["theme.json"], "component": ["button.json"]},
             "theme": {"name": "white", "value_path": ["$extensions", "carbon.themes", "{theme}"]},
             "readings": {"component.button.primary":  {"property": "background", "variant": "primary"},
                          "component.button.tertiary": {"property": "foreground", "variant": "tertiary"},
                          "component.button.disabled": {"property": "background", "state": "disabled"}}}
    t = Tree(str(d), facts)
    assert not t.problems, t.problems
    # tiers from files; themed values read; aliases rewritten across files
    assert t.tokens["component.button.primary"]["value"] == "{primitive.blue.60}", t.tokens["component.button.primary"]
    # a DTCG 2025 colour object is a value, never an alias
    assert "primitive.blue.60" not in t.alias, "a colour object was read as an alias"
    assert t.resolve("background", "button", {"variant": "primary"})[:2] == ("component.button.primary", "bound")
    assert t.resolve("background", "button", {"variant": "primary"}, "disabled")[:2] == \
        ("component.button.disabled", "bound"), "a token for every variant must stay eligible"
    tok, status, _ = t.resolve("foreground", "button", {"variant": "primary"})
    assert tok != "component.button.tertiary", "bound a primary button's text to the TERTIARY button's"


# ---- detection ----------------------------------------------------------------------
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
    no_icon = {"name": "x", "props": {}, "html": '<button data-zone="root"><span data-zone="label">S</span></button>'}
    assert not v.matches({"zones": {"icon": "present"}}, no_icon)
    assert not v.matches({"state": {"hover": True}}, v.WIT[0])
    assert not v.matches({"machine": {"state": "expanded"}}, v.WIT[0])
    assert v.matches({"zones": {"icon": "present"}}, v.WIT[0])


if __name__ == "__main__":
    for status, name, why in results:
        print("%s  %s%s" % (status, name, ("\n      " + why.replace("\n", "\n      ")) if why else ""))
    failed = sum(1 for r in results if r[0] == "FAIL")
    print("\n%d passed, %d failed" % (len(results) - failed, failed))
    sys.exit(1 if failed else 0)
