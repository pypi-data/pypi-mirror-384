"""
End-to-End tests for MossClient with cloud API

Prerequisites:
- Set MOSS_TEST_PROJECT_ID environment variable
- Set MOSS_TEST_PROJECT_KEY environment variable
- Ensure cloud API is accessible
"""

from __future__ import annotations

import os
import warnings
from typing import List

import pytest

from inferedge_moss import (
    AddDocumentsOptions,
    DocumentInfo,
    GetDocumentsOptions,
    MossClient,
)
from tests.constants import (
    ADDITIONAL_TEST_DOCUMENTS,
    TEST_DOCUMENTS,
    TEST_INDEX_NAME,
    TEST_MODEL_ID,
    TEST_PROJECT_ID,
    TEST_PROJECT_KEY,
    TEST_QUERIES,
)

# Global variables for test state
client = None
created_indexes = []


@pytest.fixture(scope="module", autouse=True)
def setup_and_cleanup():
    """Setup test environment and cleanup after tests."""
    global client, created_indexes

    # Validate environment variables
    if not os.getenv("MOSS_TEST_PROJECT_ID") or not os.getenv("MOSS_TEST_PROJECT_KEY"):
        warnings.warn(
            "Warning: Using default test credentials. Set MOSS_TEST_PROJECT_ID and "
            "MOSS_TEST_PROJECT_KEY env vars for actual testing."
        )

    # Initialize client with project credentials
    client = MossClient(TEST_PROJECT_ID, TEST_PROJECT_KEY)
    created_indexes = []

    yield


