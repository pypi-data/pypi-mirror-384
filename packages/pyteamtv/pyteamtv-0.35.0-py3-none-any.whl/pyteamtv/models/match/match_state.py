from dataclasses import dataclass
from typing import Optional


@dataclass
class MatchState:
    home_score: int
    away_score: int
    time: float
    current_period: int
    period_active: bool
    current_possession_team_id: Optional[str] = None

    @property
    def time_str(self):
        if not self.period_active:
            if self.current_period == 0:
                return "START"
            elif self.current_period == 1:
                return "RUST"
            elif self.current_period == 2:
                return "EINDE"
        else:
            minutes, seconds = divmod(int(self.time), 60)
            return f"{minutes:02d}:{seconds:02d}"

    def __repr__(self):
        return f"<MatchState period={self.current_period} time={self.time} score={self.home_score}-{self.away_score} active={self.period_active}>"
