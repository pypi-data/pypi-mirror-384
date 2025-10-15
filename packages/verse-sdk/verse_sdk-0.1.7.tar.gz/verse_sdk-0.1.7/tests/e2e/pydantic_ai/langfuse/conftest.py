from dotenv import load_dotenv

from verse_sdk import verse

load_dotenv()


verse.init(
    app_name="verse_langfuse_pydantic_ai_e2e",
    environment="development",
    exporters=[
        verse.exporters.langfuse(),
        verse.exporters.otel(),
    ],
    vendor="pydantic_ai",
    version="1.0.0",
)
