# moss_service.py
from __future__ import annotations

from typing import Dict, List, Optional

from moss_core import (
    AddDocumentsOptions,
    DocumentInfo,
    GetDocumentsOptions,
    IndexInfo,
    SearchResult,
    SerializedIndex,
)
from moss_core import deserializeFromBinary as deserialize_from_binary

from ..utils.cloud_api_client import CloudApiClient
from ..utils.serializers import CloudApiSerializer
from .index_service import IndexService


class MossService:
    """
    Cloud-based search client that manages indexes through the cloud API.
    """

    def __init__(self, project_id: str, project_key: str) -> None:
        self._index_service = IndexService()
        self._cloud_client = CloudApiClient(project_id, project_key)

    # ---------- Index lifecycle ----------

    async def create_index(
        self, index_name: str, docs: List[DocumentInfo], model_id: str
    ) -> bool:
        return await self._cloud_client.make_request(
            "createIndex",
            {
                "indexName": index_name,
                "docs": [CloudApiSerializer.serialize_document(doc) for doc in docs],
                "modelId": model_id,
            },
        )

    async def get_index(self, index_name: str) -> IndexInfo:
        response = await self._cloud_client.make_request(
            "getIndex", {"indexName": index_name}
        )
        # Convert dict response to IndexInfo object
        return CloudApiSerializer.dict_to_index_info(response)

    async def list_indexes(self) -> List[IndexInfo]:
        response = await self._cloud_client.make_request("listIndexes")
        # Convert list of dicts to list of IndexInfo objects
        return [CloudApiSerializer.dict_to_index_info(idx) for idx in response]

    async def delete_index(self, index_name: str) -> bool:
        return await self._cloud_client.make_request(
            "deleteIndex", {"indexName": index_name}
        )

    # ---------- Document mutations ----------

    async def add_docs(
        self,
        index_name: str,
        docs: List[DocumentInfo],
        options: Optional[AddDocumentsOptions] = None,
    ) -> Dict[str, int]:
        if not docs:
            return {"added": 0, "updated": 0}

        return await self._cloud_client.make_request(
            "addDocs",
            {
                "indexName": index_name,
                "docs": [CloudApiSerializer.serialize_document(doc) for doc in docs],
                "options": CloudApiSerializer.serialize_options(options),
            },
        )

    async def delete_docs(self, index_name: str, doc_ids: List[str]) -> Dict[str, int]:
        if not doc_ids:
            return {"deleted": 0}

        return await self._cloud_client.make_request(
            "deleteDocs",
            {
                "indexName": index_name,
                "docIds": doc_ids,
            },
        )

    # ---------- Document retrieval ----------

    async def get_docs(
        self,
        index_name: str,
        options: Optional[GetDocumentsOptions] = None,
    ) -> List[DocumentInfo]:
        response = await self._cloud_client.make_request(
            "getDocs",
            {
                "indexName": index_name,
                "options": CloudApiSerializer.serialize_options(options),
            },
        )

        # Convert response to DocumentInfo objects if needed
        return CloudApiSerializer.convert_documents_response(response)

    # ---------- Querying & loading ----------

    async def load_index(self, index_name: str) -> str:
        # First check if index is already loaded in memory
        if self._index_service.has_index(index_name):
            return index_name

        # Get index URLs from cloud
        try:
            response = await self._cloud_client.make_request(
                "getIndexUrl", {"indexName": index_name}
            )

            # Cloud API returns camelCase field names
            index_url = response.get("indexUrl")
            json_url = response.get("jsonUrl")

            if not response or not index_url:
                raise ValueError(
                    f"Index '{index_name}' not found or has no associated URL"
                )

            # Download the index binary data from the URL
            import httpx

            async with httpx.AsyncClient() as client:
                # Download binary index data
                binary_response = await client.get(index_url)
                binary_response.raise_for_status()
                binary_data = binary_response.content

                # Download documents JSON
                docs_response = await client.get(json_url)
                docs_response.raise_for_status()
                documents = docs_response.json()

            # Deserialize and load the index
            serialized_index: SerializedIndex = deserialize_from_binary(binary_data)

            # Convert document dictionaries to DocumentInfo objects
            document_infos = []
            if documents:
                for doc_dict in documents:
                    doc_info = DocumentInfo(
                        id=doc_dict["id"],
                        text=doc_dict["text"],
                        metadata=doc_dict.get("metadata"),
                    )
                    document_infos.append(doc_info)

            await self._index_service.create_index_from_serialized(
                serialized_index, document_infos
            )

            return index_name

        except Exception as e:
            raise RuntimeError(
                f"Failed to load index '{index_name}' from cloud: {e}"
            ) from e

    async def query(self, index_name: str, query: str, top_k: int = 5) -> SearchResult:
        if not self._index_service.has_index(index_name):
            raise ValueError(
                f"Index '{index_name}' not found, please load the index first before querying"
            )
        return await self._index_service.query(index_name, query, top_k)

    # ---------- Utilities ----------

    def has_index(self, index_name: str) -> bool:
        return self._index_service.has_index(index_name)
