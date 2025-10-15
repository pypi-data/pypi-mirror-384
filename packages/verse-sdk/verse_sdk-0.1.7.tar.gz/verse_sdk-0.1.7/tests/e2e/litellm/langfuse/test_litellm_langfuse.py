import uuid

import pytest

from tests.fixtures.agents import AgentFixtures
from verse_sdk import verse


@pytest.mark.e2e
def test_litellm_langfuse_http_export():
    with verse.trace(
        "litellm_e2e", project_id="proj_test123", session_id=str(uuid.uuid4())
    ) as t:
        agent = AgentFixtures().create_litellm_agent()
        resp = agent.ask_about_friends("Ollie the Owl")
        t.update(output=resp)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_litellm_langfuse_http_export_async():
    with verse.trace(
        "litellm_e2e", project_id="proj_test123", session_id=str(uuid.uuid4())
    ):
        agent = AgentFixtures().create_litellm_agent()
        async for _ in agent.tell_story_about_character("Cleo the Cat"):
            pass
