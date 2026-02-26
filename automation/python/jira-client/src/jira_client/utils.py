"""Utilities for converting between plain text and Atlassian Document Format (ADF)."""

from typing import Any


def text_to_adf(text: str) -> dict[str, Any]:
    """Convert plain text to Atlassian Document Format (ADF).

    Blank lines delimit paragraphs; single newlines become hard breaks.
    """
    paragraphs = []
    for para in text.split("\n\n"):
        lines = para.strip().split("\n")
        content: list[dict[str, Any]] = []
        for i, line in enumerate(lines):
            if line:
                content.append({"type": "text", "text": line})
            if i < len(lines) - 1 and line:
                content.append({"type": "hardBreak"})
        if content:
            paragraphs.append({"type": "paragraph", "content": content})

    if not paragraphs:
        paragraphs = [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]

    return {"type": "doc", "version": 1, "content": paragraphs}


def adf_to_text(adf: dict[str, Any] | str | None) -> str | None:
    """Extract plain text from an ADF document.

    Returns None if the input is empty or None.
    """
    if not adf:
        return None
    if isinstance(adf, str):
        return adf or None

    texts: list[str] = []

    def _traverse(node: dict[str, Any]) -> None:
        node_type = node.get("type")
        if node_type == "text":
            texts.append(node.get("text", ""))
        elif node_type == "hardBreak":
            texts.append("\n")
        for child in node.get("content", []):
            _traverse(child)
        if node_type == "paragraph" and texts and texts[-1] != "\n":
            texts.append("\n")

    _traverse(adf)
    return "".join(texts).strip() or None
