from typing import Optional

from ..types import ExporterConfig


class OtelConfig(ExporterConfig):
    host: Optional[str]
