"""
Configuration for the MCP server - feature toggles and settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class MCPServerConfig(BaseSettings):
    """Configuration for the Jericho MCP server."""

    # Feature toggles - can be enabled/disabled at runtime
    enable_valid_actions: bool = Field(
        default=True,
        description="Allow LLM to query valid actions in current state"
    )
    enable_object_tree: bool = Field(
        default=False,
        description="Allow LLM to query full world object tree"
    )
    enable_walkthrough_hints: bool = Field(
        default=False,
        description="Allow LLM to query walkthrough hints (if available)"
    )
    enable_score_tracking: bool = Field(
        default=True,
        description="Track and expose game score"
    )

    # Game settings
    games_dir: str = Field(
        default="z-machine-games-master/jericho-game-suite",
        description="Directory containing Z-machine game files"
    )
    max_action_length: int = Field(
        default=100,
        description="Maximum length of player actions"
    )

    # Session settings
    max_sessions: int = Field(
        default=10,
        description="Maximum concurrent game sessions"
    )
    session_timeout_minutes: int = Field(
        default=60,
        description="Session timeout in minutes"
    )

    # Valid actions settings
    valid_actions_use_object_tree: bool = Field(
        default=True,
        description="Include surrounding objects in valid action generation"
    )
    valid_actions_use_parallel: bool = Field(
        default=True,
        description="Use parallel processing for valid action filtering"
    )

    model_config = {
        "env_prefix": "MCP_",
        "env_file": ".env",
        "extra": "ignore"
    }


# Global config instance
config = MCPServerConfig()


def update_config(**kwargs) -> MCPServerConfig:
    """Update configuration values at runtime."""
    global config
    config = MCPServerConfig(**{**config.model_dump(), **kwargs})
    return config
