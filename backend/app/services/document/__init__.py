"""
Document processing services
"""
from .processor import DocumentProcessor
from .metadata import MetadataManager, metadata_manager

__all__ = [
    "DocumentProcessor",
    "MetadataManager",
    "metadata_manager",
]
