#!/usr/bin/env python3
"""Validate each platform's manifest against its generated schema, and report per
requirement in the contract's own words.

This is the 'thin reporting layer' the v3 proposal calls for: stock validator output
names a JSON path and a failed keyword, which is useless to a human. Every constraint
carries $comment (requirement id) and title (the statement), so a failure resolves back
to the sentence the designer wrote.

Three outcomes, and unverified is never folded into pass:
  pass       the schema proved it
  fail       the schema disproved it
  unverified the section was unavailable, or the method used could not see the fact
"""
import json, pathlib, sys
from jsonschema import Draft7Validator

HERE = pathlib.Path(__file__).parent

def collect_requirements(schema):
    """id -> (title, section, not_applicable_reason). Section is tracked while
    descending, not recovered from the path: the path interleaves JSON Schema
    keywords, and guessing at it is how BTN-04..09 were once reported as passing
    on a platform whose behavior section never ran."""
    found = {}
    def walk(node, path, section):
        if isinstance(node, dict):
            if "$comment" in node:
                found[node["$comment"]] = (node.get("title", ""), section,
                                           node.get("x-not-applicable"))
            for k, v in node.items():
                nxt = k if (len(path) >= 2 and path[-2] == "sections"
                            and path[-1] == "properties") else section
                walk(v, path + [k], nxt)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + [str(i)], section)
    walk(schema, [], None)
    return found

def requirement_for_error(schema, err):
    """Resolve a validation error back to the nearest requirement id."""
    node, best = schema, None
    for step in err.absolute_schema_path:
        if isinstance(node, dict) and isinstance(step, str) and step in node:
            node = node[step]
        elif isinstance(node, list) and isinstance(step, int) and step < len(node):
            node = node[step]
        else:
            break
        if isinstance(node, dict) and "$comment" in node:
            best = node["$comment"]
    # a 'required' failure points at the parent; the missing property carries the id
    if err.validator == "required" and isinstance(node, dict):
        for prop in node.get("properties", {}):
            if f"'{prop}'" in err.message:
                sub = node["properties"][prop]
                if isinstance(sub, dict) and "$comment" in sub:
                    return sub["$comment"]
    return best

def report(platform):
    schema = json.loads((HERE / f"Button.{platform}.schema.json").read_text())
    manifest = json.loads((HERE / "manifests" / f"Button.{platform}.manifest.json").read_text())
    reqs = collect_requirements(schema)

    failures = {}
    for err in Draft7Validator(schema).iter_errors(manifest):
        rid = requirement_for_error(schema, err)
        if rid:
            failures.setdefault(rid, err.message)

    unverified = {}
    for name, sec in manifest.get("sections", {}).items():
        if sec.get("status") == "unavailable":
            reason = sec.get("reason", "section unavailable")
            for rid, (_, section, _na) in reqs.items():
                if section == name:
                    unverified[rid] = reason
        for rid in sec.get("unsupported", []):
            unverified[rid] = sec.get("unsupported_reason", "method cannot observe this fact")

    rows = []
    for rid in sorted(reqs, key=lambda r: (r.split("-")[0], r)):
        title, _section, na = reqs[rid]
        if na:                  rows.append(("N/A", rid, title, na))
        elif rid in unverified: rows.append(("UNVERIFIED", rid, title, unverified[rid]))
        elif rid in failures:   rows.append(("FAIL", rid, title, failures[rid]))
        else:                   rows.append(("PASS", rid, title, ""))
    return manifest.get("conformance_level"), rows

MARK = {"PASS": "PASS ", "FAIL": "FAIL ", "UNVERIFIED": "UNVER", "N/A": " n/a "}
exit_code = 0
for platform in ("web", "ios", "android"):
    level, rows = report(platform)
    counts = {k: sum(1 for r in rows if r[0] == k) for k in ("PASS", "FAIL", "UNVERIFIED", "N/A")}
    print(f"\n{'='*78}\n{platform.upper()}  -  conformance level {level}   "
          f"{counts['PASS']} pass / {counts['FAIL']} fail / "
          f"{counts['UNVERIFIED']} unverified / {counts['N/A']} n-a\n{'='*78}")
    for status, rid, title, detail in rows:
        if status == "PASS":
            print(f"  {MARK[status]}  {rid:<8} {title}")
        else:
            print(f"  {MARK[status]}  {rid:<8} {title}")
            print(f"         {'':8} -> {detail}")
    if counts["FAIL"]:
        exit_code = 1
print()
sys.exit(exit_code)
