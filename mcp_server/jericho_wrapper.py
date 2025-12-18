"""
Jericho wrapper - abstraction layer over jericho.FrotzEnv.

Provides a clean interface for game interaction with state management.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jericho
from jericho import FrotzEnv


@dataclass
class ZObject:
    """Representation of a Z-machine object."""
    num: int
    name: str
    parent: int
    sibling: int
    child: int
    attributes: list[int]
    properties: list[Any]

    @classmethod
    def from_jericho(cls, obj: jericho.ZObject) -> "ZObject":
        """Create from jericho ZObject."""
        return cls(
            num=obj.num,
            name=obj.name,
            parent=obj.parent,
            sibling=obj.sibling,
            child=obj.child,
            attributes=list(obj.attr) if hasattr(obj, 'attr') else [],
            properties=list(obj.properties) if hasattr(obj, 'properties') else []
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "num": self.num,
            "name": self.name,
            "parent": self.parent,
            "sibling": self.sibling,
            "child": self.child,
            "attributes": self.attributes,
        }


@dataclass
class GameState:
    """Current state of a game session."""
    location: str
    score: int
    moves: int
    inventory: list[str]
    description: str
    last_action: str = ""
    last_response: str = ""
    done: bool = False
    won: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "location": self.location,
            "score": self.score,
            "moves": self.moves,
            "inventory": self.inventory,
            "description": self.description,
            "last_action": self.last_action,
            "last_response": self.last_response,
            "done": self.done,
            "won": self.won,
        }


@dataclass
class GameInfo:
    """Static information about a game."""
    name: str
    path: str
    max_score: int
    version: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "max_score": self.max_score,
            "version": self.version,
        }


@dataclass
class JerichoGame:
    """
    Wrapper around Jericho FrotzEnv providing a clean interface.
    """
    env: FrotzEnv
    game_path: Path
    game_info: GameInfo
    current_state: GameState
    history: list[tuple[str, str]] = field(default_factory=list)

    @classmethod
    def load(cls, game_path: str | Path) -> "JerichoGame":
        """Load a game from a Z-machine file."""
        path = Path(game_path)
        if not path.exists():
            raise FileNotFoundError(f"Game file not found: {path}")

        env = FrotzEnv(str(path))

        # Get initial observation
        initial_obs, info = env.reset()

        # Extract game info
        game_info = GameInfo(
            name=path.stem,
            path=str(path.absolute()),
            max_score=env.get_max_score() if hasattr(env, 'get_max_score') else 0,
            version=str(env.get_version()) if hasattr(env, 'get_version') else "unknown"
        )

        # Build initial state
        current_state = GameState(
            location=cls._get_location_name(env),
            score=env.get_score(),
            moves=env.get_moves() if hasattr(env, 'get_moves') else 0,
            inventory=cls._get_inventory_list(env),
            description=initial_obs,
            done=False,
            won=False
        )

        return cls(
            env=env,
            game_path=path,
            game_info=game_info,
            current_state=current_state,
            history=[]
        )

    @staticmethod
    def _get_location_name(env: FrotzEnv) -> str:
        """Get the name of the current location."""
        try:
            loc = env.get_player_location()
            if loc and hasattr(loc, 'name'):
                return loc.name
        except Exception:
            pass
        return "Unknown"

    @staticmethod
    def _get_inventory_list(env: FrotzEnv) -> list[str]:
        """Get list of inventory item names."""
        try:
            inv = env.get_inventory()
            return [item.name for item in inv if hasattr(item, 'name')]
        except Exception:
            return []

    def step(self, action: str) -> tuple[str, GameState]:
        """
        Execute an action and return the response and new state.

        Args:
            action: The action string to execute

        Returns:
            Tuple of (game response text, updated GameState)
        """
        # Execute action
        observation, reward, done, info = self.env.step(action)

        # Check for victory
        won = info.get('won', False) if isinstance(info, dict) else False

        # Update state
        self.current_state = GameState(
            location=self._get_location_name(self.env),
            score=self.env.get_score(),
            moves=(
                self.env.get_moves()
                if hasattr(self.env, 'get_moves')
                else self.current_state.moves + 1
            ),
            inventory=self._get_inventory_list(self.env),
            description=observation,
            last_action=action,
            last_response=observation,
            done=done,
            won=won
        )

        # Record history
        self.history.append((action, observation))

        return observation, self.current_state

    def get_valid_actions(
        self,
        use_object_tree: bool = True,
        use_parallel: bool = True
    ) -> list[str]:
        """
        Get list of valid actions in current state.

        Args:
            use_object_tree: Include surrounding object names
            use_parallel: Use parallel filtering (faster)

        Returns:
            List of valid action strings
        """
        try:
            return self.env.get_valid_actions(
                use_object_tree=use_object_tree,
                use_parallel=use_parallel
            )
        except Exception:
            # Fallback to basic actions if valid_actions fails
            return ["look", "inventory", "north", "south", "east", "west", "up", "down"]

    def get_world_objects(self) -> list[ZObject]:
        """Get all objects in the game world."""
        try:
            objects = self.env.get_world_objects()
            return [ZObject.from_jericho(obj) for obj in objects]
        except Exception:
            return []

    def get_player_location_object(self) -> ZObject | None:
        """Get the ZObject for the player's current location."""
        try:
            loc = self.env.get_player_location()
            if loc:
                return ZObject.from_jericho(loc)
        except Exception:
            pass
        return None

    def get_nearby_objects(self) -> list[ZObject]:
        """Get objects in the current location (siblings of player)."""
        objects = []
        try:
            # Get objects that are siblings or children of current location
            loc = self.env.get_player_location()
            if loc:
                world = self.env.get_world_objects()
                for obj in world:
                    if obj.parent == loc.num and obj.name:
                        objects.append(ZObject.from_jericho(obj))
        except Exception:
            pass
        return objects

    def save_state(self) -> bytes:
        """Save current game state to bytes."""
        return self.env.get_state()

    def restore_state(self, state: bytes) -> str:
        """Restore game state from bytes, returns current observation."""
        self.env.set_state(state)
        # Get current observation after restore
        obs = self.env.step("look")[0]
        self.current_state = GameState(
            location=self._get_location_name(self.env),
            score=self.env.get_score(),
            moves=self.env.get_moves() if hasattr(self.env, 'get_moves') else 0,
            inventory=self._get_inventory_list(self.env),
            description=obs,
            done=False,
            won=False
        )
        return obs

    def close(self) -> None:
        """Close the game environment."""
        try:
            self.env.close()
        except Exception:
            pass

    def get_inventory(self) -> list[str]:
        """Get list of inventory item names."""
        return self._get_inventory_list(self.env)

    def get_walkthrough(self) -> list[str] | None:
        """Get walkthrough for the game if available."""
        try:
            return self.env.get_walkthrough()
        except Exception:
            return None
