"""
Pytest configuration and shared fixtures.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_game_path(tmp_path: Path) -> Path:
    """
    Create a mock game path.

    Note: For real Jericho tests, you'd need an actual Z-machine file.
    This fixture is for testing code paths that don't require a real game.
    """
    game_file = tmp_path / "test_game.z5"
    # Create empty file (won't actually work with Jericho, but useful for path tests)
    game_file.touch()
    return game_file


@pytest.fixture
def mock_jericho_env():
    """Mock Jericho FrotzEnv for testing without real games."""
    env = MagicMock()
    env.reset.return_value = ("You are in a test room.", {})
    env.step.return_value = ("You go north.", 0, False, {"won": False})
    env.get_score.return_value = 10
    env.get_moves.return_value = 5
    env.get_max_score.return_value = 100
    env.get_valid_actions.return_value = ["go north", "go south", "take lamp"]
    env.get_player_location.return_value = MagicMock(name="Test Room", num=1)
    env.get_inventory.return_value = []
    env.get_world_objects.return_value = []
    env.save_state.return_value = b"mock_state_data"
    env.restore_state.return_value = None
    env.close.return_value = None
    return env


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing."""
    from harness.llm import CostTracker, LLMProvider, LLMResponse

    provider = MagicMock(spec=LLMProvider)
    provider.cost_tracker = CostTracker()

    async def mock_generate(*args, **kwargs):
        return LLMResponse(
            content="go north",
            model="mock-model",
            prompt_tokens=100,
            completion_tokens=10,
            total_tokens=110,
            cost_usd=0.001,
            latency_ms=50.0
        )

    provider.generate = AsyncMock(side_effect=mock_generate)
    provider.get_model_info.return_value = {"provider": "mock", "model": "mock-model"}
    return provider
