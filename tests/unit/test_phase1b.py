"""Phase 1b unit tests — hybrid fusion, metrics, semantic cache."""

from talentscreen.retrieval.hybrid import reciprocal_rank_fusion
from talentscreen.retrieval.semantic_cache import _cosine


def test_rrf_merges_dense_and_bm25() -> None:
    dense = [{"chunk_id": "a", "score": 0.9}, {"chunk_id": "b", "score": 0.8}]
    bm25 = [{"chunk_id": "b", "score": 5.0}, {"chunk_id": "c", "score": 3.0}]
    fused = reciprocal_rank_fusion([dense, bm25])
    ids = [h["chunk_id"] for h in fused]
    assert ids[0] == "b"
    assert set(ids) == {"a", "b", "c"}


def test_rrf_preserves_metadata() -> None:
    ranking = [{"chunk_id": "x", "document_id": "doc-1", "doc_type": "resume", "score": 1.0}]
    fused = reciprocal_rank_fusion([ranking])
    assert fused[0]["document_id"] == "doc-1"
    assert fused[0]["fusion"] == "rrf"


def test_cosine_identical_vectors() -> None:
    v = [1.0, 0.0, 0.0]
    assert _cosine(v, v) == 1.0


def test_f1_at_k_perfect_match() -> None:
    from eval.metrics import f1_at_k

    assert f1_at_k(["a", "b"], ["a", "b"], k=5) == 1.0


def test_keyword_recall_partial() -> None:
    from eval.metrics import keyword_recall_at_k

    texts = ["Alice has Java and AWS skills", "other"]
    score = keyword_recall_at_k(texts, ["Java", "AWS", "Terraform"], k=2)
    assert 0.6 < score < 0.7
