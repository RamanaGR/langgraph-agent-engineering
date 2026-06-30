from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from talentscreen.config import get_settings

_connected = False


def connect_milvus() -> None:
    global _connected
    if _connected:
        return
    settings = get_settings()
    connections.connect(alias="default", host=settings.milvus_host, port=str(settings.milvus_port))
    _connected = True


def ensure_collection(dimension: int | None = None) -> Collection:
    connect_milvus()
    settings = get_settings()
    dim = dimension or settings.embedding_dimension
    name = settings.milvus_collection

    if utility.has_collection(name):
        collection = Collection(name)
        for field in collection.schema.fields:
            if field.name == "embedding" and field.dtype == DataType.FLOAT_VECTOR:
                if field.params.get("dim") != dim:
                    utility.drop_collection(name)
                break
        if utility.has_collection(name):
            collection.load()
            return collection

    fields = [
        FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
        FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
    ]
    schema = CollectionSchema(fields=fields, description="TalentScreen dense retrieval index")
    collection = Collection(name=name, schema=schema)
    index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {"M": 16, "efConstruction": 200},
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    collection.load()
    return collection


def upsert_vectors(
    chunk_ids: list[str],
    tenant_ids: list[str],
    document_ids: list[str],
    doc_types: list[str],
    embeddings: list[list[float]],
) -> None:
    collection = ensure_collection(len(embeddings[0]) if embeddings else None)
    entities = [chunk_ids, tenant_ids, document_ids, doc_types, embeddings]
    collection.insert(entities)
    collection.flush()


def dense_search(
    query_vector: list[float],
    tenant_id: str,
    top_k: int = 10,
    doc_type: str | None = None,
) -> list[dict]:
    collection = ensure_collection(len(query_vector))
    expr = f'tenant_id == "{tenant_id}"'
    if doc_type:
        expr += f' && doc_type == "{doc_type}"'

    results = collection.search(
        data=[query_vector],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"ef": 64}},
        limit=top_k,
        expr=expr,
        output_fields=["chunk_id", "document_id", "doc_type", "tenant_id"],
    )
    hits = []
    for hit in results[0]:
        hits.append(
            {
                "chunk_id": hit.entity.get("chunk_id"),
                "document_id": hit.entity.get("document_id"),
                "doc_type": hit.entity.get("doc_type"),
                "tenant_id": hit.entity.get("tenant_id"),
                "score": float(hit.distance),
            }
        )
    return hits
