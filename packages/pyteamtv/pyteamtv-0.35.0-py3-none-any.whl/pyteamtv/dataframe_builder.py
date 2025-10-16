import math

from typing import List, Optional

from pyteamtv.models.observation_log import ObservationLog
from pyteamtv.models.person import Person
from pyteamtv.models.resource_group.team import TeamResourceGroup
from pyteamtv.models.sporting_event import SportingEvent
from pyteamtv.models.team import Team


def pol2cart(angle: float, distance: float):
    if angle > 90:
        angle -= 360
    angle += 90

    phi = (angle / 360) * 2 * math.pi
    rho = distance

    x = rho * math.cos(phi)
    y = rho * math.sin(phi)
    return x, y


class DataframeBuilder:
    def __init__(self, resource_group: TeamResourceGroup):
        self.teams = {team.team_id: team for team in resource_group.get_teams()}
        self.persons = {
            person.person_id: person for person in resource_group.get_persons()
        }
        self._requester = resource_group._requester

    def build_df(self, observation_logs: List[ObservationLog]):
        try:
            import pandas as pd
        except ImportError:
            raise Exception("You don't have pandas installed. Please install first")

        return pd.DataFrame.from_records(self.build_records(observation_logs))

    def _build_person_data(self, attributes: dict, key_prefix: Optional[str] = None):
        in_key = "person"
        out_prefix = ""
        if key_prefix:
            in_key = f"{key_prefix}Person"
            out_prefix = key_prefix + "_"

        pk_name = f"{in_key}Id"

        if in_key in attributes:
            if pk_name in attributes:
                person_id = attributes[pk_name]
            else:
                # In some cases the original personId field is removed but the person data is still there.
                # When that happens use the personId from the nested data
                person_id = attributes[in_key]["personId"]

            person = {
                f"{out_prefix}person_id": person_id,
                f"{out_prefix}first_name": attributes[in_key]["firstName"],
                f"{out_prefix}last_name": attributes[in_key]["lastName"],
                f"{out_prefix}number": attributes[in_key]["number"],
                f"{out_prefix}full_name": attributes[in_key]["firstName"]
                + " "
                + attributes[in_key]["lastName"],
            }
        elif pk_name in attributes:
            person_: Optional[Person] = self.persons.get(attributes[pk_name])
            if person_:
                person = {
                    f"{out_prefix}person_id": attributes[pk_name],
                    f"{out_prefix}first_name": person_.first_name,
                    f"{out_prefix}last_name": person_.last_name,
                    f"{out_prefix}full_name": person_.name,
                }
            else:
                person = dict()
        else:
            person = dict()
        return person

    def get_team_data(self, sporting_event: SportingEvent, attributes: dict):
        """
        1. Get it from the list of teams
        2. Get it from the attributes
        3. Get a generic one from the SportingEvent

        NOTE: this function has a side-effect: the self.teams dictionary will
              be updated when a team is not found and a fake team is created

        """

        team_id = attributes["teamId"]
        if sporting_event.home_team_id == team_id:
            ground = "home"
        else:
            ground = "away"

        if team_id in self.teams:
            team = self.teams[team_id]
        else:
            if "team" in attributes:
                # This can happen when a team is not shared, but the data is.
                # For certain leagues the data is entered from the club account
                # and send to the exchange. The teams entities are not shared
                team = Team(self._requester, attributes)
            else:
                home_team_name, away_team_name = sporting_event.name.split(" - ")
                team = Team(
                    self._requester,
                    {
                        "teamId": team_id,
                        "name": (
                            home_team_name if ground == "home" else away_team_name
                        ),
                    },
                )

            # It's a bad practice to update data in a get function
            # TODO: refactor
            self.teams[team_id] = team

        return dict(
            team_id=team.team_id,
            team_name=team.name,
            team_ground=ground,
            position=attributes.get("position"),
            team_name_full=team.full_name,
            team_key=team.key,
        )

    def build_records(self, observation_logs: List[ObservationLog]):
        observations = []
        skip_attributes = {
            "teamId",
            "personId",
            "team",
            "person",
        }

        for observation_log in observation_logs:
            sporting_event = observation_log.sporting_event

            team = dict()
            possession_id = None
            possession_idx = 0
            has_start_possession = any(
                observation.code == "START-POSSESSION"
                for observation in observation_log
            )
            for observation in observation_log:
                if has_start_possession and observation.code == "POSSESSION":
                    # When dataset contains start-possession, ignore the possession observations
                    # TODO: this might break when livetagging and video tagging are combined
                    #       as only livetagging contains start-possession
                    continue

                if observation.code in ("START-POSSESSION", "POSSESSION"):
                    team = self.get_team_data(sporting_event, observation.attributes)
                    person = {}
                    extra_persons = {}
                    possession_id = (
                        f"{sporting_event.sporting_event_id}:{possession_idx:05d}"
                    )
                    possession_idx += 1
                else:
                    person = self._build_person_data(observation.attributes)
                    extra_persons = {}
                    # Find all attributes ending with PersonId (capital P)
                    # Note: "personId" (lowercase p) won't match, so it's handled separately above
                    for key in observation.attributes.keys():
                        if key.endswith("PersonId"):
                            # Extract prefix (e.g., "opponent" from "opponentPersonId")
                            prefix = key[:-8]  # Remove "PersonId"
                            extra_person = self._build_person_data(
                                observation.attributes, prefix
                            )
                            extra_persons.update(extra_person)
                            # Add these to skip_attributes dynamically
                            skip_attributes.add(key)
                            skip_attributes.add(f"{prefix}Person")

                attributes = dict(possession_id=possession_id)
                attributes.update(team)
                attributes.update(person)
                attributes.update(extra_persons)
                for k, v in observation.attributes.items():
                    if k not in skip_attributes:
                        attributes[k] = v

                if "angle" in attributes and "distance" in attributes:
                    attributes["x"], attributes["y"] = pol2cart(
                        attributes["angle"], attributes["distance"]
                    )

                if "position" in attributes and attributes["position"]:
                    attributes["position"] = attributes["position"].split(":")[0]

                observation_dict = dict(
                    sporting_event_id=sporting_event.sporting_event_id,
                    sporting_event_name=sporting_event.name,
                    sporting_event_scheduled_at=sporting_event.scheduled_at,
                    observation_id=observation.observation_id,
                    clock_id=observation.clock_id,
                    start_time=observation.start_time,
                    end_time=observation.end_time,
                    code=observation.code,
                    description=observation.description,
                    **attributes,
                )

                observations.append(observation_dict)

        return observations
