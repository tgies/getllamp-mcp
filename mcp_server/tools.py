"""
MCP Tool definitions for the Jericho game interface.

These are the tools exposed to LLMs via the MCP protocol.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from mcp_server.config import config

# Lazy import to speed up MCP server startup
# Jericho takes several seconds to import
if TYPE_CHECKING:
    pass

_session_manager = None

def get_session_manager():
    """Get session manager, importing lazily."""
    global _session_manager
    if _session_manager is None:
        from mcp_server.sessions import session_manager as sm
        _session_manager = sm
    return _session_manager


# Type aliases for better tool documentation
SessionId = Annotated[str, Field(description="The game session ID")]
SlotName = Annotated[str, Field(description="Name for the save slot")]


def list_available_games() -> dict:
    """
    List all available Z-machine games.

    Returns a list of games that can be started, with their file paths.
    """
    games_dir = Path(config.games_dir)
    games = []

    if games_dir.exists():
        for ext in ["*.z3", "*.z4", "*.z5", "*.z8", "*.zblorb"]:
            for game_file in games_dir.glob(ext):
                games.append({
                    "name": game_file.stem,
                    "path": str(game_file.absolute()),
                    "format": game_file.suffix
                })

    return {
        "games": sorted(games, key=lambda g: g["name"]),
        "games_dir": str(games_dir.absolute()),
        "count": len(games)
    }


def start_game(
    game_path: Annotated[str, Field(description="Path to Z-machine game file (.z5, .z8, etc.)")],
    session_id: Annotated[str | None, Field(description="Optional custom session ID")] = None
) -> dict:
    """
    Start a new game session.

    Loads the specified Z-machine game file and returns the initial game text
    along with a session ID for future interactions.
    """
    session = get_session_manager().create_session(game_path, session_id)
    game = session.game

    return {
        "session_id": session.session_id,
        "game": game.game_info.to_dict(),
        "initial_text": game.current_state.description,
        "state": game.current_state.to_dict()
    }


def play_action(
    session_id: SessionId,
    action: Annotated[str, Field(description="The action to take (e.g., 'go north', 'take lamp')")]
) -> dict:
    """
    Execute an action in the game.

    Sends a command to the game parser and returns the response.
    Common actions include: go [direction], take [object], examine [object],
    open [object], use [object], inventory, look, etc.
    
    Returns minimal info for token efficiency. Use get_game_state for full details.
    """
    session = get_session_manager().require_session(session_id)

    # Truncate action if too long
    if len(action) > config.max_action_length:
        action = action[:config.max_action_length]

    response, state = session.game.step(action)

    # Return minimal format to save LLM tokens
    # Use get_game_state for full details like inventory/location
    result = {
        "response": response,
        "score": state.score,
        "moves": state.moves,
        "done": state.done,
        "won": state.won
    }

    return result


def get_game_state(session_id: SessionId) -> dict:
    """
    Get the current game state.

    Returns the current score, location, inventory, and other state information.
    """
    session = get_session_manager().require_session(session_id)
    return {
        "state": session.game.current_state.to_dict(),
        "game": session.game.game_info.to_dict(),
        "history_length": len(session.game.history)
    }


def look(session_id: SessionId) -> dict:
    """
    Look around the current location.

    Equivalent to typing 'look' in the game - returns a description of
    the current location and visible objects.
    """
    return play_action(session_id, "look")


def check_inventory(session_id: SessionId) -> dict:
    """
    Check your inventory.

    Returns a list of items the player is currently carrying.
    """
    return play_action(session_id, "inventory")


def get_valid_actions(session_id: SessionId) -> dict:
    """
    Get a list of valid actions in the current game state.

    NOTE: This feature can be disabled by configuration. When enabled,
    returns actions that the game parser will accept and that will have
    an effect in the current state.
    """
    if not config.enable_valid_actions:
        return {
            "error": "valid_actions feature is disabled",
            "enabled": False
        }

    session = get_session_manager().require_session(session_id)
    actions = session.game.get_valid_actions(
        use_object_tree=config.valid_actions_use_object_tree,
        use_parallel=config.valid_actions_use_parallel
    )

    return {
        "valid_actions": actions,
        "count": len(actions),
        "enabled": True
    }


def get_nearby_objects(session_id: SessionId) -> dict:
    """
    Get objects visible in the current location.

    NOTE: This feature can be disabled by configuration. Returns objects
    that are present in the current room that the player might interact with.
    """
    if not config.enable_object_tree:
        return {
            "error": "object_tree feature is disabled",
            "enabled": False
        }

    session = get_session_manager().require_session(session_id)
    objects = session.game.get_nearby_objects()

    return {
        "objects": [obj.to_dict() for obj in objects],
        "count": len(objects),
        "enabled": True
    }


def get_world_tree(session_id: SessionId) -> dict:
    """
    Get the full object tree of the game world.

    NOTE: This is a powerful feature that reveals internal game structure.
    It is disabled by default and should only be enabled for debugging
    or research purposes.
    """
    if not config.enable_object_tree:
        return {
            "error": "object_tree feature is disabled",
            "enabled": False
        }

    session = get_session_manager().require_session(session_id)
    objects = session.game.get_world_objects()

    return {
        "objects": [obj.to_dict() for obj in objects],
        "count": len(objects),
        "enabled": True
    }


def save_game(
    session_id: SessionId,
    slot_name: SlotName
) -> dict:
    """
    Save the current game state to a named slot.

    The save can be restored later using restore_game with the same slot name.
    """
    session = get_session_manager().require_session(session_id)
    slot = session.save_to_slot(slot_name)

    return {
        "saved": True,
        "slot": slot.to_dict(),
        "message": f"Game saved to slot '{slot_name}'"
    }


def restore_game(
    session_id: SessionId,
    slot_name: SlotName
) -> dict:
    """
    Restore a previously saved game state.

    Restores the game to the state it was in when saved to the specified slot.
    """
    session = get_session_manager().require_session(session_id)

    try:
        observation = session.restore_from_slot(slot_name)
        return {
            "restored": True,
            "slot_name": slot_name,
            "observation": observation,
            "state": session.game.current_state.to_dict()
        }
    except KeyError:
        return {
            "restored": False,
            "error": f"Save slot '{slot_name}' not found",
            "available_slots": list(session.save_slots.keys())
        }


def list_saves(session_id: SessionId) -> dict:
    """
    List all save slots for a session.
    """
    session = get_session_manager().require_session(session_id)
    return {
        "saves": session.list_saves(),
        "count": len(session.save_slots)
    }


def export_save(
    session_id: SessionId,
    slot_name: SlotName
) -> dict:
    """
    Export a save slot as a portable string.

    Returns a base64-encoded string that can be imported later,
    even in a different session.
    """
    session = get_session_manager().require_session(session_id)
    try:
        data = session.export_save(slot_name)
        return {
            "exported": True,
            "slot_name": slot_name,
            "data": data
        }
    except KeyError:
        return {
            "exported": False,
            "error": f"Save slot '{slot_name}' not found"
        }


def import_save(
    session_id: SessionId,
    slot_name: SlotName,
    data: Annotated[str, Field(description="Base64-encoded save data from export_save")]
) -> dict:
    """
    Import a previously exported save.

    Creates a new save slot from exported data.
    """
    session = get_session_manager().require_session(session_id)
    try:
        slot = session.import_save(slot_name, data)
        return {
            "imported": True,
            "slot": slot.to_dict()
        }
    except ValueError as e:
        return {
            "imported": False,
            "error": str(e)
        }


def close_session(session_id: SessionId) -> dict:
    """
    Close a game session and release resources.

    The session ID will no longer be valid after this.
    """
    closed = get_session_manager().close_session(session_id)
    return {
        "closed": closed,
        "message": "Session closed" if closed else "Session not found"
    }


def list_sessions() -> dict:
    """
    List all active game sessions.
    """
    return {
        "sessions": get_session_manager().list_sessions(),
        "count": get_session_manager().active_session_count
    }


# Export all tools for registration
ALL_TOOLS = [
    list_available_games,
    start_game,
    play_action,
    get_game_state,
    look,
    check_inventory,
    get_valid_actions,
    get_nearby_objects,
    get_world_tree,
    save_game,
    restore_game,
    list_saves,
    export_save,
    import_save,
    close_session,
    list_sessions,
]
