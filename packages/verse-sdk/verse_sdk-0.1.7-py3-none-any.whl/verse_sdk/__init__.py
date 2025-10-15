from .decorators import lazily
from .sdk_builder import VerseSDKBuilder

verse = VerseSDKBuilder()
exporters = verse.exporters

observe = lazily(verse, "observe")
observe_generation = lazily(verse, "observe_generation")
observe_span = lazily(verse, "observe_span")
observe_tool = lazily(verse, "observe_tool")
observe_trace = lazily(verse, "observe_trace")
shutdown = verse.shutdown

__all__ = [
    "exporters",
    "observe",
    "observe_generation",
    "observe_span",
    "observe_trace",
    "shutdown",
    "verse",
]
