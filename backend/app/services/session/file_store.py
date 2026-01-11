"""
File-based session storage
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.models.schemas import Message, SessionInfo

logger = logging.getLogger(__name__)


class SessionStore:
    """File-based session storage"""

    def __init__(self, session_dir: str | None = None):
        self.session_dir = session_dir or settings.SESSION_DIR
        os.makedirs(self.session_dir, exist_ok=True)
        # Normalize and make absolute for security checks
        self.session_dir = os.path.abspath(self.session_dir)

    def _validate_session_id(self, session_id: str) -> None:
        """
        Validate session_id to prevent path traversal attacks.

        Raises ValueError if session_id is invalid or contains path traversal characters.
        """
        if not session_id:
            raise ValueError("Session ID cannot be empty")

        # Check for path traversal characters
        if "/" in session_id or "\\" in session_id or ".." in session_id:
            raise ValueError(f"Invalid session ID: {session_id} contains path traversal characters")

        # Validate UUID format (sessions are created with UUIDs)
        try:
            uuid.UUID(session_id)
        except ValueError as e:
            raise ValueError(f"Invalid session ID format: {session_id} is not a valid UUID") from e

    def _get_session_path(self, session_id: str) -> str:
        """
        Get file path for session with path traversal protection.

        Raises ValueError if session_id is invalid or would result in path traversal.
        """
        # Validate session_id format
        self._validate_session_id(session_id)

        # Construct path
        session_path = os.path.join(self.session_dir, f"{session_id}.json")

        # Normalize path to resolve any remaining issues
        session_path = os.path.normpath(session_path)
        session_path = os.path.abspath(session_path)

        # Ensure the resolved path is within the session directory
        # This prevents path traversal even if validation somehow fails
        if not os.path.commonpath([self.session_dir, session_path]) == self.session_dir:
            raise ValueError(f"Path traversal detected: {session_id}")

        return session_path

    def create_session(
        self, model_id: str, document_ids: list[str], name: str | None = None
    ) -> SessionInfo:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        session_data = {
            "id": session_id,
            "name": name,
            "model_id": model_id,
            "document_ids": document_ids,
            "messages": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        self._save_session(session_id, session_data)
        return self._dict_to_session_info(session_data)

    def get_session(self, session_id: str) -> SessionInfo:
        """Get session by ID"""
        session_path = self._get_session_path(session_id)

        if not os.path.exists(session_path):
            raise FileNotFoundError(f"Session {session_id} not found")

        with open(session_path) as f:
            session_data = json.load(f)

        return self._dict_to_session_info(session_data)

    def update_session(
        self,
        session_id: str,
        messages: list[Message] | None = None,
        model_id: str | None = None,
        document_ids: list[str] | None = None,
        name: str | None = None,
    ):
        """Update session data"""
        session_data = self._load_session(session_id)

        if messages is not None:
            session_data["messages"] = [
                msg.model_dump() if isinstance(msg, Message) else msg for msg in messages
            ]

        if model_id is not None:
            session_data["model_id"] = model_id

        if document_ids is not None:
            session_data["document_ids"] = document_ids

        if name is not None:
            session_data["name"] = name

        session_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        self._save_session(session_id, session_data)

    def delete_session(self, session_id: str):
        """Delete a session"""
        session_path = self._get_session_path(session_id)

        if os.path.exists(session_path):
            os.remove(session_path)

    def list_sessions(self) -> list[SessionInfo]:
        """List all sessions"""
        sessions = []

        if not os.path.exists(self.session_dir):
            return sessions

        for filename in os.listdir(self.session_dir):
            if filename.endswith(".json"):
                session_id = filename[:-5]
                try:
                    session = self.get_session(session_id)
                    sessions.append(session)
                except Exception as e:
                    logger.warning(
                        "Failed to load session file, skipping",
                        extra={"session_id": session_id, "file_name": filename, "error": str(e)},
                    )
                    continue

        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        return sessions

    def add_message(self, session_id: str, message: Message):
        """Add a message to session"""
        session_data = self._load_session(session_id)

        message_dict = message.model_dump() if isinstance(message, Message) else message
        session_data["messages"].append(message_dict)
        session_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        self._save_session(session_id, session_data)

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        return os.path.exists(self._get_session_path(session_id))

    def _save_session(self, session_id: str, session_data: dict[str, Any]):
        """Save session data to file"""
        session_path = self._get_session_path(session_id)

        with open(session_path, "w") as f:
            json.dump(session_data, f, indent=2, default=str)

    def _load_session(self, session_id: str) -> dict[str, Any]:
        """Load session data from file"""
        session_path = self._get_session_path(session_id)

        if not os.path.exists(session_path):
            raise FileNotFoundError(f"Session {session_id} not found")

        with open(session_path) as f:
            return json.load(f)

    def _dict_to_session_info(self, session_data: dict[str, Any]) -> SessionInfo:
        """Convert dict to SessionInfo model"""
        # Parse messages
        messages = [
            Message(**msg) if isinstance(msg, dict) else msg
            for msg in session_data.get("messages", [])
        ]

        # Parse dates - ensure timezone-aware
        created_at = session_data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
            # Make timezone-aware if naive (assume UTC for legacy data)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

        updated_at = session_data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
            # Make timezone-aware if naive (assume UTC for legacy data)
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)

        return SessionInfo(
            id=session_data["id"],
            name=session_data.get("name"),
            model_id=session_data["model_id"],
            document_ids=session_data.get("document_ids", []),
            messages=messages,
            created_at=created_at,
            updated_at=updated_at,
        )


# Global instance
session_store = SessionStore()
