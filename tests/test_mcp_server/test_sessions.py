"""
Tests for session management.
"""

from unittest.mock import MagicMock, patch

import pytest

from mcp_server.sessions import SaveSlot, SessionManager


class TestSaveSlot:
    """Tests for SaveSlot."""

    def test_to_dict(self):
        """Test serialization of save slot."""
        from mcp_server.jericho_wrapper import GameState

        state = GameState(
            location="Test",
            score=10,
            moves=5,
            inventory=[],
            description="A test room."
        )

        slot = SaveSlot(
            name="test_save",
            created_at=1234567890.0,
            state_data=b"test_data",
            game_state=state
        )

        d = slot.to_dict()
        assert d["name"] == "test_save"
        assert d["created_at"] == 1234567890.0
        assert "game_state" in d


class TestSessionManager:
    """Tests for SessionManager."""

    def test_empty_manager(self):
        """Test empty session manager."""
        manager = SessionManager()
        assert manager.active_session_count == 0
        assert manager.list_sessions() == []

    def test_get_nonexistent_session(self):
        """Test getting a session that doesn't exist."""
        manager = SessionManager()
        assert manager.get_session("nonexistent") is None

    def test_require_nonexistent_session(self):
        """Test requiring a session that doesn't exist raises."""
        manager = SessionManager()
        with pytest.raises(KeyError):
            manager.require_session("nonexistent")

    def test_close_nonexistent_session(self):
        """Test closing a session that doesn't exist."""
        manager = SessionManager()
        assert manager.close_session("nonexistent") is False

    @patch('mcp_server.sessions.JerichoGame')
    def test_create_session(self, mock_jericho_game):
        """Test creating a session with mocked Jericho."""
        from mcp_server.jericho_wrapper import GameInfo, GameState

        # Setup mock
        mock_game = MagicMock()
        mock_game.game_info = GameInfo(
            name="test", path="/test.z5", max_score=100, version="1"
        )
        mock_game.current_state = GameState(
            location="Start", score=0, moves=0,
            inventory=[], description="Test"
        )
        mock_jericho_game.load.return_value = mock_game

        manager = SessionManager()
        session = manager.create_session("/test.z5", session_id="test-123")

        assert session.session_id == "test-123"
        assert manager.active_session_count == 1
        assert manager.get_session("test-123") is not None

    @patch('mcp_server.sessions.JerichoGame')
    @patch('mcp_server.sessions.config')
    def test_max_sessions_limit(self, mock_config, mock_jericho_game):
        """Test that max sessions limit is enforced."""
        from mcp_server.jericho_wrapper import GameInfo, GameState

        # Configure mock config
        mock_config.max_sessions = 2
        mock_config.session_timeout_minutes = 60

        # Setup mock game
        mock_game = MagicMock()
        mock_game.game_info = GameInfo(
            name="test", path="/test.z5", max_score=100, version="1"
        )
        mock_game.current_state = GameState(
            location="Start", score=0, moves=0,
            inventory=[], description="Test"
        )
        mock_game.close = MagicMock()
        mock_jericho_game.load.return_value = mock_game

        manager = SessionManager()
        manager.create_session("/test1.z5")
        manager.create_session("/test2.z5")

        with pytest.raises(RuntimeError, match="Maximum sessions"):
            manager.create_session("/test3.z5")
