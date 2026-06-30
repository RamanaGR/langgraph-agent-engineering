
from talentscreen.generation.citations import parse_llm_json, validate_citations
from talentscreen.guardrails.pii import redact_pii
from talentscreen.retrieval.query_expansion import expand_query


def test_expand_query_adds_synonyms() -> None:
    expanded, terms = expand_query("Who has Java and AWS experience?")
    assert "java" in expanded.lower()
    assert any(t in ("spring boot", "ec2", "lambda", "amazon web services") for t in terms)


def test_expand_query_no_match() -> None:
    expanded, terms = expand_query("Tell me about company culture")
    assert expanded == "Tell me about company culture"
    assert terms == []


def test_regex_pii_redaction() -> None:
    result = redact_pii("Contact alice@example.com or 555-123-4567")
    assert "alice@example.com" not in result.redacted_text
    assert "555-123-4567" not in result.redacted_text
    assert result.engine in ("presidio", "regex")


def test_citation_validation_filters_invalid() -> None:
    payload = {
        "answer": "Carol has AWS skills.",
        "citations": [
            {"chunk_id": "valid-id", "quote": "AWS EC2"},
            {"chunk_id": "hallucinated-id", "quote": "fake"},
        ],
        "confidence": 0.8,
    }
    validated = validate_citations(payload, {"valid-id"})
    assert len(validated["citations"]) == 1
    assert validated["citation_validation"]["invalid_chunk_ids"] == ["hallucinated-id"]
    assert validated["citation_validation"]["all_valid"] is False


def test_parse_llm_json_with_fence() -> None:
    raw = '```json\n{"answer": "ok", "citations": [], "confidence": 1}\n```'
    parsed = parse_llm_json(raw)
    assert parsed["answer"] == "ok"


def test_cache_key_stable() -> None:
    from talentscreen.retrieval.cache import _cache_key

    k1 = _cache_key(
        tenant_id="demo",
        query="Java AWS",
        top_k=5,
        doc_type=None,
        generate_answer=True,
    )
    k2 = _cache_key(
        tenant_id="demo",
        query="java aws",
        top_k=5,
        doc_type=None,
        generate_answer=True,
    )
    assert k1 == k2
    assert k1.startswith("ts:cache:query:")
