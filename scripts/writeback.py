#!/usr/bin/env python3
"""Write what the token tree answered into the contract's own token slots.

    python3 scripts/writeback.py path/to/Button.md [--context PATH] [--dry-run]

The tree is the authority on tokens, so what it answers UNIQUELY goes into the contract without
asking. A `—` cell becomes the token it resolved to, with its `scope`; a row that resolves to a
different token per variant becomes a PATTERN — `component.button.{kind}-hover` — and every value
that breaks the pattern gets an override row of its own, with its own token and scope. Nothing
else is decided here:

    - a case the tree cannot answer (ambiguous, absent, unreadable) keeps `—` and stays a gap;
    - a pinned token is never replaced — only its `scope` is filled;
    - `n/a` rows are left as they are.

Anything an IMPLEMENTATION suggests is not the tree, and never arrives through this script:
`scripts/evidence.py` turns it into questions for the person.

Running it twice changes nothing the second time.
"""
import argparse, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import resolve as R  # noqa: E402


def template_of(token, combo):
    """`component.button.secondary-hover` with kind=secondary -> `component.button.{kind}-hover`."""
    out = token
    for prop, val in combo.items():
        out = re.sub(r"(?<=[.\-])%s(?=$|[.\-])" % re.escape(val), "{%s}" % prop, out)
    return out


def plan(rows, cases):
    """[(row, cell, scope, [override rows])] for the slot table, in order."""
    by_row = {}
    for c in cases:
        if not c.get("alias_of"):
            by_row.setdefault(c["base_id"], []).append(c)
    used = [int(m.group(1)) for r in rows if (m := re.match(r"APP-(\d+)$", r["id"]))]
    next_id = [max(used or [0]) + 1]

    def new_id():
        rid = "APP-%02d" % next_id[0]
        next_id[0] += 1
        return rid

    out = []
    for r in rows:
        cell = r["token"].strip().strip("`")
        mine = by_row.get(r["id"], [])
        bound = [c for c in mine if c["status"] == "bound"]
        if cell.lower().startswith("n/a") or not bound:
            out.append((r, r["token"], r.get("scope") or "—", []))
            continue
        if cell not in ("—", "-", ""):
            # Pinned, or already a pattern: the person's choice stands; only its scope is filled.
            scopes = {c["scope"] for c in bound}
            out.append((r, r["token"], scopes.pop() if len(scopes) == 1 else r.get("scope") or "—", []))
            continue
        # `—`: the tree answered. The pattern most values share becomes the row's token — over
        # the values the row SPANS only; a value the row names itself is not a placeholder.
        own = R.parse_when(r.get("when", "always"))[1]
        span = lambda c: {k: v for k, v in c["variant"].items() if k not in own}  # noqa: E731
        tally = {}
        for c in bound:
            tally.setdefault((template_of(c["token"], span(c)), c["scope"]), []).append(c)
        (tpl, scope), _ = max(tally.items(), key=lambda kv: len(kv[1]))
        overrides = []
        for c in mine:
            if c["status"] == "bound" and (template_of(c["token"], span(c)), c["scope"]) == (tpl, scope):
                continue
            conds = [] if r.get("when", "always") in ("always", "") else [r["when"][len("when:"):]]
            conds += ["%s=%s" % kv for kv in span(c).items()]
            o = dict(r, id=new_id(), when="when:" + ",".join(conds))
            if c["status"] == "bound":
                overrides.append((o, "`%s`" % c["token"], c["scope"]))
            else:
                overrides.append((o, "—", "—"))       # still a gap, now visibly per value
        out.append((r, "`%s`" % tpl, scope, overrides))
    return out


def render(headers, planned):
    """The slot table, with a `scope` column after `token`."""
    cols = [h for h in headers if h != "scope"]
    cols.insert(cols.index("token") + 1, "scope")
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]

    def line(row, token, scope):
        vals = dict(row, token=token, scope=scope, id="id-" + row["id"])
        return "| " + " | ".join(str(vals.get(c, "—")).replace("|", "\\|") for c in cols) + " |"

    for row, token, scope, overrides in planned:
        lines.append(line(row, token, scope))
        lines += [line(o, t, sc) for o, t, sc in overrides]
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("contract")
    ap.add_argument("--context")
    ap.add_argument("--dry-run", action="store_true", help="print the new table, change nothing")
    args = ap.parse_args()

    path = pathlib.Path(args.contract).resolve()
    S = R.load_sources(path, args.context)
    R.ENUM_PROPS.update(R.enum_props(S["body"]))
    cases = R.resolve_slots(S["body"], S["fm"], S["tree"], S["arch_fm"])

    text = path.read_text()
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines) if l.strip().startswith("|")
                  and {"property", "token", "id"} <= {c.strip() for c in l.strip().strip("|").split("|")}
                  and "statement" not in l), None)
    if start is None:
        sys.exit("no token slot table in %s" % path)
    end = start
    while end < len(lines) and lines[end].strip().startswith("|"):
        end += 1
    headers = [c.strip() for c in lines[start].strip().strip("|").split("|")]
    rows = R.slot_rows(S["body"])

    new = render(headers, plan(rows, cases))
    if args.dry_run:
        print("\n".join(new))
        return
    lines[start:end] = new
    updated = "\n".join(lines)
    if updated == text:
        print("%s: nothing to write — every token the tree answers is already stated" % path.name)
        return
    path.write_text(updated)
    print("%s: token slots written from the tree (%d row(s) now)" % (path.name, len(new) - 2))


if __name__ == "__main__":
    main()
