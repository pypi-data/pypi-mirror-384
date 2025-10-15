# moss_client.py
from __future__ import annotations

from typing import Dict, List, Optional

from moss_core import (
    AddDocumentsOptions,
    DocumentInfo,
    GetDocumentsOptions,
    IndexInfo,
    SearchResult,
)

from ..services.moss_service import MossService


class MossClient:
    """
    Semantic search client for vector similarity operations.

    Example:
        ```python
        client = MossClient('your-project-id', 'your-project-key')

        # Create an index with documents
        await client.create_index('docs', [
            {'id': '1', 'text': 'Machine learning fundamentals'},
            {'id': '2', 'text': 'Deep learning neural networks'}
        ], 'moss-minilm')

        # Load index from cloud and query
        await client.load_index('docs')
        results = await client.query('docs', 'AI and neural networks')
        ```
    """

    def __init__(self, project_id: str, project_key: str) -> None:
        """
        Creates a new MossClient instance with cloud capabilities.

        Args:
            project_id: Your project ID for cloud authentication
            project_key: Your project key for cloud authentication
        """
        self._internal = MossService(project_id, project_key)

    # ---------- Index lifecycle ----------

    async def create_index(
        self, index_name: str, docs: List[DocumentInfo], model_id: str
    ) -> bool:
        """
        Create a new index and populate it with documents.
        """
        return await self._internal.create_index(index_name, docs, model_id)

    async def get_index(self, index_name: str) -> IndexInfo:
        """
        Get information about a specific index.
        """
        return await self._internal.get_index(index_name)

    async def list_indexes(self) -> List[IndexInfo]:
        """
        List all indexes with their information.
        """
        return await self._internal.list_indexes()

    async def delete_index(self, index_name: str) -> bool:
        """
        Delete an index and all its data.
        """
        return await self._internal.delete_index(index_name)

    # ---------- Document mutations ----------

    async def add_docs(
        self,
        index_name: str,
        docs: List[DocumentInfo],
        options: Optional[AddDocumentsOptions] = None,
    ) -> Dict[str, int]:
        """
        Add or update documents in an index.
        """
        return await self._internal.add_docs(index_name, docs, options)

    async def delete_docs(self, index_name: str, doc_ids: List[str]) -> Dict[str, int]:
        """
        Delete documents from an index by their IDs.
        """
        return await self._internal.delete_docs(index_name, doc_ids)

    # ---------- View existing documents ----------

    async def get_docs(
        self,
        index_name: str,
        options: Optional[GetDocumentsOptions] = None,
    ) -> List[DocumentInfo]:
        """
        Retrieve documents from an index.
        """
        return await self._internal.get_docs(index_name, options)

    # ---------- Index loading & querying ----------

    async def load_index(self, index_name: str) -> str:
        """
        Load an index from a local .moss file into memory.
        """
        return await self._internal.load_index(index_name)

    async def query(self, index_name: str, query: str, top_k: int = 5) -> SearchResult:
        """
        Perform a semantic similarity search against the specified index.
        """
        return await self._internal.query(index_name, query, top_k)
