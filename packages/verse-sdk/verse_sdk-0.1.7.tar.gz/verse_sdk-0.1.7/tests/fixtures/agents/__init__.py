from tests.fixtures.agents.litellm_agent import LitellmAgent
from tests.fixtures.agents.pydantic_agent import PydanticAgent


class AgentFixtures:
    """Factory for different agent fixtures"""

    def create_litellm_agent(self) -> LitellmAgent:
        """Create a Litellm agent"""
        return LitellmAgent()

    def create_pydantic_agent(self) -> PydanticAgent:
        """Create a Pydantic agent"""
        return PydanticAgent()
