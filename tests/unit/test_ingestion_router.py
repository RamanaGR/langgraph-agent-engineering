import pytest

from talentscreen.ingestion.router import ParserChoice, choose_parser


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("resume.pdf", ParserChoice.DOCLING),
        ("resume.docx", ParserChoice.DOCLING),
        ("notes.txt", ParserChoice.UNSTRUCTURED),
        ("feedback.md", ParserChoice.UNSTRUCTURED),
        ("interview.log", ParserChoice.UNSTRUCTURED),
    ],
)
def test_file_type_router(filename: str, expected: ParserChoice) -> None:
    assert choose_parser(filename) == expected


def test_semantic_chunk_overlap() -> None:
    from talentscreen.ingestion.chunking import semantic_chunk

    text = "Java developer. " * 200
    chunks = semantic_chunk(text, metadata={"doc_type": "resume"})
    assert len(chunks) > 1
    assert all("text" in c and c["text"] for c in chunks)


def test_content_hash_idempotency() -> None:
    from talentscreen.ingestion.pipeline import content_hash

    data = b"same-content"
    assert content_hash(data) == content_hash(data)
    assert content_hash(data) != content_hash(b"other")


def test_bedrock_stub_example_shape() -> None:
    from talentscreen.generation.llm.bedrock_stub import BedrockLLMProvider

    example = BedrockLLMProvider.example_response()
    llm = example.to_llm_response()
    assert llm.cached is True
    assert "claude" in llm.model
