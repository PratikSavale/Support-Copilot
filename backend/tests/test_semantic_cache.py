import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.cache_service import SemanticCacheService
from utils.log_parser import extract_diagnostic_signature

class TestSemanticCacheService:
    """Unit tests for the SemanticCacheService with full mocks."""

    @pytest.mark.asyncio
    @patch("services.cache_service.get_chroma_client")
    @patch("services.cache_service.get_collection")
    @patch("services.cache_service.get_embedding_engine")
    async def test_cache_miss(self, mock_get_engine, mock_get_col, mock_get_client):
        """Should return None if no match is found or similarity is below threshold."""
        # Setup mocks
        mock_engine = AsyncMock()
        mock_engine.embed_query = AsyncMock(return_value=[0.1, 0.2])
        mock_get_engine.return_value = mock_engine

        mock_col = MagicMock()
        mock_col.query = MagicMock(return_value={
            "ids": [[]],
            "metadatas": [[]],
            "distances": [[]],
        })
        mock_get_col.return_value = mock_col

        service = SemanticCacheService()
        result = await service.check_cache("how to resolve mapstruct issues")
        
        assert result is None
        mock_engine.embed_query.assert_called_once_with("how to resolve mapstruct issues")
        mock_col.query.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.cache_service.get_chroma_client")
    @patch("services.cache_service.get_collection")
    @patch("services.cache_service.get_embedding_engine")
    async def test_cache_hit_high_similarity(self, mock_get_engine, mock_get_col, mock_get_client):
        """Should return the cached response on a high similarity semantic match."""
        mock_engine = AsyncMock()
        mock_engine.embed_query = AsyncMock(return_value=[0.1, 0.2])
        mock_get_engine.return_value = mock_engine

        mock_col = MagicMock()
        mock_col.query = MagicMock(return_value={
            "ids": [["hash_123"]],
            "metadatas": [[{
                "cached_response": "Restart the MapStruct compiler",
                "sources": json.dumps([{"source_id": "s1", "title": "Mapstruct Guide"}]),
                "hit_count": 5
            }]],
            "distances": [[0.02]], # cosine distance < 0.05 => similarity > 0.95
        })
        mock_get_col.return_value = mock_col
        mock_col.update = MagicMock()

        service = SemanticCacheService()
        result = await service.check_cache("how to resolve mapstruct issues")

        assert result is not None
        assert result["response"] == "Restart the MapStruct compiler"
        assert result["sources"][0]["source_id"] == "s1"
        mock_col.update.assert_called_once_with(
            ids=["hash_123"],
            metadatas=[{
                "cached_response": "Restart the MapStruct compiler",
                "sources": json.dumps([{"source_id": "s1", "title": "Mapstruct Guide"}]),
                "hit_count": 6
            }]
        )

    @pytest.mark.asyncio
    @patch("services.cache_service.get_chroma_client")
    @patch("services.cache_service.get_collection")
    @patch("services.cache_service.get_embedding_engine")
    async def test_cache_miss_low_similarity(self, mock_get_engine, mock_get_col, mock_get_client):
        """Should return None if match similarity is below threshold."""
        mock_engine = AsyncMock()
        mock_engine.embed_query = AsyncMock(return_value=[0.1, 0.2])
        mock_get_engine.return_value = mock_engine

        mock_col = MagicMock()
        mock_col.query = MagicMock(return_value={
            "ids": [["hash_123"]],
            "metadatas": [[{
                "cached_response": "Unrelated answer",
                "sources": "[]"
            }]],
            "distances": [[0.15]], # similarity = 0.85 < 0.95
        })
        mock_get_col.return_value = mock_col

        service = SemanticCacheService()
        result = await service.check_cache("how to resolve mapstruct issues")

        assert result is None

    @pytest.mark.asyncio
    @patch("services.cache_service.get_chroma_client")
    @patch("services.cache_service.get_collection")
    @patch("services.cache_service.get_embedding_engine")
    async def test_store_cache(self, mock_get_engine, mock_get_col, mock_get_client):
        """Should upsert new items to semantic cache collection."""
        mock_engine = AsyncMock()
        mock_engine.embed_query = AsyncMock(return_value=[0.1, 0.2])
        mock_get_engine.return_value = mock_engine

        mock_col = MagicMock()
        mock_col.upsert = MagicMock()
        mock_get_col.return_value = mock_col

        service = SemanticCacheService()
        await service.store_cache(
            query="how to fix mapstruct",
            response="Restart compiler",
            sources=[{"source_id": "s1", "title": "Mapstruct Guide"}],
            knowledge_source_ids=["s1"]
        )

        mock_col.upsert.assert_called_once()
        args, kwargs = mock_col.upsert.call_args
        assert kwargs["documents"] == ["how to fix mapstruct"]
        assert kwargs["metadatas"][0]["cached_response"] == "Restart compiler"

    @patch("services.cache_service.get_chroma_client")
    @patch("services.cache_service.get_collection")
    @patch("services.cache_service.get_embedding_engine")
    def test_invalidate_cache(self, mock_get_engine, mock_get_col, mock_get_client):
        """Should delete items matching source_id from collection."""
        mock_col = MagicMock()
        mock_col.delete = MagicMock()
        mock_get_col.return_value = mock_col

        service = SemanticCacheService()
        service.invalidate_cache("s1")

        mock_col.delete.assert_called_once_with(where={"source_id": "s1"})


class TestLogParser:
    """Unit tests for the local regular-expression log trace parser."""

    def test_java_stack_trace_extraction(self):
        log = """
        Exception in thread "main" java.lang.NullPointerException: Cannot invoke "Object.toString()"
            at com.example.orderservice.config.PaymentGatewayConfig.initialize(PaymentGatewayConfig.java:58)
            at com.example.orderservice.OrderApplication.main(OrderApplication.java:12)
        """
        signature = extract_diagnostic_signature(log)
        assert signature == "NullPointerException in PaymentGatewayConfig.initialize line 58"

    def test_python_traceback_extraction(self):
        log = """
        Traceback (most recent call last):
          File "/app/web/views.py", line 42, in index_view
            res = 1 / 0
        ZeroDivisionError: division by zero
        """
        signature = extract_diagnostic_signature(log)
        assert signature == "ZeroDivisionError in views.py.index_view line 42"

    def test_node_stack_trace_extraction(self):
        log = """
        TypeError: Cannot read properties of undefined (reading 'fetch')
            at Object.initialize (/app/src/db.js:89:12)
            at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
        """
        signature = extract_diagnostic_signature(log)
        assert signature == "TypeError in db.js.initialize line 89"

    def test_generic_exception_fallback(self):
        log = "We hit a critical IllegalStateException during execution"
        signature = extract_diagnostic_signature(log)
        assert signature == "Exception: We hit a critical IllegalStateException during execution"

    def test_empty_log_returns_none(self):
        assert extract_diagnostic_signature("") is None
        assert extract_diagnostic_signature("Hello world! Everything is perfect.") is None
