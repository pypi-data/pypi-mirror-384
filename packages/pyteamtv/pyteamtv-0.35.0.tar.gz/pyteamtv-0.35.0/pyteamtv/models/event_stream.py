from datetime import datetime, timezone
import time
from queue import Queue
from typing import Iterator, Tuple, Optional

from threading import Thread, Event as ThreadEvent

from .match.match_config import MatchConfig
from .match.match_state import MatchState
from .teamtv_object import TeamTVObject
from ..infra.match_state.event_store import QueueEventStore, Event
from ..infra.match_state.match_config_calculator import calculate_match_config
from ..infra.match_state.match_event_fetcher import match_event_fetcher
from ..infra.match_state.match_state_calculator import calculate_match_state


def utcnow() -> datetime:
    return datetime.fromtimestamp(time.time(), timezone.utc)


class EventStreamReader(Iterator):
    def get_last_event(
        self, timestamp: Optional[datetime] = None
    ) -> Optional[Tuple[MatchConfig, MatchState, Event]]:
        events = self.event_store.get_events(timestamp)

        if timestamp is None:
            timestamp = (
                utcnow()
            )  # TODO: or should this be occurredOn attribute of event

        while len(events) > self.cursor:
            state = calculate_match_state(events[: self.cursor + 1], timestamp)
            match_config = calculate_match_config(events[: self.cursor + 1], timestamp)
            item = events[self.cursor]
            self.cursor += 1
            if self.start_timestamp and item.occurred_on < self.start_timestamp:
                continue

            return match_config, state, item

        return None

    def get_state(
        self, timestamp: Optional[datetime] = None
    ) -> Tuple[MatchConfig, MatchState]:
        events = self.event_store.get_events(timestamp)

        if timestamp is None:
            timestamp = (
                utcnow()
            )  # TODO: or should this be occurredOn attribute of event

        state = calculate_match_state(events[: self.cursor + 1], timestamp)
        match_config = calculate_match_config(events[: self.cursor + 1], timestamp)
        return match_config, state

    def __next__(self) -> Tuple[MatchConfig, MatchState, Event]:
        while True:
            event = self.get_last_event()
            if event:
                return event

            time.sleep(0.1)

    def __init__(self, poll_url: str, seek_to_start: bool = False):
        self.queue = Queue()
        self.start_timestamp = None if seek_to_start else utcnow()
        self.event_store = QueueEventStore(self.queue)
        self.should_stop = ThreadEvent()
        self.cursor = 0
        self.poll_url = poll_url

        self.thread = Thread(target=self._read_to_queue, daemon=True)
        self.thread.start()

    def _read_to_queue(self):
        match_event_fetcher(self.poll_url, self.queue, self.should_stop)

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.should_stop.set()
        self.thread.join()


class EventStream(TeamTVObject):
    @property
    def event_stream_id(self):
        return self._event_stream_id

    @property
    def endpoint_urls(self):
        return self._endpoint_urls

    def __repr__(self):
        return f"<EventStream event_stream_id={self.event_stream_id}>"

    def _use_attributes(self, attributes: dict):
        self._event_stream_id = attributes["eventStreamId"]
        self._endpoint_urls = attributes["endpointUrls"]

        super()._use_attributes(attributes)

    def open(self, seek_to_start: bool = False):
        return EventStreamReader(
            self.endpoint_urls["polling"], seek_to_start=seek_to_start
        )
