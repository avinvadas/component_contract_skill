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
