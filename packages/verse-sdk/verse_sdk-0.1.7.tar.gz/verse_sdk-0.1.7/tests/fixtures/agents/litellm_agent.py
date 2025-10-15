from tests.fixtures.agents.prompt import SYSTEM_PROMPT
from tests.fixtures.datasource import datasource
from verse_sdk import verse

from .litellm import get_completion_text, run_completion, run_completion_async


class LitellmAgent:
    def ask_about_friends(self, character_name: str):
        """
        A sample question that should trigger:
        -   `get_all_characters`
        -   `get_friends`
        """
        input = f"""What are {character_name}'s friends?"""

        with verse.span(
            "Character Friends Agent",
            op="agent",
            input=input,
            scope="test_agent",
        ) as span:
            response = run_completion(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": input},
                ],
                datasource,
            )

            output = get_completion_text(response)
            span.output(output=output)
            return output

    async def tell_story_about_character(self, character_name: str):
        """
        A sample question that should trigger:
        -   `get_character_by_id`
        -   `get_character_location`
        -   `get_character_occupation`
        """
        input = f"""Tell me a story about the day in the life of {character_name}. Include the following details:
        -   What they do for friends
        -   What they do for work
        -   Where they live
        """

        with verse.span(
            "Character Story Agent",
            op="agent",
            input=input,
            scope="test_agent",
        ) as span:
            output = ""
            parts = run_completion_async(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": input},
                ],
                datasource,
            )

            async for part in parts:
                output += part
                yield part

            span.output(output=output)
