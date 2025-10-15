from pydantic_ai import Agent

from tests.fixtures.agents.prompt import SYSTEM_PROMPT
from tests.fixtures.datasource import datasource
from verse_sdk import verse


class PydanticAgent:
    agent: Agent

    def __init__(self):
        """Initialize the agent"""
        self.agent = Agent(
            model="openai:gpt-4o-mini",
            system_prompt=SYSTEM_PROMPT,
            tools=datasource,
        )

    def ask_about_character(self, character_id: int):
        """
        A sample question that should trigger:
        -   `get_character_by_id`
        -   `get_character_location`
        -   `get_character_occupation`
        """
        return self._ask(
            f"""
            Tell me about character with ID {character_id}.
            Where do they live and what do they do for work?
            """.strip()
        )

    def ask_about_friends(self, character_name: str):
        """
        A sample question that should trigger:
        -   `get_all_characters`
        -   `get_friends`
        """
        return self._ask(f"""What are {character_name}'s friends?""")

    async def _ask(self, query: str):
        """Run a prompt with SDK tracing"""
        with verse.span("Character Agent", op="agent", scope="test_agent") as s:
            response = await self.agent.run(
                query,
            )

            result = response.output
            s.input(input=query)
            s.output(output=result)
            return result
