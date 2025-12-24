"""
MCP Server entry point.

This is the main entry point for the Jericho MCP server.
Can be run standalone for use with Claude Desktop, Gemini CLI, etc.
"""

from typing import Any

from fastmcp import FastMCP

from mcp_server.config import update_config
from mcp_server.tools import (
    check_inventory,
    close_session,
    export_save,
    get_game_state,
    get_nearby_objects,
    get_valid_actions,
    get_world_tree,
    import_save,
    list_available_games,
    list_saves,
    list_sessions,
    look,
    play_action,
    restore_game,
    save_game,
    start_game,
)


def create_server(
    enable_valid_actions: bool | None = None,
    enable_object_tree: bool | None = None,
    enable_walkthrough_hints: bool | None = None,
    **kwargs: Any
) -> FastMCP:
    """
    Create and configure the MCP server.

    Args:
        enable_valid_actions: Override valid_actions feature toggle
        enable_object_tree: Override object_tree feature toggle
        enable_walkthrough_hints: Override walkthrough_hints feature toggle
        **kwargs: Additional config overrides

    Returns:
        Configured FastMCP server instance
    """
    # Apply config overrides
    overrides = {k: v for k, v in {
        "enable_valid_actions": enable_valid_actions,
        "enable_object_tree": enable_object_tree,
        "enable_walkthrough_hints": enable_walkthrough_hints,
        **kwargs
    }.items() if v is not None}

    if overrides:
        update_config(**overrides)

    # Create the MCP server
    mcp = FastMCP(
        name="getllamp",
        instructions="""
You are playing an interactive fiction (text adventure) game through the getllamp MCP server.

GETTING STARTED:
1. Use list_available_games() to see what games you can play
2. Use start_game(game_path) to begin a new game session
3. Use play_action(session_id, action) to interact with the game

GAMEPLAY TIPS:
- Use simple commands like 'go north', 'take lamp', 'examine door'
- Use 'look' to see your surroundings, 'inventory' to see your items
- Save frequently with save_game() - some actions can be fatal!
- If stuck, examine everything and try different command phrasings

AVAILABLE FEATURES:
- Valid actions: Shows what commands the game accepts (may be disabled)
- Object tree: Shows objects in the game world (may be disabled)
- Multiple sessions: You can have multiple games running

Be creative, explore thoroughly, and enjoy the adventure!
"""
    )

    # Register all tools
    mcp.tool()(list_available_games)
    mcp.tool()(start_game)
    mcp.tool()(play_action)
    mcp.tool()(get_game_state)
    mcp.tool()(look)
    mcp.tool()(check_inventory)
    mcp.tool()(get_valid_actions)
    mcp.tool()(get_nearby_objects)
    mcp.tool()(get_world_tree)
    mcp.tool()(save_game)
    mcp.tool()(restore_game)
    mcp.tool()(list_saves)
    mcp.tool()(export_save)
    mcp.tool()(import_save)
    mcp.tool()(close_session)
    mcp.tool()(list_sessions)

    # Note: Resources not registered - FastMCP requires URI templates with parameters
    # All necessary info is available via tools (get_game_state, list_sessions, etc.)

    return mcp


# Create default server instance
_server: FastMCP | None = None


def get_server() -> FastMCP:
    """Get or create the default server instance."""
    global _server
    if _server is None:
        _server = create_server()
    return _server


def main():
    """Run the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="getllamp Jericho MCP Server")
    parser.add_argument(
        "--enable-valid-actions",
        action="store_true",
        default=None,
        help="Enable valid_actions feature"
    )
    parser.add_argument(
        "--disable-valid-actions",
        action="store_true",
        help="Disable valid_actions feature"
    )
    parser.add_argument(
        "--enable-object-tree",
        action="store_true",
        default=None,
        help="Enable object_tree feature"
    )
    parser.add_argument(
        "--disable-object-tree",
        action="store_true",
        help="Disable object_tree feature"
    )
    parser.add_argument(
        "--games-dir",
        type=str,
        default=None,
        help="Directory containing Z-machine game files"
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport method (default: stdio)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to for SSE transport (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on for SSE transport (default: 8000)"
    )

    args = parser.parse_args()

    # Build config overrides
    enable_valid_actions = None
    if args.enable_valid_actions:
        enable_valid_actions = True
    elif args.disable_valid_actions:
        enable_valid_actions = False

    enable_object_tree = None
    if args.enable_object_tree:
        enable_object_tree = True
    elif args.disable_object_tree:
        enable_object_tree = False

    config_kwargs = {}
    if args.games_dir:
        config_kwargs["games_dir"] = args.games_dir

    # Create and run server
    server = create_server(
        enable_valid_actions=enable_valid_actions,
        enable_object_tree=enable_object_tree,
        **config_kwargs
    )

    # Run with selected transport
    if args.transport == "stdio":
        # IMPORTANT: show_banner=False prevents the FastMCP ASCII banner from being
        # printed to stdout, which would corrupt the JSON-RPC protocol over stdio
        server.run(transport="stdio", show_banner=False)
    else:
        print(f"Starting SSE server on http://{args.host}:{args.port}")
        server.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()

