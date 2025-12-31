"""
Document metadata extraction and management
"""

import json
import os
from datetime import datetime
from typing import Any


class MetadataManager:
    """Manage document metadata storage"""

    def __init__(self, metadata_dir: str = "./.metadata"):
        self.metadata_dir = metadata_dir
        os.makedirs(metadata_dir, exist_ok=True)

    def save_metadata(self, doc_id: str, metadata: dict[str, Any]):
        """Save document metadata to file"""
        metadata_path = os.path.join(self.metadata_dir, f"{doc_id}.json")

        # Add timestamps
        if "upload_date" not in metadata:
            metadata["upload_date"] = datetime.utcnow().isoformat()

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

    def load_metadata(self, doc_id: str) -> dict[str, Any]:
        """Load document metadata from file"""
        metadata_path = os.path.join(self.metadata_dir, f"{doc_id}.json")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata not found for document {doc_id}")

        with open(metadata_path) as f:
            return json.load(f)

    def delete_metadata(self, doc_id: str):
        """Delete document metadata"""
        metadata_path = os.path.join(self.metadata_dir, f"{doc_id}.json")

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
                except Exception:
                    continue

        return metadata_list

    def exists(self, doc_id: str) -> bool:
        """Check if metadata exists for document"""
        metadata_path = os.path.join(self.metadata_dir, f"{doc_id}.json")
        return os.path.exists(metadata_path)


# Global instance
metadata_manager = MetadataManager()
