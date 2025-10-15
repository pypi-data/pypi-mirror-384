"""
DIService facade that namespaces document and layout operations.
"""

from sema4ai.data import DataSource

from sema4ai_docint.agent_server_client.transport import TransportBase
from sema4ai_docint.extraction.reducto import AsyncExtractionClient, SyncExtractionClient

from ._context import _DIContext
from ._data_model import _DataModelService
from ._document import _DocumentService
from ._knowledge_base_service import _KnowledgeBaseService
from ._layout import _LayoutService


def build_extraction_service(
    sema4_api_key: str,
    disable_ssl_verification: bool = False,
) -> SyncExtractionClient:
    """Factory function to build just the ExtractionService

    Deprecated:
        Use build_extraction_service_async instead.

    Args:
        sema4_api_key: The sema4 api key to use for the extraction service
        disable_ssl_verification: Whether to disable ssl verification for the extraction service

    Returns:
        The ExtractionService instance
    """
    return SyncExtractionClient(
        api_key=sema4_api_key,
        disable_ssl_verification=disable_ssl_verification,
    )


def build_extraction_service_async(
    sema4_api_key: str,
    disable_ssl_verification: bool = False,
) -> AsyncExtractionClient:
    """Factory function to build just the ExtractionService

    Args:
        sema4_api_key: The sema4 api key to use for the extraction service
        disable_ssl_verification: Whether to disable ssl verification for the extraction service

    Returns:
        The ExtractionService instance
    """
    return AsyncExtractionClient(
        api_key=sema4_api_key,
        disable_ssl_verification=disable_ssl_verification,
    )


def build_di_service(
    datasource: DataSource,
    sema4_api_key: str | None = None,
    disable_ssl_verification: bool = False,
    *,
    agent_server_transport: TransportBase | None = None,
    pg_vector: DataSource | None = None,
) -> "DIService":
    """Factory function to build the DIService

    Args:
        datasource: The datasource to use
        sema4_api_key: The sema4 api key to use for the extraction service
        disable_ssl_verification: Whether to disable ssl verification for the extraction service
        agent_server_transport: The transport to use for the agent server client, will default to a
            HTTP transport if not provided.
        pg_vector: PGVector datasource (only required for using the knowledge base service)

    Returns:
        The DIService instance
    """
    context = _DIContext.create(
        datasource=datasource,
        sema4_api_key=sema4_api_key,
        disable_ssl_verification=disable_ssl_verification,
        agent_server_transport=agent_server_transport,
        pg_vector=pg_vector,
    )

    return DIService(
        document_service=_DocumentService(context),
        layout_service=_LayoutService(context),
        data_model_service=_DataModelService(context),
        knowledge_base_service=_KnowledgeBaseService(context) if pg_vector else None,
        context=context,
    )


class DIService:
    """Single entrypoint facade with namespaced services.

    This service creates a shared context containing all external clients
    and passes it to individual domain services for clean access to dependencies.
    """

    def __init__(
        self,
        document_service: _DocumentService,
        layout_service: _LayoutService,
        data_model_service: _DataModelService,
        knowledge_base_service: _KnowledgeBaseService | None,
        context: _DIContext,
    ) -> None:
        """Initialize DIService with optional external client capabilities."""
        self._document = document_service
        self._layout = layout_service
        self._data_model = data_model_service
        self._knowledge_base = knowledge_base_service
        self._context = context

    @property
    def document(self) -> _DocumentService:
        return self._document

    @property
    def layout(self) -> _LayoutService:
        return self._layout

    @property
    def data_model(self) -> _DataModelService:
        return self._data_model

    @property
    def knowledge_base(self) -> _KnowledgeBaseService | None:
        return self._knowledge_base

    @property
    def extraction(self) -> SyncExtractionClient | None:
        """Access to the extraction service for multi-client document extraction if
        sema4_api_key is provided."""
        return self._context.extraction_service

    @property
    def extraction_async(self) -> AsyncExtractionClient | None:
        """Access to the extraction service for multi-client document extraction if
        sema4_api_key is provided."""
        return self._context.extraction_service_async
