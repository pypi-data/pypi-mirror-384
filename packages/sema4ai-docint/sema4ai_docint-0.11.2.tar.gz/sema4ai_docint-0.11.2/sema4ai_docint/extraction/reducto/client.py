"""
Main client implementation for doc-extraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, ClassVar

import httpx
import sema4ai_http
from reducto import AsyncReducto
from reducto.types import ExtractResponse, ParseResponse, SplitCategory, SplitResponse
from reducto.types.shared.parse_response import ResultFullResult

from sema4ai_docint.extraction.reducto.exceptions import (
    ExtractMultipleResultsError,
    ExtractNoResultsError,
)
from sema4ai_docint.logging import logger
from sema4ai_docint.models.extraction import ExtractionResult

if TYPE_CHECKING:
    from sema4ai_docint.extraction.reducto.async_ import Job


class ExtractionClient(ABC):
    """Main client for document-extraction."""

    SEMA4_REDUCTO_ENDPOINT = "https://backend.sema4.ai/reducto"
    DEFAULT_EXTRACT_SYSTEM_PROMPT = (
        "Be precise and thorough. Mark required, missing fields as null. Omit optional fields."
    )

    _extract_only_keys: ClassVar[list[str]] = [
        "schema",
        "system_prompt",
        "generate_citations",
        "array_extract",
        "use_chunking",
        "include_images",
        "spreadsheet_agent",
    ]

    @staticmethod
    def _make_mounts(
        network_config: sema4ai_http.NetworkProfile,
    ) -> dict[str, httpx.HTTPTransport | None]:
        """Make mounts for proxy configuration. Copied from sema4ai-http-helper README."""
        if not network_config.ssl_context:
            raise ValueError("SSL context missing from sema4ai-http-helper NetworkProfile")

        mounts: dict[str, httpx.HTTPTransport | None] = {}
        for http_proxy in chain(
            network_config.proxy_config.http, network_config.proxy_config.https
        ):
            mounts[http_proxy] = httpx.HTTPTransport(network_config.ssl_context)
        for no_proxy in network_config.proxy_config.no_proxy:
            mounts[no_proxy] = None

        return mounts

    @property
    def client(self) -> AsyncReducto:
        """Return the async Reducto client."""
        return self._client

    @client.setter
    def client(self, value: AsyncReducto):
        """Set the async Reducto client."""
        if not isinstance(value, AsyncReducto):
            raise ValueError("client must be a AsyncReducto instance")
        self._client = value

    @abstractmethod
    def unwrap(self) -> AsyncReducto:
        """Return the underlying async Reducto client."""
        pass

    @abstractmethod
    def upload(
        self, document: Path | bytes | BinaryIO, *, content_length: int | None = None
    ) -> str:
        """Upload a document to the client.

        Args:
            document: Either a filesystem `Path`, raw `bytes`, or a binary file-like
                object (`BinaryIO`).
            content_length: Optional explicit content length. If not provided, it will be
                inferred when possible.

        Returns:
            The file ID of the uploaded document.
        """
        pass

    @abstractmethod
    def parse(self, document_id: str, config: dict[str, Any] | None = None) -> ParseResponse:
        """Parse a document using the client.

        Args:
            document_id: The Reducto file ID of the document to parse. Can also be a job ID
                in the format `jobid://{job_id}` to reference the output of a previous job.
            config: Optional configuration to override default parse settings

        Returns:
            The parse response from Reducto.
        """
        pass

    @abstractmethod
    def parse_file(self, file: Path | str, config: dict[str, Any] | None = None) -> ParseResponse:
        """Parse a file at the provided path using the client.

        Args:
            file: The path to the file to parse.
            config: Optional configuration to override default parse settings

        Returns:
            The parse response from Reducto.
        """
        pass

    @abstractmethod
    def split(
        self,
        document_id: str,
        split_description: Iterable[SplitCategory],
        split_rules: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> SplitResponse:
        """Split a document using the client.

        Args:
            document_id: The Reducto file ID of the document to split. Can also be a job ID
                in the format `jobid://{job_id}` to reference the output of a previous job.
            split_description: The description of the split to perform.
            split_rules: Optional split rules to use.
            config: Optional configuration to override default split settings

        Returns:
            The split response from Reducto.
        """
        pass

    @abstractmethod
    def extract(
        self,
        document_url: str,
        schema: dict[str, Any],
        system_prompt: str | None = None,
        start_page: int | None = None,
        end_page: int | None = None,
        extraction_config: dict[str, Any] | None = None,
    ) -> ExtractResponse:
        """Extract data from a document using the client.

        Args:
            document_url: The Reducto file ID of the document to extract data from. Can also
                be a job ID in the format `jobid://{job_id}` to reference the output of a
                previous job.
            schema: The JSON schema for extraction
            system_prompt: Optional custom system prompt for extraction
            start_page: Optional start page for extraction
            end_page: Optional end page for extraction
            extraction_config: Optional configuration to override default extraction settings

        Returns:
            The extraction response from Reducto.
        """
        pass

    @staticmethod
    def convert_extract_response(resp: ExtractResponse) -> ExtractionResult:
        """Convert a Reducto ExtractResponse to a Sema4ai ExtractionResult.

        Note: in all our pipelines, we expect extraction chunking to be disabled, so
        we always only take the first result from Reducto ExtractResponse.
        """
        if len(resp.result) > 1:
            raise ExtractMultipleResultsError(results=resp.result)
        if not resp.result:
            raise ExtractNoResultsError(results=resp.result)
        return ExtractionResult(
            results=resp.result[0],
            citations=resp.citations[0] if resp.citations else None,
        )

    def split_opts(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Constructs the default split options for Reducto, applying any overrides to the
        default configuration.
        """
        default_config = ExtractionClient._default_parse_opts()

        # Merge with provided configuration if available
        if config:
            return ExtractionClient.merge_config(default_config, config)

        return default_config

    @classmethod
    def _default_parse_opts(cls) -> dict[str, Any]:
        """
        Default parse options for Reducto.

        These options are shared across both parse and extract. Changes to this default option must
        be made with extreme care as they will affect the accuracy of extraction.
        """

        return {
            "options": {
                "extraction_mode": "ocr",
                "ocr_mode": "standard",
                "chunking": {"chunk_mode": "disabled"},
                "table_summary": {"enabled": False},
                "figure_summary": {"enabled": False},
                "filter_blocks": ["Page Number", "Header", "Footer", "Comment"],
                "force_url_result": False,
            },
            "advanced_options": {
                "ocr_system": "highres",
                "table_output_format": "html",
                "merge_tables": False,
                "continue_hierarchy": True,
                "keep_line_breaks": False,
                "page_range": {"start": None, "end": None},
                "large_table_chunking": {"enabled": True, "size": 50},
                "spreadsheet_table_clustering": "default",
                "remove_text_formatting": False,
                "filter_line_numbers": False,
            },
            "experimental_options": {
                "enrich": {"enabled": False, "mode": "standard"},
                "native_office_conversion": False,
                "enable_checkboxes": False,
                "rotate_pages": False,
                "enable_underlines": False,
                "enable_equations": False,
                "return_figure_images": False,
                "layout_enrichment": False,
                "layout_model": "default",
            },
            "timeout": 300,
        }

    def parse_opts(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        default_config = ExtractionClient._default_parse_opts()

        # Merge with provided configuration if available
        if config:
            # Some options are only valid for extract, not parse. We filter them out here.
            filtered_config = {
                k: v for k, v in config.items() if k not in ExtractionClient._extract_only_keys
            }
            return ExtractionClient.merge_config(default_config, filtered_config)

        return default_config

    def extract_opts(
        self,
        schema: dict[str, Any],
        system_prompt: str,
        start_page: int | None = None,
        end_page: int | None = None,
        extraction_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        default_config = ExtractionClient._default_parse_opts()
        # Merge in the extraction configuration with the default parse option
        default_config = ExtractionClient.merge_config(
            default_config,
            {
                "schema": schema,
                "advanced_options": {
                    "page_range": {
                        "start": start_page,
                        "end": end_page,
                    },
                },
                "array_extract": {
                    "enabled": False,
                    # Let the mode default to legacy, don't set it to streaming
                },
                "system_prompt": system_prompt,
                "generate_citations": True,
                "timeout": 300,
            },
        )

        # Merge with provided extraction configuration if available
        if extraction_config:
            return ExtractionClient.merge_config(default_config, extraction_config)

        return default_config

    @classmethod
    def _has_top_level_array(cls, schema: dict[str, Any]) -> bool:
        """Check if the schema has a top-level property which is an array."""
        if "properties" in schema:
            for _, v in schema["properties"].items():
                if "type" in v and v["type"] == "array":
                    return True
        return False

    @classmethod
    def merge_config(
        cls, default_config: dict[str, Any], user_config: dict[str, Any] | None
    ) -> dict[str, Any]:
        """
        Merge user configuration with default configuration.

        Args:
            default_config: The default configuration from code
            user_config: The configuration from user (can be None)

        Returns:
            Merged configuration with database config overriding default config
        """
        if not user_config:
            return default_config

        def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
            """Recursively merge two dictionaries, with override taking precedence."""
            result = base.copy()
            for key, value in override.items():
                # Special handling for fields that should be completely replaced, not merged
                if key in ["schema", "system_prompt"]:
                    result[key] = value
                elif key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(default_config, user_config)

    @classmethod
    def localize_parse_response(cls, resp: ParseResponse) -> ParseResponse:
        """
        Conditionally fetch the remote results from a ResultURLResult in this ParseResponse.

        Args:
            resp: The ParseResponse to localize

        Returns:
            The parsed result as a ResultFullResult object
        """
        # Nothing to do, we have the full result
        if resp.result.type != "url":
            return resp

        try:
            response = sema4ai_http.get(resp.result.url)
            response.raise_for_status()  # Raise an exception for bad status codes
            result_dict = response.json()

            # Convert the dictionary to a ResultFullResult object
            resp.result = ResultFullResult(**result_dict)
            return resp
        except Exception as e:
            logger.error(f"Error fetching result from URL: {e!s}")
            raise e

    @abstractmethod
    def extract_with_schema(
        self,
        extraction_input: Path | str | Job,
        extraction_schema: dict[str, Any] | str,
        extraction_config: dict[str, Any] | None = None,
        prompt: str | None = None,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> ExtractionResult:
        """Extract data from a document using Reducto.

        Note: citations are enabled by default, to disable them, provide an extraction_config
        with generate_citations set to False.

        Args:
            extraction_input: The path to a local file, a Reducto job ID, a Reducto file ID,
                or a Job handle (async only).
            extraction_schema: Extraction schema to use for processing (string or
                ExtractionSchema dict).
                This defines the structure for extracting data from the document.
                Should contain JSONSchema properties like 'type', 'properties', 'required'.
            extraction_config: Optional extraction configuration for processing
            prompt: Optional system prompt for Reducto
            start_page: Optional start page for extraction
            end_page: Optional end page for extraction
        """
        pass

    @abstractmethod
    def extract_with_data_model(
        self,
        extraction_input: Path | str | Job,
        extraction_schema: dict[str, Any] | str,
        data_model_prompt: str | None = None,
        extraction_config: dict[str, Any] | None = None,
        document_layout_prompt: str | None = None,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> ExtractionResult:
        """Extract data from a document using Reducto.

        Note: citations are enabled by default, to disable them, provide an extraction_config
        with generate_citations set to False.

        Args:
            extraction_input: The path to a local file, a Reducto job ID, a Reducto file ID,
                or a Job handle (async only).
            extraction_schema: Extraction schema to use for processing (string or
                ExtractionSchema dict).
                This defines the structure for extracting data from the document.
                Should contain JSONSchema properties like 'type', 'properties', 'required'.
            data_model_prompt: Optional system prompt for processing
            extraction_config: Optional extraction configuration for processing
            document_layout_prompt: Optional system prompt for layout processing
            start_page: Optional start page for extraction (1-indexed)
            end_page: Optional end page for extraction (1-indexed)
        """
        pass

    @abstractmethod
    def extract_details(
        self,
        file_path: Path,
        extraction_schema: str | dict[str, Any],
        data_model_prompt: str | None = None,
        extraction_config: dict[str, Any] | None = None,
        document_layout_prompt: str | None = None,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> ExtractionResult:
        """Extract data from a document using Reducto, returning an ExtractionResult.

        Note: This method is deprecated in favor of extract_with_data_model.

        Args:
            file_path: The path to the document file to extract from.
            extraction_schema: JSONSchema as a string or dictionary to direct extraction.
            data_model_prompt: Optional system prompt for the data model.
            extraction_config: Optional Reducto extraction configuration for processing.
            document_layout_prompt: Optional system prompt for document layout.
            start_page: Optional start page for extraction (1-indexed).
            end_page: Optional end page for extraction (1-indexed).
        """
        pass
