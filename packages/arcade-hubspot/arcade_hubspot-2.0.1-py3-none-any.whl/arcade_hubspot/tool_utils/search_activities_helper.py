"""Helper functions for activity search tools."""

from typing import Any


def truncate_string(text: str | None, max_len: int = 100) -> str | None:
    """Truncate a string to max length, adding [...] if truncated."""
    if not text or not isinstance(text, str):
        return text
    if len(text) <= max_len:
        return text
    return text[:max_len] + "[...]"


def _truncate_nested_dict(value: dict[str, Any]) -> dict[str, Any]:
    """Recursively truncate nested dictionary string values."""
    truncated_nested: dict[str, Any] = {}
    for nested_key, nested_value in value.items():
        if isinstance(nested_value, str):
            truncated_nested[nested_key] = truncate_string(nested_value, 100)
        else:
            truncated_nested[nested_key] = nested_value
    return truncated_nested


def truncate_search_results(
    results: list[dict[str, Any]], should_truncate: bool = True
) -> list[dict[str, Any]]:
    """Truncate string fields in search results. Skip truncation if only 1 result."""
    if not should_truncate or len(results) <= 1:
        return results

    truncated_results = []
    for result in results:
        truncated_result: dict[str, Any] = {}
        for key, value in result.items():
            if isinstance(value, str):
                truncated_result[key] = truncate_string(value, 100)
            elif isinstance(value, dict):
                truncated_result[key] = _truncate_nested_dict(value)
            else:
                truncated_result[key] = value
        truncated_results.append(truncated_result)

    return truncated_results
