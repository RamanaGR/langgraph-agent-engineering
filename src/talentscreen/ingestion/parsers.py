from pathlib import Path

from talentscreen.ingestion.router import ParsedDocument


def parse_plain_text(file_bytes: bytes, filename: str) -> ParsedDocument:
    """Fast path for .txt / .md / .log without heavy Unstructured extras."""
    text = file_bytes.decode("utf-8", errors="replace").strip()
    suffix = Path(filename).suffix.lower()
    return ParsedDocument(
        text=text,
        parser_used="plain_text",
        metadata={"source_filename": filename, "format": suffix or ".txt"},
    )


def parse_with_docling(file_bytes: bytes, filename: str) -> ParsedDocument:
    """Parse structured resumes with Docling (tables/headers preserved)."""
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise ImportError(
            "Docling not installed. Run: uv sync --extra docling"
        ) from exc

    suffix = filename.rsplit(".", 1)[-1].lower()
    suffix_map = {"pdf": ".pdf", "docx": ".docx", "doc": ".doc"}
    ext = suffix_map.get(suffix, ".pdf")

    import tempfile

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        converter = DocumentConverter()
        result = converter.convert(str(tmp_path))
        text = result.document.export_to_markdown()
        return ParsedDocument(
            text=text,
            parser_used="docling",
            metadata={"source_filename": filename, "format": ext},
        )
    finally:
        tmp_path.unlink(missing_ok=True)


def parse_with_unstructured(file_bytes: bytes, filename: str) -> ParsedDocument:
    """Parse with Unstructured.io; falls back to plain text if extras are missing."""
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md", ".log"}:
        try:
            return _parse_with_unstructured_text(file_bytes, filename, suffix)
        except ImportError:
            return parse_plain_text(file_bytes, filename)

    from io import BytesIO

    from unstructured.partition.auto import partition

    elements = partition(file=BytesIO(file_bytes), metadata_filename=filename)
    text = "\n\n".join(str(el) for el in elements)
    return ParsedDocument(
        text=text,
        parser_used="unstructured",
        metadata={"source_filename": filename, "element_count": len(elements)},
    )


def _parse_with_unstructured_text(file_bytes: bytes, filename: str, suffix: str) -> ParsedDocument:
    from io import BytesIO

    if suffix == ".md":
        try:
            from unstructured.partition.md import partition_md

            elements = partition_md(file=BytesIO(file_bytes), metadata_filename=filename)
            parser = "unstructured_md"
        except ImportError:
            return parse_plain_text(file_bytes, filename)
    else:
        from unstructured.partition.text import partition_text

        elements = partition_text(text=file_bytes.decode("utf-8", errors="replace"))
        parser = "unstructured_text"

    text = "\n\n".join(str(el) for el in elements)
    return ParsedDocument(
        text=text,
        parser_used=parser,
        metadata={"source_filename": filename, "element_count": len(elements)},
    )
