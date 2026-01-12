"""
Document metadata extraction and management
"""

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from app.utils.security import get_secure_file_path, validate_id_format

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manage document metadata storage"""

    def __init__(self, metadata_dir: str = "./.metadata"):
        self.metadata_dir = metadata_dir
        os.makedirs(metadata_dir, exist_ok=True)
        # Normalize and make absolute for security checks
        self.metadata_dir = os.path.abspath(self.metadata_dir)

    def _validate_doc_id(self, doc_id: str) -> None:
        """
        Validate doc_id to prevent path traversal attacks.

        Raises ValueError if doc_id is invalid or contains path traversal characters.
        """
        validate_id_format(doc_id, "document ID")

    def _get_metadata_path(self, doc_id: str) -> str:
        """
        Get file path for metadata with path traversal protection.

        Raises ValueError if doc_id is invalid or would result in path traversal.
        """
        self._validate_doc_id(doc_id)
        return get_secure_file_path(self.metadata_dir, doc_id, ".json")

    def save_metadata(self, doc_id: str, metadata: dict[str, Any]):
        """Save document metadata to file"""
        metadata_path = self._get_metadata_path(doc_id)

        # Copy to avoid mutating caller's dict
        metadata_copy = dict(metadata)

        # Add timestamps
        if "upload_date" not in metadata_copy:
            metadata_copy["upload_date"] = datetime.now(UTC).isoformat()

        with open(metadata_path, "w") as f:
            json.dump(metadata_copy, f, indent=2, default=str)

    def load_metadata(self, doc_id: str) -> dict[str, Any]:
        """Load document metadata from file"""
        metadata_path = self._get_metadata_path(doc_id)

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata not found for document {doc_id}")

        with open(metadata_path) as f:
            return json.load(f)

    def delete_metadata(self, doc_id: str):
        """Delete document metadata"""
        metadata_path = self._get_metadata_path(doc_id)

        if os.path.exists(metadata_path):
            os.remove(metadata_path)

    def list_all_metadata(self) -> list[dict[str, Any]]:
        """List all document metadata"""
        metadata_list = []

        if not os.path.exists(self.metadata_dir):
            return metadata_list

        for filename in os.listdir(self.metadata_dir):
            if filename.endswith(".json"):
                doc_id = filename[:-5]  # Remove .json extension
                try:
                    metadata = self.load_metadata(doc_id)
                    metadata["id"] = doc_id
                    metadata_list.append(metadata)
                except Exception as e:
                    logger.warning(
                        "Failed to load metadata file, skipping",
                        extra={"doc_id": doc_id, "file_name": filename, "error": str(e)},
                    )
                    continue

        return metadata_list

    def exists(self, doc_id: str) -> bool:
        """Check if metadata exists for document"""
        metadata_path = self._get_metadata_path(doc_id)
        return os.path.exists(metadata_path)


# Global instance
metadata_manager = MetadataManager()
