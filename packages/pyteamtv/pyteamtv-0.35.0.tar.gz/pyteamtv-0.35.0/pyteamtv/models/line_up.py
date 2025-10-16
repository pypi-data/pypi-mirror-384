from typing import Literal, NewType, Dict, TYPE_CHECKING

from .teamtv_object import TeamTVObject

if TYPE_CHECKING:
    from .person import Person
    from .team import Team

Position = NewType("Position", Literal["ATTACK", "DEFENCE"])


class LineUp(TeamTVObject):
    @property
    def line_up_id(self):
        return self._line_up_id

    @property
    def sporting_event(self):
        return self._sporting_event

    def sync_players(self, team: "Team", positions: Dict["Person", Position]):
        # Make sure we only sync when things changed
        person_id_positions = {
            person.person_id: position for person, position in positions.items()
        }
        current_person_id_positions = {
            player["personId"]: player["position"]
            for player in self._roles_per_team.get(team.team_id, [])
        }

        if person_id_positions != current_person_id_positions:
            self._requester.request(
                "POST",
                f"/lineUps/{self.line_up_id}/resetTeamLineUp",
                {"teamId": team.team_id},
            )
            for person_id, position in person_id_positions.items():
                self._requester.request(
                    "POST",
                    f"/lineUps/{self.line_up_id}/addPlayer",
                    {
                        "teamId": team.team_id,
                        "personId": person_id,
                        "position": position,
                    },
                )

    def _use_attributes(self, attributes: dict):
        self._sporting_event = attributes["sportingEvent"]
        self._line_up_id = attributes["lineUpId"]
        self._roles_per_team = attributes["rolesPerTeam"]
        if not isinstance(self._roles_per_team, dict):
            self._roles_per_team = {}

        super()._use_attributes(attributes)

    def __repr__(self):
        return f"<LineUp sportingEvent={self.sporting_event}>"
