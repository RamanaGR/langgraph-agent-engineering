from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ParserChoice(StrEnum):
    DOCLING = "docling"
    UNSTRUCTURED = "unstructured"


@dataclass
class ParsedDocument:
    text: str
    parser_used: str
    metadata: dict


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def choose_parser(filename: str, mime_type: str | None = None) -> ParserChoice:
    """Route files to Docling (structured PDF/DOCX) or Unstructured (text logs)."""
    suffix = Path(filename).suffix.lower()
    if suffix in {".pdf", ".docx", ".doc"}:
        return ParserChoice.DOCLING
    if suffix in {".md", ".txt", ".log"}:
        return ParserChoice.UNSTRUCTURED
    if mime_type:
        if mime_type in {"application/pdf", DOCX_MIME}:
            return ParserChoice.DOCLING
        if mime_type.startswith("text/"):
            return ParserChoice.UNSTRUCTURED
    return ParserChoice.UNSTRUCTURED
