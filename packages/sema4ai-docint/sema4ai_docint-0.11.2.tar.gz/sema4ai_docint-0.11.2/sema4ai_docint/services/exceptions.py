"""
Custom exceptions for document intelligence services.
"""


class DocumentServiceError(Exception):
    """Base exception for document service operations."""

    pass


class LayoutServiceError(Exception):
    """Exception for document layout operations."""

    pass


class DataModelServiceError(Exception):
    """Exception for data model operations."""

    pass


class ExtractionServiceError(Exception):
    """Exception for extraction operations."""

    pass


class KnowledgeBaseServiceError(Exception):
    """Exception for knowledge base operations."""

    pass
