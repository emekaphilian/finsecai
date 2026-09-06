import asyncio

from app.core.config import settings
from app.db.models import EvidenceChunk, Incident, Tenant
from app.services.evidence_ingestion import embed_evidence_chunks
from app.services.evidence_retrieval import retrieve_relevant_evidence
from app.services.intelligence_service import analyze


def test_missing_cohere_api_key_results_in_explicit_failure(db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.cohere_api_key", "", raising=False)

    tenant = Tenant(name="Cohere Failure Tenant")
    db_session.add(tenant)
    db_session.flush()

    incident = Incident(
        tenant_id=tenant.id,
        user_id="u-1",
        amount=5000.0,
        risk_score=0.82,
        anomaly_score=0.75,
    )
    db_session.add(incident)
    db_session.commit()

    analysis = asyncio.run(analyze(db_session, tenant.id, incident))

    assert analysis["analysis_json"]["intelligence_status"] == "COHERE_API_KEY_MISSING"
    assert analysis["analysis_json"]["llm_provider"] is None
    assert analysis["analysis_json"]["retrieval_method"] == "disabled_non_postgres"


def test_embed_evidence_chunks_reports_embedding_failure_without_crashing(db_session, monkeypatch):
    tenant = Tenant(name="Embedding Tenant")
    db_session.add(tenant)
    db_session.flush()

    chunk = EvidenceChunk(
        tenant_id=tenant.id,
        source="high",
        framework_id="CASE-HIGH-0",
        text="A suspicious login attempt from a new device",
    )
    db_session.add(chunk)
    db_session.flush()

    monkeypatch.setattr("app.services.evidence_ingestion.semantic_rag_available", lambda _db: True)

    class BoomService:
        def embed_documents(self, _texts):
            raise RuntimeError("Cohere down")

    monkeypatch.setattr("app.services.evidence_ingestion.get_embedding_provider", BoomService)

    embedded_count = embed_evidence_chunks(db_session, [chunk])

    assert embedded_count == 0
    assert chunk.metadata_json.get("embedding_status") == "failed"
    assert chunk.metadata_json.get("embedding_error") == "Cohere down"


def test_retrieval_fallback_mentions_unavailable_semantic_rag(db_session):
    tenant = Tenant(name="Fallback Tenant")
    db_session.add(tenant)
    db_session.flush()

    chunk = EvidenceChunk(
        tenant_id=tenant.id,
        source="high",
        framework_id="CASE-HIGH-0",
        text="Suspicious account takeover pattern",
    )
    db_session.add(chunk)
    db_session.commit()

    rows = retrieve_relevant_evidence(db_session, tenant.id, "suspicious account takeover", top_k=3)

    assert rows
    assert rows[0]["metadata"]["retrieval_method"] == "disabled_non_postgres"
    assert rows[0]["metadata"]["semantic_rag_available"] is False


def _build_vector(num_ones: int) -> list[float]:
    return [1.0] * num_ones + [0.0] * (settings.cohere_embed_dimension - num_ones)


class DummyEmbeddingService:
    def __init__(self) -> None:
        self.query_vector = _build_vector(512)

    def embed_documents(self, texts):
        mapping = {
            "A": _build_vector(512),
            "B": _build_vector(384),
            "C": _build_vector(256),
            "D": _build_vector(192),
            "E": _build_vector(128),
            "B2": _build_vector(512),
        }
        return [mapping[text] for text in texts]

    def embed_query(self, text):
        return self.query_vector


def test_cohere_similarity_threshold_configured_is_0_40():
    assert settings.cohere_similarity_threshold == 0.40


def test_embedding_provider_factory_uses_explicit_openai_selection(monkeypatch):
    import app.services.cohere_embeddings as embeddings

    class AvailableOpenAI:
        provider_name = "openai"
        model_name = "text-embedding-3-small"

    monkeypatch.setattr(settings, "embedding_provider", "openai")
    monkeypatch.setattr(embeddings, "OpenAIEmbeddingService", AvailableOpenAI)

    service = embeddings.get_embedding_service()

    assert service.provider_name == "openai"
    assert service.model_name == "text-embedding-3-small"


def test_retrieve_relevant_evidence_respects_configured_threshold_and_tenant_isolation(
    db_session, monkeypatch
):
    class DummyDistance:
        def __init__(self, value):
            self.value = value

        def __le__(self, other):
            return ("distance_le", self.value, other)

        def label(self, name):
            return self

    class DummyEmbeddingAttr:
        def cosine_distance(self, query_vector):
            return DummyDistance(0.3)

        def is_not(self, other):
            return ("is_not", other)

    class DummyQuery:
        def __init__(self):
            self.calls = []

        def filter(self, *args):
            self.calls.append(("filter", args))
            return self

        def order_by(self, arg):
            self.calls.append(("order_by", arg))
            return self

        def limit(self, arg):
            self.calls.append(("limit", arg))
            return self

        def all(self):
            chunk = EvidenceChunk(
                id="test-a",
                tenant_id="tenant-a",
                source="A",
                framework_id="TEST-A",
                text="A",
            )
            return [(chunk, 0.3)]

    class DummyEmbeddingServiceA:
        def embed_documents(self, texts):
            return [[1.0] * settings.cohere_embed_dimension for _ in texts]

        def embed_query(self, text):
            return [1.0] * settings.cohere_embed_dimension

    dummy_query = DummyQuery()

    class DummyEvidenceChunk:
        tenant_id = "tenant-a"
        embedding = DummyEmbeddingAttr()

        def __init__(self, id, framework_id, source, text):
            self.id = id
            self.framework_id = framework_id
            self.source = source
            self.text = text
            self.metadata_json = None
            self.embedding_model = None

    monkeypatch.setattr(
        "app.services.evidence_retrieval.get_embedding_provider",
        DummyEmbeddingService,
    )
    monkeypatch.setattr(
        "app.services.evidence_retrieval.semantic_rag_available",
        lambda _db: True,
    )
    monkeypatch.setattr(
        "app.services.evidence_retrieval.EvidenceChunk",
        DummyEvidenceChunk,
    )
    monkeypatch.setattr(db_session, "query", lambda *args: dummy_query)

    results = retrieve_relevant_evidence(db_session, "tenant-a", "query", top_k=3)

    assert len(results) == 1
    assert results[0]["framework_id"] == "TEST-A"
    assert results[0]["similarity"] == 0.7
    assert any(call[0] == "filter" for call in dummy_query.calls)
    assert any(
        call[0] == "filter"
        and any(isinstance(expr, tuple) and expr[0] == "distance_le" for expr in call[1])
        for call in dummy_query.calls
    )
    assert any(call[0] == "order_by" for call in dummy_query.calls)
    assert any(call[0] == "limit" and call[1] == 3 for call in dummy_query.calls)
