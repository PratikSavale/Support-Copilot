"""AI helper utilities (Person 2)."""

import re

_ERROR_PATTERNS = re.compile(r"(error|err_|exception|traceback|\b\d{3,}\b)", re.I)
_STEP_PATTERNS = re.compile(
    r"(step\s*\d|\d+\.\s|first|then|finally|navigate|click|run|execute)", re.I
)
_RESOLUTION_PATTERNS = re.compile(
    r"(solution|resolve|fix|workaround|restart|reinstall|update|configure)", re.I
)


def compute_completeness_score(chunks: list[str]) -> float:
    """Heuristic completeness score in range [0.0, 1.0]."""
    if not chunks:
        return 0.0

    combined = " ".join(chunks)
    has_errors = bool(_ERROR_PATTERNS.search(combined))
    has_steps = bool(_STEP_PATTERNS.search(combined))
    has_resolution = bool(_RESOLUTION_PATTERNS.search(combined))
    return round((has_errors + has_steps + has_resolution) / 3.0, 4)


def truncate_excerpt(text: str, max_chars: int = 200) -> str:
    """Return compact excerpt for source snippets."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."
