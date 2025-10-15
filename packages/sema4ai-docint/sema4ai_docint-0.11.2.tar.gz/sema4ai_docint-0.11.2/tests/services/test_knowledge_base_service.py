import os
import uuid
from unittest.mock import Mock, patch

import pytest
from sema4ai.data import DataSource, get_connection

from sema4ai_docint.models.constants import PROJECT_NAME
from sema4ai_docint.services._context import _DIContext
from sema4ai_docint.services._knowledge_base_service import _KnowledgeBaseService
from sema4ai_docint.services._setup_kb import _setup_kb
from sema4ai_docint.services.exceptions import KnowledgeBaseServiceError

# Test-specific constants to avoid interacting with production data
TEST_KNOWLEDGE_BASE_NAME = "test_documents"
TEST_PARSED_DOCUMENTS_TABLE_NAME = "test_parsed_documents"


@pytest.fixture
def patch_constants():
    """Fixture to patch constants with test values to avoid production data interaction."""
    patches = [
        # Patch in the constants module
        patch(
            "sema4ai_docint.models.constants.KNOWLEDGE_BASE_NAME",
            TEST_KNOWLEDGE_BASE_NAME,
        ),
        patch(
            "sema4ai_docint.models.constants.PARSED_DOCUMENTS_TABLE_NAME",
            TEST_PARSED_DOCUMENTS_TABLE_NAME,
        ),
        # Patch in the knowledge base service module
        patch(
            "sema4ai_docint.services._knowledge_base_service.KNOWLEDGE_BASE_NAME",
            TEST_KNOWLEDGE_BASE_NAME,
        ),
        patch(
            "sema4ai_docint.services._knowledge_base_service.PARSED_DOCUMENTS_TABLE_NAME",
            TEST_PARSED_DOCUMENTS_TABLE_NAME,
        ),
        # Patch in the setup kb module
        patch(
            "sema4ai_docint.services._setup_kb.KNOWLEDGE_BASE_NAME",
            TEST_KNOWLEDGE_BASE_NAME,
        ),
        patch(
            "sema4ai_docint.services._setup_kb.PARSED_DOCUMENTS_TABLE_NAME",
            TEST_PARSED_DOCUMENTS_TABLE_NAME,
        ),
    ]

    # Start all patches
    for p in patches:
        p.start()

    yield

    # Stop all patches
    for p in patches:
        p.stop()


@pytest.fixture
def cleanup_kb():
    """Fixture for cleaning up knowledge bases after tests."""
    yield

    conn = get_connection()
    conn.execute_sql(f"DROP KNOWLEDGE_BASE IF EXISTS {PROJECT_NAME}.{TEST_KNOWLEDGE_BASE_NAME}")

    test_datasource_name = f"test_postgres_{os.getpid()}"
    try:
        conn.execute_sql(
            f"DROP TABLE IF EXISTS {test_datasource_name}.{TEST_PARSED_DOCUMENTS_TABLE_NAME}"
        )
    except Exception:
        pass


@pytest.fixture
def pgvector_datasource(postgres_datasource):
    """Create a PGVector datasource using postgres credentials."""
    pgvector_db_name = f"doc_int_pgvector_{os.getpid()!s}"

    conn = get_connection()
    connection_data = conn._get_datasource_info(postgres_datasource.datasource_name)[
        "connection_data"
    ]

    sql = f"""
    CREATE DATABASE IF NOT EXISTS {pgvector_db_name}
    WITH ENGINE = 'pgvector',
    PARAMETERS = {{
        "user": "{connection_data.get("user")}",
        "port": {connection_data.get("port", 5432)},
        "password": "{connection_data.get("password")}",
        "host": "{connection_data.get("host")}",
        "database": "{connection_data.get("database")}"
    }}
    """
    conn.execute_sql(sql)

    pgvector_datasource = DataSource.model_validate(datasource_name=pgvector_db_name)

    yield pgvector_datasource

    try:
        get_connection().execute_sql(f"DROP DATABASE IF EXISTS `{pgvector_db_name}`")
    except Exception:
        pass


