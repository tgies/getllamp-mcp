"""
MCP Resources for game information and configuration.

Resources provide read-only data that LLMs can query.
"""

from pathlib import Path

from mcp_server.config import config


def _get_session_manager():
    """Lazy import to avoid slow Jericho import at startup."""
    from mcp_server.sessions import session_manager
    return session_manager


def get_feature_config() -> dict:
    """
    Get current feature configuration.
    
    Returns which optional features are enabled or disabled.
    Use this to understand what tools are available.
    """
    return {
        "valid_actions_enabled": config.enable_valid_actions,
        "object_tree_enabled": config.enable_object_tree,
        "walkthrough_hints_enabled": config.enable_walkthrough_hints,
        "score_tracking_enabled": config.enable_score_tracking,
        "valid_actions_settings": {
            "use_object_tree": config.valid_actions_use_object_tree,
            "use_parallel": config.valid_actions_use_parallel
        }
    }


def get_server_info() -> dict:
    """
    Get information about the MCP server.
    """
    return {
        "name": "getllamp",
        "version": "0.1.0",
        "description": "Jericho Z-Machine MCP Server for Interactive Fiction",
        "games_directory": str(Path(config.games_dir).absolute()),
        "max_sessions": config.max_sessions,
        "session_timeout_minutes": config.session_timeout_minutes,
        "active_sessions": _get_session_manager().active_session_count
    }


def get_interactive_fiction_tips() -> dict:
    """
    Get tips for playing interactive fiction games.
    
    Useful context for LLMs unfamiliar with the genre.
    """
    return {
        "tips": [
            "Use simple commands like 'go north', 'take lamp', 'examine door'",
            "Common directions: north, south, east, west, up, down, in, out",
            "Use 'look' to see your surroundings again",
            "Use 'inventory' or 'i' to see what you're carrying",
            "Use 'examine [object]' or 'x [object]' to look at things closely",
            "Save frequently! Some actions can be fatal or irreversible",
            "If stuck, try 'examine' on everything visible",
            "Prepositions matter: 'put lamp in box' vs 'put lamp on table'",
            "Some games have darkness - you may need a light source",
            "Read descriptions carefully for hints about what to do"
        ],
        "common_commands": [
            "look / l - describe current location",
            "inventory / i - list carried items",
            "examine / x [thing] - look at something closely",
            "take / get [thing] - pick something up",
            "drop [thing] - put something down",
            "open / close [thing] - manipulate containers/doors",
            "go [direction] - move to another location",
            "save - save your game",
            "restore - load a saved game",
            "score - see your current score",
            "verbose - get full room descriptions"
        ],
        "genre_conventions": [
            "Most games have a goal like finding treasure or solving a mystery",
            "Death is often possible but can be restored from saves",
            "Some objects are red herrings and not needed for the solution",
            "Games often require combining objects or using them in specific places",
            "NPCs (non-player characters) may have useful information",
            "Some puzzles are time-based or require specific sequences"
        ]
    }


# All resources for registration
ALL_RESOURCES = {
    "config://features": ("Feature Configuration", get_feature_config),
    "info://server": ("Server Information", get_server_info),
    "tips://interactive-fiction": ("Interactive Fiction Tips", get_interactive_fiction_tips),
}
