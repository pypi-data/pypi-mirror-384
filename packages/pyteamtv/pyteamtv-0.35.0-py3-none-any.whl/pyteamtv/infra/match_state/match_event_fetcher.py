from datetime import datetime, timezone
from threading import Event

import requests
import time
from queue import Queue


def match_event_fetcher(
    event_stream_url: str, match_event_queue: Queue, should_stop: Event
) -> None:
    last_event_id = None

    while not should_stop.is_set():
        url = event_stream_url
        if last_event_id:
            url += "?last-event-id={}".format(last_event_id)

        response = requests.get(url, timeout=2)

        events = response.json()
        for event in events:
            occurred_on = datetime.fromisoformat(
                event["occurred_on"].replace("Z", "+00:00")
            ).replace(tzinfo=timezone.utc)
            match_event_queue.put(
                dict(
                    eventType=event["event_name"],
                    eventAttributes=event["event_attributes"],
                    occurredOn=occurred_on,
                )
            )
            last_event_id = event["event_id"]

        time.sleep(1)
