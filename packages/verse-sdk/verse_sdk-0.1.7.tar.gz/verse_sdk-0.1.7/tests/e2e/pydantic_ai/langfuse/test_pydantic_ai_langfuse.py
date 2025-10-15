import uuid

import pytest

from tests.fixtures.agents import AgentFixtures
from verse_sdk import verse


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_pydantic_ai_langfuse_http_export():
    with verse.trace(
        "pydantic_ai_e2e", project_id="proj_test123", session_id=str(uuid.uuid4())
    ) as t:
        agent = AgentFixtures().create_pydantic_agent()
        resp = await agent.ask_about_friends("Ollie the Owl")
        t.update(output=resp)
