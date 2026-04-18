#!/usr/bin/env python3
"""Small YAML helpers for the v16.1 scaffold.

The scripts prefer PyYAML when it is installed.  When it is not available,
this module falls back to a conservative parser for the YAML subset emitted by
Stage-A v16.1 contracts: indentation-based mappings/lists, quoted or plain
scalars, booleans, nulls, and integer scalars.  The fallback intentionally
rejects advanced YAML features rather than guessing.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Iterable

PLACEHOLDERS = {"", "TBD", "UNKNOWN", "...", "TODO", "null", "None", "NONE"}


@dataclass
class LoadedYaml:
    data: Any
    parser: str


class MiniYamlError(ValueError):
    pass


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    fence = re.match(r"^```(?:yaml|yml)?\s*(.*?)\s*```$", stripped, re.S | re.I)
    if fence:
        return fence.group(1).strip() + "\n"
    return text


def _remove_inline_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for i, ch in enumerate(line):
        if ch == "\\" and in_double and not escaped:
            escaped = True
            continue
        if ch == "'" and not in_double and not escaped:
            in_single = not in_single
        elif ch == '"' and not in_single and not escaped:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if i == 0 or line[i - 1].isspace():
                return line[:i].rstrip()
        escaped = False
    return line.rstrip()


def _logical_lines(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        if raw.lstrip().startswith("#"):
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise MiniYamlError("Tabs are not allowed for indentation.")
        line = _remove_inline_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            raise MiniYamlError(f"Indentation must use multiples of two spaces: {raw!r}")
        out.append((indent, line.strip()))
    return out


def _split_key_value(text: str) -> tuple[str, str | None]:
    in_single = False
    in_double = False
    escaped = False
    for i, ch in enumerate(text):
        if ch == "\\" and in_double and not escaped:
            escaped = True
            continue
        if ch == "'" and not in_double and not escaped:
            in_single = not in_single
        elif ch == '"' and not in_single and not escaped:
            in_double = not in_double
        elif ch == ":" and not in_single and not in_double:
            key = text[:i].strip()
            value = text[i + 1 :].strip()
            if not key:
                raise MiniYamlError(f"Empty mapping key in {text!r}")
            return key, value if value != "" else None
        escaped = False
    raise MiniYamlError(f"Expected key: value, got {text!r}")


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        inner = value[1:-1]
        if value.startswith('"'):
            inner = inner.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
        else:
            inner = inner.replace("''", "'")
        return inner
    if re.fullmatch(r"[-+]?\d+", value):
        try:
            return int(value)
        except ValueError:
            pass
    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        # Conservative inline list support: comma-separated scalars without nested structures.
        parts = []
        buf = ""
        in_single = False
        in_double = False
        for ch in body:
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            if ch == "," and not in_single and not in_double:
                parts.append(_parse_scalar(buf.strip()))
                buf = ""
            else:
                buf += ch
        if buf.strip():
            parts.append(_parse_scalar(buf.strip()))
        return parts
    return value


def _parse_block(lines: list[tuple[int, str]], idx: int, indent: int) -> tuple[Any, int]:
    if idx >= len(lines):
        return None, idx
    if lines[idx][0] < indent:
        return None, idx
    if lines[idx][0] != indent:
        raise MiniYamlError(f"Unexpected indentation at line {idx + 1}: {lines[idx]}")

    is_list = lines[idx][1].startswith("- ")
    if is_list:
        arr: list[Any] = []
        while idx < len(lines):
            cur_indent, content = lines[idx]
            if cur_indent < indent:
                break
            if cur_indent != indent or not content.startswith("- "):
                break
            item = content[2:].strip()
            idx += 1
            if item == "":
                if idx < len(lines) and lines[idx][0] > cur_indent:
                    nested, idx = _parse_block(lines, idx, lines[idx][0])
                    arr.append(nested)
                else:
                    arr.append(None)
                continue
            if ":" in item and not item.startswith(('"', "'")):
                key, value = _split_key_value(item)
                d: dict[str, Any] = {}
                if value is None:
                    if idx < len(lines) and lines[idx][0] > cur_indent:
                        nested, idx = _parse_block(lines, idx, lines[idx][0])
                        d[key] = nested
                    else:
                        d[key] = None
                else:
                    d[key] = _parse_scalar(value)
                if idx < len(lines) and lines[idx][0] > cur_indent:
                    nested, idx = _parse_block(lines, idx, lines[idx][0])
                    if isinstance(nested, dict):
                        d.update(nested)
                    else:
                        raise MiniYamlError("List item mapping continuation must be a mapping.")
                arr.append(d)
            else:
                arr.append(_parse_scalar(item))
        return arr, idx

    d: dict[str, Any] = {}
    while idx < len(lines):
        cur_indent, content = lines[idx]
        if cur_indent < indent:
            break
        if cur_indent != indent:
            break
        if content.startswith("- "):
            break
        key, value = _split_key_value(content)
        idx += 1
        if value is None:
            if idx < len(lines) and lines[idx][0] > cur_indent:
                nested, idx = _parse_block(lines, idx, lines[idx][0])
                d[key] = nested
            else:
                d[key] = None
        else:
            d[key] = _parse_scalar(value)
    return d, idx


def mini_safe_load(text: str) -> Any:
    text = _strip_code_fence(text)
    if not text.strip():
        return None
    lines = _logical_lines(text)
    if not lines:
        return None
    data, idx = _parse_block(lines, 0, lines[0][0])
    if idx != len(lines):
        raise MiniYamlError(f"Could not parse all lines; stopped at line {idx + 1}")
    return data


def safe_load_yaml(text: str) -> LoadedYaml:
    text = _strip_code_fence(text)
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        return LoadedYaml(data=data, parser="pyyaml")
    except ModuleNotFoundError:
        return LoadedYaml(data=mini_safe_load(text), parser="mini")
    except Exception as exc:
        # If PyYAML is present and the YAML is invalid, do not guess with fallback.
        raise MiniYamlError(f"YAML parse failed: {exc}") from exc


def dump_yaml_subset(data: Any, indent: int = 0) -> str:
    sp = " " * indent
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{sp}{k}:")
                lines.append(dump_yaml_subset(v, indent + 2))
            else:
                lines.append(f"{sp}{k}: {_format_scalar(v)}")
        return "\n".join(lines)
    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, dict):
                if not item:
                    lines.append(f"{sp}- {{}}")
                else:
                    first = True
                    for k, v in item.items():
                        if first:
                            if isinstance(v, (dict, list)):
                                lines.append(f"{sp}- {k}:")
                                lines.append(dump_yaml_subset(v, indent + 4))
                            else:
                                lines.append(f"{sp}- {k}: {_format_scalar(v)}")
                            first = False
                        else:
                            if isinstance(v, (dict, list)):
                                lines.append(f"{sp}  {k}:")
                                lines.append(dump_yaml_subset(v, indent + 4))
                            else:
                                lines.append(f"{sp}  {k}: {_format_scalar(v)}")
            elif isinstance(item, list):
                lines.append(f"{sp}-")
                lines.append(dump_yaml_subset(item, indent + 2))
            else:
                lines.append(f"{sp}- {_format_scalar(item)}")
        return "\n".join(lines)
    return f"{sp}{_format_scalar(data)}"


def _format_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    s = str(value)
    if s == "" or re.search(r"[:#\n\[\]{}]|^[-]|\s$|^\s", s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def get_path(data: Any, path: str, default: Any = None) -> Any:
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().strip('"\'') in PLACEHOLDERS
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def require_nonplaceholder(data: Any, path: str, issues: list[str]) -> Any:
    val = get_path(data, path)
    if is_placeholder(val):
        issues.append(f"{path} is missing or placeholder")
    return val


def require_equal(data: Any, path: str, expected: Any, issues: list[str]) -> None:
    val = get_path(data, path)
    if val != expected:
        issues.append(f"{path} must be {expected!r}, got {val!r}")


def require_bool(data: Any, path: str, expected: bool, issues: list[str]) -> None:
    val = get_path(data, path)
    if val is not expected:
        issues.append(f"{path} must be {expected}, got {val!r}")


def require_list(data: Any, path: str, min_len: int, issues: list[str]) -> list[Any]:
    val = get_path(data, path)
    if not isinstance(val, list) or len(val) < min_len:
        issues.append(f"{path} must be a list with at least {min_len} item(s)")
        return []
    return val


def extract_marked_block(text: str, begin: str, end: str) -> str | None:
    pattern = re.compile(re.escape(begin) + r"\s*(.*?)\s*" + re.escape(end), re.S | re.I)
    m = pattern.search(text)
    if m:
        return m.group(1).strip()
    return None


def extract_yaml_fences(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"```(?:yaml|yml)\s*(.*?)```", text, re.S | re.I)]


def write_failure_report(path: Path, title: str, issues: Iterable[str], extra: str = "") -> None:
    body = f"# {title}\n\n"
    body += "## Issues\n\n" + "\n".join(f"- {issue}" for issue in issues) + "\n"
    if extra:
        body += "\n" + extra.strip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
