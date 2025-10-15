from uuid import UUID

from archipy.helpers.metaclasses.singleton import Singleton
from features.scenario_context import ScenarioContext


class ScenarioContextPoolManager(metaclass=Singleton):
    """Manager for scenario-specific context objects.

    This class maintains a pool of scenario contexts indexed by scenario ID,
    ensuring that each scenario has its own isolated context.
    """

    def __init__(self):
        """Initialize the pool manager."""
        self.context_pool = {}

    def get_context(self, scenario_id: UUID) -> ScenarioContext:
        """Get or create a scenario context for the given ID."""
        if scenario_id not in self.context_pool.keys():
            self.context_pool[scenario_id] = ScenarioContext(scenario_id)
        return self.context_pool[scenario_id]

    def cleanup_context(self, scenario_id: UUID) -> None:
        """Clean up a specific scenario context."""
        if scenario_id in self.context_pool:
            self.context_pool[scenario_id].cleanup()
            del self.context_pool[scenario_id]

    def cleanup_all(self) -> None:
        """Clean up all scenario contexts."""
        for scenario_id, scenario_context in list(self.context_pool.items()):
            scenario_context.cleanup()
            del self.context_pool[scenario_id]
