"""
Document processing services
"""

from .metadata import MetadataManager, metadata_manager
from .processor import DocumentProcessor

__all__ = [
    "DocumentProcessor",
    "MetadataManager",
    "metadata_manager",
]