@pytest.fixture
def kb_context(
    postgres_datasource, extraction_service, pgvector_datasource, agent_server_transport
):
    """
    Create a context with datasource, extraction service, and pgvector for knowledge base tests.

    Includes agent_server_transport so tests can configure file responses for ingest operations.
    """
    return _DIContext(
        datasource=postgres_datasource,
        extraction_service=extraction_service,
        pg_vector=pgvector_datasource,
        agent_server_transport=agent_server_transport,
    )


class TestKnowledgeBaseService:
    @pytest.fixture
    def kb_service(self, kb_context):
        """Create a KnowledgeBaseService instance for testing."""
        return _KnowledgeBaseService(kb_context)

    @pytest.fixture
    def mock_reducto_client(self):
        """Mock Reducto client for testing."""
        mock_client = Mock()
        mock_client.upload.return_value = "test-file-id-123"

        # Create mock chunks that match ResultFullResultChunk structure
        mock_chunk1 = Mock()
        mock_chunk1.model_dump.return_value = {
            "blocks": [
                {
                    "bbox": {
                        "height": 50.0,
                        "left": 50.0,
                        "page": 1,
                        "top": 700.0,
                        "width": 250.0,
                        "original_page": 1,
                    },
                    "content": (
                        "INVOICE\nInvoice Number: INV-00001\nDate: August 20, 2025\n"
                        "Bill To: Avenue University\n123 University Ave\nSuite 456\n"
                        "Dallas, TX 75201"
                    ),
                    "type": "Text",
                    "confidence": "high",
                    "image_url": None,
                }
            ],
            "content": (
                "INVOICE\nInvoice Number: INV-00001\nDate: August 20, 2025\n"
                "Bill To: Avenue University\n123 University Ave\nSuite 456\nDallas, TX 75201"
            ),
            "embed": (
                "INVOICE\nInvoice Number: INV-00001\nDate: August 20, 2025\n"
                "Bill To: Avenue University\n123 University Ave\nSuite 456\nDallas, TX 75201"
            ),
            "enriched": None,
            "enrichment_success": None,
        }

        mock_chunk2 = Mock()
        mock_chunk2.model_dump.return_value = {
            "blocks": [
                {
                    "bbox": {
                        "height": 200.0,
                        "left": 50.0,
                        "page": 1,
                        "top": 400.0,
                        "width": 500.0,
                        "original_page": 1,
                    },
                    "content": (
                        "DESCRIPTION\tQTY\tRATE\tAMOUNT\nServices\t100\t$55.00\t$5,500.00\n"
                        "Support\t50\t$35.00\t$1,750.00\nConsulting\t200\t$50.00\t$10,000.00"
                    ),
                    "type": "Table",
                    "confidence": "high",
                    "image_url": None,
                }
            ],
            "content": (
                "DESCRIPTION\tQTY\tRATE\tAMOUNT\nServices\t100\t$55.00\t$5,500.00\n"
                "Support\t50\t$35.00\t$1,750.00\nConsulting\t200\t$50.00\t$10,000.00"
            ),
            "embed": (
                "DESCRIPTION\tQTY\tRATE\tAMOUNT\nServices\t100\t$55.00\t$5,500.00\n"
                "Support\t50\t$35.00\t$1,750.00\nConsulting\t200\t$50.00\t$10,000.00"
            ),
            "enriched": None,
            "enrichment_success": None,
        }

        mock_chunk3 = Mock()
        mock_chunk3.model_dump.return_value = {
            "blocks": [
                {
                    "bbox": {
                        "height": 150.0,
                        "left": 350.0,
                        "page": 1,
                        "top": 200.0,
                        "width": 200.0,
                        "original_page": 1,
                    },
                    "content": (
                        "SUBTOTAL: $17,250.00\nTAX: $0.00\nTOTAL: $17,250.00\n"
                        "Amount Due: $17,250.00\nDue Date: September 19, 2025"
                    ),
                    "type": "Text",
                    "confidence": "high",
                    "image_url": None,
                }
            ],
            "content": (
                "SUBTOTAL: $17,250.00\nTAX: $0.00\nTOTAL: $17,250.00\n"
                "Amount Due: $17,250.00\nDue Date: September 19, 2025"
            ),
            "embed": (
                "SUBTOTAL: $17,250.00\nTAX: $0.00\nTOTAL: $17,250.00\n"
                "Amount Due: $17,250.00\nDue Date: September 19, 2025"
            ),
            "enriched": None,
            "enrichment_success": None,
        }

        mock_result = Mock()
        mock_result.chunks = [mock_chunk1, mock_chunk2, mock_chunk3]
        mock_result.type = "full"

        mock_document_data = Mock()
        mock_document_data.duration = 2.5
        mock_document_data.job_id = "test-job-123"
        mock_document_data.result = mock_result
        mock_document_data.usage = Mock()
        mock_document_data.usage.num_pages = 1
        mock_document_data.usage.credits = 10.0

        mock_client.parse.return_value = mock_document_data
        return mock_client

    def test_complete_knowledge_base_workflow_with_invoice(
        self,
        setup_db,
        kb_service,
        postgres_datasource,
        mock_reducto_client,
        test_pdf_path,
        cleanup_db,
        cleanup_kb,
        openai_api_key,
        patch_constants,
        agent_server_transport,
    ):
        """Test complete workflow: create KB, ingest INV-00001.pdf, and query for invoice total."""

        kb_service._context.extraction_service._reducto_client = mock_reducto_client

        mock_embedding_config = {
            "provider": "openai",
            "model_name": "text-embedding-3-large",
            "api_key": openai_api_key,
        }
        mock_reranking_config = {
            "provider": "openai",
            "model_name": "gpt-4o",
            "api_key": openai_api_key,
        }

        with patch(
            "sema4ai_docint.services._setup_kb._get_model_configs_from_agent",
            return_value=(mock_embedding_config, mock_reranking_config),
        ):
            agent_server_transport.set_file_responses({"INV-00001.pdf": test_pdf_path})
            with patch("sema4ai_docint.services._knowledge_base_service.TransformDocumentLayout"):
                with patch(
                    "sema4ai_docint.services._knowledge_base_service.TransformDocumentLayout"
                ) as mock_transformer:
                    mock_transformer_instance = Mock()
                    test_document_id = "test-doc-uuid-123"
                    mock_transformer_instance.get_doc_uuid.return_value = test_document_id
                    mock_transformer.return_value = mock_transformer_instance

                    ingest_result = kb_service.ingest("INV-00001.pdf")

                    # The ingest method now returns the document_id directly
                    assert ingest_result == test_document_id

                    query_result = kb_service.query(
                        document_name="INV-00001.pdf",
                        document_id=None,
                        natural_language_query="what is the total of the invoice",
                        relevance=0.7,
                    )

                    # Verify the query result structure and content
                    assert isinstance(query_result, list)
                    assert len(query_result) > 0, "Query should return at least one result"

                    # Check that the results contain the expected invoice total
                    # The invoice total should be $17,250.00 based on the test PDF
                    expected_total = "$17,250.00"
                    found_total = False

                    for result in query_result:
                        content_to_check = []
                        if result.chunk_content:
                            content_to_check.append(result.chunk_content)

                        for content in content_to_check:
                            if expected_total in content:
                                found_total = True
                                break

                        if found_total:
                            break

                    assert found_total, (
                        f"Expected total {expected_total} not found in query results"
                    )

                    # Verify that results have high relevance (should be > 0.7 since that's our
                    # threshold)
                    for result in query_result:
                        assert result.relevance >= 0.7, (
                            f"Result relevance {result.relevance} is below threshold 0.7"
                        )
                        assert result.id is not None
                        assert result.document_name == "INV-00001.pdf"
                        assert result.page_number == 1
                        assert isinstance(result.chunk, dict)

                    mock_reducto_client.upload.assert_called_once_with(test_pdf_path)
                    mock_reducto_client.parse.assert_called_once()

    def test_query_missing_parameters(self, kb_service):
        """Test query when both document_name and document_id are missing."""
        with pytest.raises(
            KnowledgeBaseServiceError,
            match="Either document_name or document_id must be provided",
        ):
            kb_service.query(
                document_name=None,
                document_id=None,
                natural_language_query="test query",
            )

    def test_ingest_no_extraction_service(self, kb_service):
        """Test ingestion when extraction service is not available."""
        kb_service._context.extraction_service = None

        with pytest.raises(KnowledgeBaseServiceError, match="Extraction service is not available"):
            kb_service.ingest("test_document.pdf")

    def test_ingest_no_content_found(
        self,
        setup_db,
        kb_service,
        postgres_datasource,
        test_pdf_path,
        cleanup_db,
        agent_server_transport,
    ):
        """Test ingestion when no content is found in document."""
        # Mock Reducto client to return no content
        mock_client = Mock()
        mock_client.upload.return_value = "test-file-id-123"
        mock_document_data = Mock()
        mock_document_data.result = None  # No content found
        mock_client.parse.return_value = mock_document_data

        kb_service._context.extraction_service._reducto_client = mock_client

        # Mock the _setup_kb call to avoid database setup issues
        with patch("sema4ai_docint.services._knowledge_base_service._setup_kb"):
            agent_server_transport.set_file_responses({"empty_document.pdf": test_pdf_path})
            with patch("sema4ai_docint.services._knowledge_base_service.TransformDocumentLayout"):
                with patch(
                    "sema4ai_docint.services._knowledge_base_service.TransformDocumentLayout"
                ) as mock_transformer:
                    mock_transformer_instance = Mock()
                    mock_transformer_instance.get_doc_uuid.return_value = str(uuid.uuid4())
                    mock_transformer.return_value = mock_transformer_instance

                    result = kb_service.ingest("empty_document.pdf")

                    assert result == "No content found in the document empty_document.pdf"


