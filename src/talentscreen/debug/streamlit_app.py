"""Minimal Streamlit debug UI — dense → rerank → citations."""

from __future__ import annotations

import json

import httpx
import streamlit as st

API_BASE = "http://localhost:8000"


def main() -> None:
    st.set_page_config(page_title="TalentScreen Debug", layout="wide")
    st.title("TalentScreen — RAG Debug (Phase 1a)")
    st.caption("Dense retrieval → cross-encoder rerank → LLM answer with citations")

    with st.sidebar:
        st.header("Settings")
        api_base = st.text_input("API base URL", value=API_BASE)
        tenant_id = st.text_input("Tenant ID", value="demo-tenant")
        top_k = st.slider("Top K", min_value=1, max_value=15, value=5)
        doc_type = st.selectbox(
            "Doc type filter",
            ["(all)", "resume", "interview_notes", "job_description"],
        )
        generate_answer = st.checkbox("Generate LLM answer", value=True)
        use_cache = st.checkbox("Use Redis cache", value=True)
        retrieval_mode = st.selectbox("Retrieval mode", ["hybrid", "dense"], index=0)

        if st.button("Check /degraded"):
            try:
                resp = httpx.get(f"{api_base}/degraded", timeout=10.0)
                st.json(resp.json())
            except Exception as exc:
                st.error(str(exc))

    query = st.text_area(
        "Recruiter query",
        value="Who has Java and AWS experience?",
        height=100,
    )

    if st.button("Run query", type="primary"):
        payload = {
            "query": query,
            "tenant_id": tenant_id,
            "top_k": top_k,
            "generate_answer": generate_answer,
            "use_cache": use_cache,
            "retrieval_mode": retrieval_mode,
        }
        if doc_type != "(all)":
            payload["doc_type"] = doc_type

        with st.spinner("Running pipeline..."):
            try:
                resp = httpx.post(f"{api_base}/query", json=payload, timeout=180.0)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as exc:
                st.error(f"API error {exc.response.status_code}: {exc.response.text}")
                return
            except Exception as exc:
                st.error(str(exc))
                return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Cache", data.get("cache_type") or ("hit" if data.get("cache_hit") else "miss"))
        col2.metric("Dense hits", data.get("dense_hit_count", 0))
        col3.metric("Fused hits", data.get("fused_hit_count", 0))
        col4.metric("Reranked", len(data.get("hits", [])))

        st.subheader("Query processing")
        rewrites = data.get("rewritten_queries") or []
        if rewrites:
            st.write("**LLM rewritten variants:**")
            for v in rewrites:
                st.code(v)
        st.write(f"**Sanitized:** {data.get('sanitized_query')}")
        st.write(f"**Expanded:** {data.get('expanded_query')}")
        if data.get("expansion_terms"):
            st.write(f"**Terms added:** {', '.join(data['expansion_terms'])}")
        if data.get("pii_entities"):
            engine = data.get("pii_engine")
            entities = ", ".join(data["pii_entities"])
            st.warning(f"PII detected ({engine}): {entities}")

        st.subheader("Reranked chunks")
        for i, hit in enumerate(data.get("hits", []), start=1):
            label = hit.get("filename", hit.get("doc_type"))
            with st.expander(
                f"#{i} score={hit.get('score', 0):.3f} "
                f"(dense={hit.get('dense_score', 'n/a')}) — {label}"
            ):
                st.markdown(f"**chunk_id:** `{hit.get('chunk_id')}`")
                st.text(hit.get("text", ""))

        answer = data.get("answer")
        if answer:
            st.subheader("Generated answer")
            st.markdown(answer.get("answer", ""))
            st.write(f"Confidence: {answer.get('confidence', 0):.2f}")
            if answer.get("model"):
                st.caption(f"Model: {answer['model']} (cached={answer.get('llm_cached')})")

            citations = answer.get("citations") or []
            if citations:
                st.subheader("Citations")
                for cite in citations:
                    st.markdown(f"- `{cite.get('chunk_id')}`: _{cite.get('quote', '')}_")

            validation = answer.get("citation_validation") or {}
            if validation.get("invalid_chunk_ids"):
                st.error(f"Invalid citations: {validation['invalid_chunk_ids']}")

        if data.get("generation_error"):
            st.warning(f"Generation error (retrieval succeeded): {data['generation_error']}")

        if data.get("trace_id"):
            st.info(f"Langfuse trace_id: `{data['trace_id']}`")

        with st.expander("Raw JSON"):
            st.code(json.dumps(data, indent=2), language="json")


if __name__ == "__main__":
    main()
