import ast
import json
import re


def parse_skills(raw: object) -> list[str]:
    """Turn dataset skill cells into a unique, lowercase skill list."""
    if raw is None:
        return []
    text = str(raw).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return []

    parsed: object | None = None
    for loader in (json.loads, ast.literal_eval):
        try:
            parsed = loader(text)
            break
        except (ValueError, SyntaxError, json.JSONDecodeError):
            continue

    if isinstance(parsed, list):
        values = parsed
    else:
        values = re.split(r"\s*,\s*", text.strip("[]"))

    seen: list[str] = []
    for item in values:
        skill = str(item).strip().strip("\"'").lower()
        if skill and skill not in seen:
            seen.append(skill)
    return seen


def tokenize(text: object) -> set[str]:
    if text is None:
        return set()
    return {token for token in re.findall(r"[a-z0-9+#]+", str(text).lower()) if len(token) > 1}