class TestSetupKB:
    """Test the _setup_kb function with different datasource configurations."""

    def test_setup_kb_with_postgres_datasource(
        self,
        setup_db,
        postgres_datasource,
        pgvector_datasource,
        cleanup_db,
        cleanup_kb,
        openai_api_key,
        patch_constants,
    ):
        """Test _setup_kb with a postgres datasource and pgvector datasource."""

        # Mock the model configuration function using openai_api_key fixture
        mock_embedding_config = {
            "provider": "openai",
            "model_name": "text-embedding-3-large",
            "api_key": openai_api_key,
        }
        mock_reranking_config = {
            "provider": "openai",
            "model_name": "gpt-4o",
            "api_key": openai_api_key,
        }

        with patch(
            "sema4ai_docint.services._setup_kb._get_model_configs_from_agent",
            return_value=(mock_embedding_config, mock_reranking_config),
        ):
            # Call the real _setup_kb function with separate postgres and pgvector datasources
            result = _setup_kb(postgres_datasource, pgvector_datasource)

            # Verify the setup was successful
            assert f"Successfully set up knowledge base '{TEST_KNOWLEDGE_BASE_NAME}'" in result
            assert f"in project '{PROJECT_NAME}'" in result

            # Verify the knowledge base was actually created by checking it exists
            conn = get_connection()
            kb_list = conn.list_knowledge_bases()

            # Find our knowledge base in the list
            kb_found = False
            for kb in kb_list:
                if kb.name == TEST_KNOWLEDGE_BASE_NAME and kb.project == PROJECT_NAME:
                    kb_found = True
                    break

            assert kb_found, (
                f"Knowledge base '{TEST_KNOWLEDGE_BASE_NAME}' not found in "
                f"{[f'{kb.project}.{kb.name}' for kb in kb_list]}"
            )
