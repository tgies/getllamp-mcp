"""
Session management for game instances.

Handles multiple concurrent game sessions with save/restore functionality.
"""

import base64
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from mcp_server.config import config
from mcp_server.jericho_wrapper import GameState, JerichoGame


@dataclass
class SaveSlot:
    """A saved game state."""
    name: str
    created_at: float
    state_data: bytes
    game_state: GameState

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "game_state": self.game_state.to_dict()
        }


@dataclass
class GameSession:
    """A game session with save slots."""
    session_id: str
    game: JerichoGame
    created_at: float
    last_activity: float
    save_slots: dict[str, SaveSlot] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, game_path: str | Path, session_id: str | None = None) -> "GameSession":
        """Create a new game session."""
        game = JerichoGame.load(game_path)
        now = time.time()
        return cls(
            session_id=session_id or str(uuid4()),
            game=game,
            created_at=now,
            last_activity=now
        )

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def save_to_slot(self, slot_name: str) -> SaveSlot:
        """Save current state to a named slot."""
        slot = SaveSlot(
            name=slot_name,
            created_at=time.time(),
            state_data=self.game.save_state(),
            game_state=self.game.current_state
        )
        self.save_slots[slot_name] = slot
        self.touch()
        return slot

    def restore_from_slot(self, slot_name: str) -> str:
        """Restore state from a named slot. Returns observation."""
        if slot_name not in self.save_slots:
            raise KeyError(f"Save slot not found: {slot_name}")
        slot = self.save_slots[slot_name]
        obs = self.game.restore_state(slot.state_data)
        self.touch()
        return obs

    def list_saves(self) -> list[dict]:
        """List all save slots."""
        return [slot.to_dict() for slot in self.save_slots.values()]

    def export_save(self, slot_name: str) -> str:
        """Export a save slot as base64 string."""
        if slot_name not in self.save_slots:
            raise KeyError(f"Save slot not found: {slot_name}")
        return base64.b64encode(self.save_slots[slot_name].state_data).decode('ascii')

    def import_save(self, slot_name: str, data: str) -> SaveSlot:
        """Import a save slot from base64 string."""
        state_data = base64.b64decode(data)
        # Temporarily restore to validate and get state info
        old_state = self.game.save_state()
        try:
            self.game.restore_state(state_data)
            slot = SaveSlot(
                name=slot_name,
                created_at=time.time(),
                state_data=state_data,
                game_state=self.game.current_state
            )
            self.save_slots[slot_name] = slot
            # Restore to previous state
            self.game.restore_state(old_state)
            return slot
        except Exception as e:
            self.game.restore_state(old_state)
            raise ValueError(f"Invalid save data: {e}")

    def close(self) -> None:
        """Close the session and release resources."""
        self.game.close()


class SessionManager:
    """
    Manages multiple game sessions.

    Handles session creation, lookup, cleanup, and persistence.
    """

    def __init__(self):
        self._sessions: dict[str, GameSession] = {}

    @property
    def active_session_count(self) -> int:
        return len(self._sessions)

    def create_session(
        self,
        game_path: str | Path,
        session_id: str | None = None
    ) -> GameSession:
        """
        Create a new game session.

        Args:
            game_path: Path to Z-machine game file
            session_id: Optional custom session ID

        Returns:
            New GameSession

        Raises:
            RuntimeError: If max sessions exceeded
        """
        if len(self._sessions) >= config.max_sessions:
            # Try to clean up expired sessions first
            self._cleanup_expired()
            if len(self._sessions) >= config.max_sessions:
                raise RuntimeError(f"Maximum sessions ({config.max_sessions}) exceeded")

        session = GameSession.create(game_path, session_id)
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> GameSession | None:
        """Get a session by ID, or None if not found."""
        session = self._sessions.get(session_id)
        if session:
            session.touch()
        return session

    def require_session(self, session_id: str) -> GameSession:
        """Get a session by ID, raising if not found."""
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session not found: {session_id}")
        return session

    def close_session(self, session_id: str) -> bool:
        """Close and remove a session. Returns True if found."""
        session = self._sessions.pop(session_id, None)
        if session:
            session.close()
            return True
        return False

    def list_sessions(self) -> list[dict]:
        """List all active sessions."""
        return [
            {
                "session_id": s.session_id,
                "game": s.game.game_info.name,
                "score": s.game.current_state.score,
                "moves": s.game.current_state.moves,
                "created_at": s.created_at,
                "last_activity": s.last_activity
            }
            for s in self._sessions.values()
        ]

    def _cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count removed."""
        now = time.time()
        timeout = config.session_timeout_minutes * 60
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.last_activity > timeout
        ]
        for sid in expired:
            self.close_session(sid)
        return len(expired)

    def close_all(self) -> None:
        """Close all sessions."""
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()


# Global session manager instance
session_manager = SessionManager()
