from datetime import timedelta, datetime
from typing import List

from .event_store import Event

from ...models.match.match_state import MatchState


def diff(end_time, start_time) -> float:
    d = end_time - start_time
    if isinstance(d, timedelta):
        return d.total_seconds()
    return d


def calculate_match_state(events: List[Event], timestamp: datetime) -> MatchState:
    if len(events) == 0:
        return MatchState(
            home_score=0, away_score=0, current_period=0, period_active=False, time=0
        )

    home_team_id = None
    away_team_id = None

    home_score = 0
    away_score = 0

    time_correction = 0
    pause_time = None

    period_active = False
    current_period = 0
    period_start_time = 0

    current_possession_team_id = None

    for event in events:
        event_type = event.event_type
        event_attributes = event.attributes
        occurred_on = event.occurred_on

        if event_type == "SportingEventCreated":
            home_team_id = event_attributes["homeTeam"]["teamId"]
            away_team_id = event_attributes["awayTeam"]["teamId"]
        elif event_type == "Goal":
            if event_attributes["goalAttributes"]["teamId"] == home_team_id:
                home_score += 1
            elif event_attributes["goalAttributes"]["teamId"] == away_team_id:
                away_score += 1

        elif event_type == "StartPossession":
            current_possession_team_id = event_attributes["startPossessionAttributes"][
                "teamId"
            ]
        elif event_type == "Shot":
            shot_attributes = event_attributes["shotAttributes"]
            if shot_attributes["result"] == "GOAL":
                if current_possession_team_id == home_team_id:
                    home_score += 1
                elif current_possession_team_id == away_team_id:
                    away_score += 1

        elif event_type == "StartPeriod":
            period_start_time = occurred_on
            time_correction = 0
            pause_time = None
            period_active = True
            current_period = int(event_attributes["period"])
        elif event_type == "Time:pause":
            # dont break when events are entered multiple times
            if pause_time is None:
                pause_time = occurred_on
        elif event_type == "Time:resume":
            # dont break when events are entered multiple times
            if pause_time is not None:
                time_correction -= diff(occurred_on, pause_time)
                pause_time = None
        elif event_type == "Time:correction":
            time_correction += float(
                event_attributes["time:correctionAttributes"]["seconds"]
            )
        elif event_type == "EndPeriod":
            period_active = False

    if period_active:
        if pause_time is None:
            base_time = diff(timestamp, period_start_time)
        else:
            base_time = diff(pause_time, period_start_time)
        base_time += time_correction

        current_time = base_time
    else:
        current_time = 0

    return MatchState(
        home_score=home_score,
        away_score=away_score,
        time=current_time,
        current_period=current_period,
        period_active=period_active,
        current_possession_team_id=current_possession_team_id,
    )
