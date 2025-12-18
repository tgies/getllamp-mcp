"""
Tests for MCP tools.
"""

import pytest
from unittest.mock import patch, MagicMock

from mcp_server.tools import list_available_games


class TestListAvailableGames:
    """Tests for list_available_games tool."""
    
    def test_empty_directory(self, tmp_path):
        """Test listing games from empty directory."""
        with patch('mcp_server.tools.config') as mock_config:
            mock_config.games_dir = str(tmp_path)
            result = list_available_games()
            
            assert result["games"] == []
            assert result["count"] == 0
    
    def test_with_game_files(self, tmp_path):
        """Test listing games from directory with game files."""
        # Create mock game files
        (tmp_path / "zork1.z5").touch()
        (tmp_path / "zork2.z5").touch()
        (tmp_path / "readme.txt").touch()  # Should be ignored
        
        with patch('mcp_server.tools.config') as mock_config:
            mock_config.games_dir = str(tmp_path)
            result = list_available_games()
            
            assert result["count"] == 2
            names = [g["name"] for g in result["games"]]
            assert "zork1" in names
            assert "zork2" in names
    
    def test_nonexistent_directory(self, tmp_path):
        """Test listing games from nonexistent directory."""
        with patch('mcp_server.tools.config') as mock_config:
            mock_config.games_dir = str(tmp_path / "nonexistent")
            result = list_available_games()
            
            assert result["games"] == []
            assert result["count"] == 0