class TestMossClientE2E:
    """End-to-End tests for MossClient with cloud API."""

    # Index Lifecycle Operations
    class TestIndexLifecycle:
        """Test index lifecycle operations."""

        @pytest.mark.asyncio
        async def test_list_indexes_successfully(self):
            """Should list indexes successfully."""
            indexes = await client.list_indexes()

            assert isinstance(indexes, list)

            # Verify structure of index info
            if len(indexes) > 0:
                first_index = indexes[0]
                assert hasattr(first_index, "name")
                assert hasattr(first_index, "doc_count")
                assert hasattr(first_index, "model")

        @pytest.mark.asyncio
        async def test_create_new_index_with_documents(self):
            """Should create a new index with documents."""
            # Convert test documents to DocumentInfo objects
            docs = [
                DocumentInfo(id=doc["id"], text=doc["text"]) for doc in TEST_DOCUMENTS
            ]

            success = await client.create_index(TEST_INDEX_NAME, docs, TEST_MODEL_ID)

            assert success is True
            created_indexes.append(TEST_INDEX_NAME)

        @pytest.mark.asyncio
        async def test_fail_create_existing_index(self):
            """Should fail to create an index that already exists."""
            docs = [
                DocumentInfo(id=doc["id"], text=doc["text"]) for doc in TEST_DOCUMENTS
            ]

            with pytest.raises(Exception):
                await client.create_index(TEST_INDEX_NAME, docs, TEST_MODEL_ID)

        @pytest.mark.asyncio
        async def test_retrieve_index_information(self):
            """Should retrieve index information."""
            index_info = await client.get_index(TEST_INDEX_NAME)

            assert index_info.name == TEST_INDEX_NAME
            assert index_info.doc_count == len(TEST_DOCUMENTS)
            assert index_info.model.id == TEST_MODEL_ID

        @pytest.mark.asyncio
        async def test_fail_get_nonexistent_index(self):
            """Should fail to get non-existent index."""
            with pytest.raises(Exception):
                await client.get_index("non-existent-index")

    # Document Operations
    class TestDocumentOperations:
        """Test document operations."""

        @pytest.mark.asyncio
        async def test_retrieve_documents_from_index(self):
            """Should retrieve documents from index."""
            docs = await client.get_docs(TEST_INDEX_NAME)

            assert len(docs) == len(TEST_DOCUMENTS)

            # Verify document structure
            for doc in docs:
                assert hasattr(doc, "id")
                assert hasattr(doc, "text")
                assert isinstance(doc.id, str)
                assert isinstance(doc.text, str)

            # Verify all test documents are present
            doc_ids = [doc.id for doc in docs]
            for test_doc in TEST_DOCUMENTS:
                assert test_doc["id"] in doc_ids

        @pytest.mark.asyncio
        async def test_retrieve_specific_documents_by_id(self):
            """Should retrieve specific documents by ID."""
            target_doc_ids = ["doc-1", "doc-3"]
            docs = await client.get_docs(
                TEST_INDEX_NAME, GetDocumentsOptions(doc_ids=target_doc_ids)
            )

            assert len(docs) == len(target_doc_ids)

            retrieved_ids = [doc.id for doc in docs]
            for doc_id in target_doc_ids:
                assert doc_id in retrieved_ids

        @pytest.mark.asyncio
        async def test_add_new_documents_to_existing_index(self):
            """Should add new documents to existing index."""
            additional_docs = [
                DocumentInfo(id=doc["id"], text=doc["text"])
                for doc in ADDITIONAL_TEST_DOCUMENTS
            ]

            result = await client.add_docs(TEST_INDEX_NAME, additional_docs)

            assert result["added"] == len(ADDITIONAL_TEST_DOCUMENTS)
            assert result.get("updated", 0) == 0

            # Verify documents were added
            index_info = await client.get_index(TEST_INDEX_NAME)
            assert index_info.doc_count == len(TEST_DOCUMENTS) + len(
                ADDITIONAL_TEST_DOCUMENTS
            )

        @pytest.mark.asyncio
        async def test_update_existing_documents_with_upsert(self):
            """Should update existing documents with upsert."""
            updated_doc = DocumentInfo(
                id="doc-1",
                text="Updated: Machine learning is a powerful subset of artificial intelligence with modern applications.",
            )

            result = await client.add_docs(
                TEST_INDEX_NAME, [updated_doc], AddDocumentsOptions(upsert=True)
            )

            assert result.get("added", 0) == 0
            assert result["updated"] == 1

            # Verify document was updated
            docs = await client.get_docs(
                TEST_INDEX_NAME, GetDocumentsOptions(doc_ids=["doc-1"])
            )
            assert docs[0].text == updated_doc.text

        @pytest.mark.asyncio
        async def test_delete_documents_from_index(self):
            """Should delete documents from index."""
            docs_to_delete = ["doc-6", "doc-7"]
            result = await client.delete_docs(TEST_INDEX_NAME, docs_to_delete)

            assert result["deleted"] == len(docs_to_delete)

            # Verify documents were deleted
            remaining_docs = await client.get_docs(TEST_INDEX_NAME)
            remaining_ids = [doc.id for doc in remaining_docs]

            for doc_id in docs_to_delete:
                assert doc_id not in remaining_ids

    # Search and Query Operations
    class TestSearchAndQuery:
        """Test search and query operations."""

        @pytest.mark.asyncio
        async def test_load_index_successfully(self):
            """Should load index successfully."""
            loaded_index_name = await client.load_index(TEST_INDEX_NAME)
            assert loaded_index_name == TEST_INDEX_NAME

        @pytest.mark.asyncio
        async def test_perform_semantic_search_queries(self):
            """Should perform semantic search queries."""
            for test_query in TEST_QUERIES:
                results = await client.query(TEST_INDEX_NAME, test_query["query"], 3)

                assert hasattr(results, "docs")
                assert isinstance(results.docs, list)
                assert len(results.docs) > 0
                assert len(results.docs) <= 3

                # Verify result structure
                for item in results.docs:
                    assert hasattr(item, "id")
                    assert hasattr(item, "text")
                    assert hasattr(item, "score")
                    assert isinstance(item.id, str)
                    assert isinstance(item.text, str)
                    assert isinstance(item.score, float)
                    assert item.score > 0
                    assert item.score <= 1

                # Verify results are sorted by relevance (descending score)
                for j in range(1, len(results.docs)):
                    assert results.docs[j - 1].score >= results.docs[j].score

        @pytest.mark.asyncio
        async def test_respect_topk_parameter(self):
            """Should respect topK parameter."""
            top_k = 2
            results = await client.query(
                TEST_INDEX_NAME, "artificial intelligence", top_k
            )

            assert len(results.docs) <= top_k

    # Error Handling
    class TestErrorHandling:
        """Test error handling."""

        @pytest.mark.asyncio
        async def test_handle_operations_on_nonexistent_index(self):
            """Should handle operations on non-existent index."""
            non_existent_index = "does-not-exist"

            with pytest.raises(Exception):
                await client.get_docs(non_existent_index)

            with pytest.raises(Exception):
                await client.query(non_existent_index, "test query")

            with pytest.raises(Exception):
                await client.add_docs(
                    non_existent_index, [DocumentInfo(id="test", text="test")]
                )

            with pytest.raises(Exception):
                await client.delete_docs(non_existent_index, ["test"])

        @pytest.mark.asyncio
        async def test_handle_empty_document_arrays_gracefully(self):
            """Should handle empty document arrays gracefully."""
            result = await client.add_docs(TEST_INDEX_NAME, [])
            assert result["added"] == 0
            assert result.get("updated", 0) == 0

        @pytest.mark.asyncio
        async def test_handle_empty_docids_array_for_deletion(self):
            """Should handle empty docIds array for deletion."""
            result = await client.delete_docs(TEST_INDEX_NAME, [])
            assert result["deleted"] == 0

    # Index Cleanup
    class TestIndexCleanup:
        """Test index cleanup."""

        @pytest.mark.asyncio
        async def test_delete_the_test_index(self):
            """Should delete the test index."""
            success = await client.delete_index(TEST_INDEX_NAME)
            assert success is True

            # Remove from cleanup list since we just deleted it
            if TEST_INDEX_NAME in created_indexes:
                created_indexes.remove(TEST_INDEX_NAME)

            # Verify index is deleted
            with pytest.raises(Exception):
                await client.get_index(TEST_INDEX_NAME)
