from dataclasses import dataclass
from typing import Optional


@dataclass
class Team:
    team_id: str
    name: str
    short_code: str
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


@dataclass
class MatchConfig:
    home_team: Team
    away_team: Team
    period_count: int

    @classmethod
    def empty(cls):
        return cls(
            home_team=Team(team_id="home", name="Home", short_code="HOM"),
            away_team=Team(team_id="away", name="Away", short_code="AWA"),
            period_count=2,
        )
