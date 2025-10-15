"""
Moss Semantic Search SDK

Powerful Python SDK for semantic search using state-of-the-art embedding models.

Example:
    ```python
    from inferedge_moss import MossClient, DocumentInfo, AddDocumentsOptions

    client = MossClient('your-project-id', 'your-project-key')

    # Create documents
    docs = [DocumentInfo(id="1", text="Example document")]

    # Create index with documents
    await client.create_index('my-index', docs, 'moss-minilm')

    # Load an existing index from cloud storage
    index_id = await client.load_index('my-knowledge-base')
    results = await client.query(index_id, 'search query')
    ```
"""

# Re-export core types for convenience
from moss_core import (
    AddDocumentsOptions,
    DocumentInfo,
    GetDocumentsOptions,
    IndexInfo,
    IndexStatus,
    IndexStatusValues,
    ModelRef,
    QueryResultDocumentInfo,
    SearchResult,
)

from .client.moss_client import MossClient
from .pipecat.moss_context_retriever import MossContextRetriever

__version__ = "1.0.0-beta.4"

__all__ = [
    "MossClient",
    "MossContextRetriever",  # for pipecat
    # Core data types
    "DocumentInfo",
    "AddDocumentsOptions",
    "GetDocumentsOptions",
    "IndexInfo",
    "SearchResult",
    "QueryResultDocumentInfo",
    "ModelRef",
    "IndexStatus",
    "IndexStatusValues",
]
