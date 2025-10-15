# index_service.py
from __future__ import annotations

from typing import Dict, List, Literal, Optional

from moss_core import Index  # PyO3-bound Rust class
from moss_core import (
    DocumentInfo,
    SearchResult,
    SerializedIndex,
)

from .embedding_service import EmbeddingService

MossModel = Literal["moss-minilm", "moss-mediumlm"]


class IndexService:
    def __init__(self) -> None:
        # In-memory registry of indices, backed by Rust via PyO3
        self._indexes: Dict[str, Index] = {}
        # Track the model id for each index so we can embed with the right model
        self._index_models: Dict[str, str] = {}
        # Store full document information for query result mapping
        self._index_documents: Dict[str, Dict[str, DocumentInfo]] = {}
        # Cache embedding services by model ID to avoid repeated initialization
        self._embedding_services: Dict[str, EmbeddingService] = {}

    async def _get_embedding_service(self, model_id: str) -> EmbeddingService:
        """Get or create an embedding service for the given model ID."""
        if model_id not in self._embedding_services:
            embedding_service = EmbeddingService(
                model_id=model_id, normalize=True, quantized=False
            )
            await embedding_service.load_model()
            self._embedding_services[model_id] = embedding_service
        return self._embedding_services[model_id]

    # ---------- Index lifecycle ----------
    async def create_index_from_serialized(
        self, data: SerializedIndex, documents: Optional[List[DocumentInfo]] = None
    ) -> Index:
        if data.name in self._indexes:
            raise ValueError(f"Index with name '{data.name}' already exists")

        # Construct with the serialized model id
        index = Index(data.name, data.model.id)
        # Rust deserialize is sync
        index.deserialize(data)

        # Initialize embedding service for this model
        await self._get_embedding_service(data.model.id)

        self._indexes[data.name] = index
        self._index_models[data.name] = data.model.id

        # Store documents for query mapping if provided
        if documents:
            self._index_documents[data.name] = {doc.id: doc for doc in documents}
        else:
            self._index_documents[data.name] = {}

        return index

    # ---------- Querying ----------

    async def query(self, index_name: str, query: str, top_k: int = 5) -> SearchResult:
        import time

        start_time = time.time()

        index = self._indexes.get(index_name)
        if not index:
            raise KeyError(f"Index '{index_name}' not found")

        model_str = self._index_models[index_name]
        embedding_service = await self._get_embedding_service(model_str)
        q_emb = await embedding_service.create_embedding(query)

        # Get raw query results from Rust (IDs and scores only)
        raw_result = index.query(query, top_k, q_emb)

        # Get stored documents for this index
        doc_map = self._index_documents.get(index_name, {})

        # Map results back to full document information
        populated_docs = []
        for result_doc in raw_result.docs:
            if result_doc.id in doc_map:
                full_doc = doc_map[result_doc.id]
                # Create a new result doc with full information
                populated_doc = type(
                    "QueryResultDoc",
                    (),
                    {
                        "id": result_doc.id,
                        "score": result_doc.score,
                        "text": full_doc.text,
                        "metadata": getattr(full_doc, "metadata", None),
                    },
                )()
                populated_docs.append(populated_doc)

        # Calculate timing
        time_taken_ms = int((time.time() - start_time) * 1000)

        # Return SearchResult with populated documents
        return type(
            "SearchResult",
            (),
            {
                "docs": populated_docs,
                "query": query,
                "index_name": index_name,
                "time_taken_ms": time_taken_ms,
            },
        )()

    # ---------- Utilities ----------

    def has_index(self, index_name: str) -> bool:
        return index_name in self._indexes
