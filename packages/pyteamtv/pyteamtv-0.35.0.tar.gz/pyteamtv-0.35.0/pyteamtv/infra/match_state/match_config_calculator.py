from datetime import timedelta, datetime
from typing import List

from .event_store import Event
from ...models.match.match_config import MatchConfig, Team


def calculate_match_config(events: List[Event], timestamp: datetime) -> MatchConfig:
    match_config = MatchConfig.empty()

    for event in events:
        event_type = event.event_type
        event_attributes = event.attributes
        occurred_on = event.occurred_on

        if event_type == "SportingEventCreated":
            match_config.home_team = Team(
                team_id=event_attributes["homeTeam"]["teamId"],
                name=event_attributes["homeTeam"]["name"],
                short_code=event_attributes["homeTeam"]["shortCode"],
                primary_color=event_attributes["homeTeam"]["appearance"][
                    "primaryColor"
                ],
                secondary_color=event_attributes["homeTeam"]["appearance"][
                    "secondaryColor"
                ],
            )
            match_config.away_team = Team(
                team_id=event_attributes["awayTeam"]["teamId"],
                name=event_attributes["awayTeam"]["name"],
                short_code=event_attributes["awayTeam"]["shortCode"],
                primary_color=event_attributes["awayTeam"]["appearance"][
                    "primaryColor"
                ],
                secondary_color=event_attributes["awayTeam"]["appearance"][
                    "secondaryColor"
                ],
            )
            match_config.period_count = event_attributes.get("matchConfig", {}).get(
                "periodCount", 2
            )
        elif event_type == "MatchConfigChanged":
            if "periodCount" in event_attributes:
                match_config.period_count = event_attributes["periodCount"]

    return match_config
