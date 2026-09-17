#!/usr/bin/env python3
"""Find and read `.claude/design-system-context.yml` — the facts about THIS design system.

The file is YAML because people edit it. The scripts that read it must run anywhere with no
dependency, and PyYAML is not in the standard library. So: PyYAML when it is importable, and
otherwise a reader for exactly the subset this file uses —

    nested mappings by indentation · scalars (plain, quoted, true/false, null, numbers)
    inline lists `[a, b]` · block lists of scalars `- a` · `#` comments

— which REFUSES anything outside that subset (anchors, multi-line strings, flow mappings, a
list of mappings) with the line number, rather than guessing. A silently misread context file
would mis-resolve every token in the design system, which is worse than a clear error.
"""
import pathlib, re

CONTEXT_REL = pathlib.Path(".claude") / "design-system-context.yml"


class ContextError(ValueError):
    pass


def find(start):
    """Walk up from `start` to the nearest `.claude/design-system-context.yml`, or None."""
    here = pathlib.Path(start).resolve()
    for d in [here] + list(here.parents):
        candidate = d / CONTEXT_REL
        if candidate.is_file():
            return candidate
    return None


def repo_root(context_path):
    """Paths inside the context file are relative to the directory holding `.claude/`."""
    return pathlib.Path(context_path).resolve().parent.parent


def load(path):
    text = pathlib.Path(path).read_text()
    try:
        import yaml  # type: ignore
    except ImportError:
        return _load_subset(text, str(path))
    return yaml.safe_load(text) or {}


# ---- subset reader -------------------------------------------------------------------
_REFUSE = [(re.compile(r"^\s*[&*!]|:\s*[&*!]"), "anchors, aliases and tags"),
           (re.compile(r":\s*[|>][-+]?\s*$"), "multi-line strings"),
           (re.compile(r":\s*\{"), "flow mappings"),
           (re.compile(r"^\s*-\s+[^\s#][^:#]*:\s"), "a list of mappings")]


def _scalar(raw):
    v = raw.strip()
    if v == "" or v in ("null", "~"):
        return None
    if v[0] in "\"'" and v[-1] == v[0] and len(v) >= 2:
        return v[1:-1]
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    if v.startswith("[") and v.endswith("]"):
        return [_scalar(x) for x in v[1:-1].split(",") if x.strip()]
    return v


def _strip_comment(line):
    out, quote = [], None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1].isspace()):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _load_subset(text, name):
    lines = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = _strip_comment(raw)
        if not line.strip():
            continue
        for pattern, what in _REFUSE:
            if pattern.search(line):
                raise ContextError("%s:%d uses %s, which the dependency-free reader does not "
                                   "support — install PyYAML or simplify the line" % (name, n, what))
        lead = line[: len(line) - len(line.lstrip())]
        if "\t" in lead:
            raise ContextError("%s:%d indents with a tab" % (name, n))
        lines.append((n, len(lead), line.strip()))
    if not lines:
        return {}
    value, i = _block(lines, 0, lines[0][1], name)
    if i != len(lines):
        raise ContextError("%s:%d is indented less than the document start" % (name, lines[i][0]))
    if not isinstance(value, dict):
        raise ContextError("%s: the top level must be a mapping" % name)
    return value


def _block(lines, i, indent, name):
    """Parse the block starting at line i whose items sit at exactly `indent`."""
    if lines[i][2].startswith("- ") or lines[i][2] == "-":
        items = []
        while i < len(lines) and lines[i][1] == indent and lines[i][2].startswith("-"):
            items.append(_scalar(lines[i][2][1:]))
            i += 1
        return items, i

    mapping = {}
    while i < len(lines) and lines[i][1] >= indent:
        n, ind, body = lines[i]
        if ind > indent:
            raise ContextError("%s:%d is indented more than its siblings" % (name, n))
        if body.startswith("-"):
            raise ContextError("%s:%d list item where a `key:` was expected" % (name, n))
        m = re.match(r"^([^:]+?)\s*:(?:\s+(.*))?$", body)
        if not m:
            raise ContextError("%s:%d is not `key: value`" % (name, n))
        key, value = m.group(1).strip().strip("\"'"), m.group(2)
        i += 1
        if value not in (None, ""):
            mapping[key] = _scalar(value)
            continue
        nxt = lines[i] if i < len(lines) else None
        if nxt and (nxt[1] > indent or (nxt[1] == indent and nxt[2].startswith("-"))):
            mapping[key], i = _block(lines, i, nxt[1], name)
        else:
            mapping[key] = None
    return mapping, i
