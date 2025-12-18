"""
Tests for MCP server configuration.
"""

from mcp_server.config import MCPServerConfig, config, update_config


class TestMCPServerConfig:
    """Tests for MCPServerConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        cfg = MCPServerConfig()

        assert cfg.enable_valid_actions is True
        assert cfg.enable_object_tree is False
        assert cfg.enable_walkthrough_hints is False
        assert cfg.max_sessions == 10
        assert cfg.session_timeout_minutes == 60

    def test_custom_values(self):
        """Test creating config with custom values."""
        cfg = MCPServerConfig(
            enable_valid_actions=False,
            enable_object_tree=True,
            max_sessions=5
        )

        assert cfg.enable_valid_actions is False
        assert cfg.enable_object_tree is True
        assert cfg.max_sessions == 5

    def test_update_config(self):
        """Test updating global config."""
        original = config.enable_valid_actions

        updated = update_config(enable_valid_actions=not original)
        assert updated.enable_valid_actions == (not original)

        # Reset
        update_config(enable_valid_actions=original)
