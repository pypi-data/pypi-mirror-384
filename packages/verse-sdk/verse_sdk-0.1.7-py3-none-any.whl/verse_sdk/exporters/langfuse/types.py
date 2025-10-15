from typing import Optional

from ..types import ExporterConfig


class LangfuseConfig(ExporterConfig):
    host: Optional[str]
    public_key: str
    region: Optional[str]
    secret_key: str
