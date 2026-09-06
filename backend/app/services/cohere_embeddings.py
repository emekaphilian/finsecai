"""Provider-agnostic embeddings for FinSecAI semantic retrieval.

Cohere is the primary implementation. OpenAI is also supported.
Additional embedding providers can be added behind the same contract.
"""

from __future__ import annotations

from typing import Protocol

from app.core.config import settings


class EmbeddingProviderError(RuntimeError):
    """Raised when the configured embedding provider cannot be used."""


class EmbeddingProvider(Protocol):
    """Contract consumed by evidence ingestion and retrieval."""

    provider_name: str
    model_name: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class CohereEmbeddingService:
    """Cohere implementation of the embedding provider contract."""

    provider_name = "cohere"

    def __init__(self) -> None:
        if not settings.cohere_api_key:
            raise EmbeddingProviderError("COHERE_API_KEY is not configured")
        try:
            import cohere
        except Exception as exc:  # pragma: no cover
            raise EmbeddingProviderError("Cohere SDK is not available") from exc

        self.client = cohere.ClientV2(api_key=settings.cohere_api_key)
        self.model_name = settings.cohere_embed_model

    def _embed(self, texts: list[str], input_type: str) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self.client.embed(
                model=self.model_name,
                texts=texts,
                input_type=input_type,
                embedding_types=["float"],
            )
        except Exception as exc:
            raise EmbeddingProviderError("Cohere embedding request failed") from exc
        embeddings = response.embeddings.float
        if any(len(vector) != settings.cohere_embed_dimension for vector in embeddings):
            raise EmbeddingProviderError("Cohere returned an unexpected embedding dimension")
        return embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, "search_document")

    def embed_query(self, text: str) -> list[float]:
        vectors = self._embed([text], "search_query")
        return vectors[0]


class OpenAIEmbeddingService:
    """OpenAI implementation of the embedding provider contract."""

    provider_name = "openai"

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise EmbeddingProviderError("OPENAI_API_KEY is not configured")
        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover
            raise EmbeddingProviderError("OpenAI SDK is not available") from exc
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model_name = settings.openai_embed_model

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self.client.embeddings.create(model=self.model_name, input=texts)
        except Exception as exc:
            raise EmbeddingProviderError("OpenAI embedding request failed") from exc
        vectors = [list(item.embedding) for item in response.data]
        if any(len(vector) != settings.openai_embed_dimension for vector in vectors):
            raise EmbeddingProviderError("OpenAI returned an unexpected embedding dimension")
        if settings.openai_embed_dimension != settings.cohere_embed_dimension:
            raise EmbeddingProviderError(
                "Configured embedding providers must share the pgvector dimension"
            )
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]


def get_embedding_provider() -> EmbeddingProvider:
    """Return the explicitly configured embedding provider."""
    provider_name = (
        getattr(settings, "embedding_provider", None) or "cohere"
    ).strip().lower()
    providers: dict[str, type[EmbeddingProvider]] = {
        "cohere": CohereEmbeddingService,
        "openai": OpenAIEmbeddingService,
    }
    provider_class = providers.get(provider_name)
    if provider_class is None:
        raise EmbeddingProviderError(
            f"Unsupported embedding provider: {provider_name}"
        )
    return provider_class()


# Backward-compatible alias for existing callers.
get_embedding_service = get_embedding_provider
