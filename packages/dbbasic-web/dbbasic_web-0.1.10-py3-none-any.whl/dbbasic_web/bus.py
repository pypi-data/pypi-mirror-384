"""Message bus using dbbasic-pipe (Unix pipes, TSV streams)"""
import json
from typing import AsyncIterator
from dbbasic.pipe import Pipe
from .settings import DATA_DIR


class EventBus:
    """Event bus using TSV-based streams (no Redis needed)"""

    def __init__(self, stream_dir: str = None):
        self.stream_dir = stream_dir or str(DATA_DIR / "streams")

    def _get_pipe(self, stream: str) -> Pipe:
        """Get or create a pipe for a stream"""
        return Pipe(f"{self.stream_dir}/{stream}.tsv")

    async def publish(self, stream: str, event: dict) -> str:
        """Publish an event to a stream"""
        pipe = self._get_pipe(stream)
        event_json = json.dumps(event)
        pipe.write({"data": event_json})
        return event_json

    async def consume(self, stream: str, group: str = "default", consumer: str = "consumer") -> AsyncIterator[dict]:
        """Consume events from a stream"""
        pipe = self._get_pipe(stream)

        # Read from pipe
        for row in pipe.read():
            data = json.loads(row.get("data", "{}"))
            yield {"data": data}

    def publish_sync(self, stream: str, event: dict) -> str:
        """Synchronous publish (for non-async contexts)"""
        pipe = self._get_pipe(stream)
        event_json = json.dumps(event)
        pipe.write({"data": event_json})
        return event_json
