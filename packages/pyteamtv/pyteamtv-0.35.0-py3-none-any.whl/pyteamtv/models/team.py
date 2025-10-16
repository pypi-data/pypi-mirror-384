import re

from .list import List
from .person import Person
from .player import Player
from .teamtv_object import TeamTVObject


# Compile a regex pattern for matching the sponsor name
sponsor_remove_pattern = re.compile(r"/(.+?) ([0-9a-z]+)$")

# Compile a regex pattern for replacing multiple whitespace with a single one
whitespace_replace_pattern = re.compile(r"\s+")


def strip_sponsor(name: str) -> str:
    # Replace the sponsor name with just the team name
    name = sponsor_remove_pattern.sub(r" \2", name)
    return whitespace_replace_pattern.sub(" ", name)


def get_team_key(team_name: str) -> str:
    # Remove the sponsor name, convert the team name to lowercase,
    # remove any whitespace, and return the result
    return strip_sponsor(team_name).lower().replace(" ", "").strip()


class Team(TeamTVObject):
    @property
    def full_name(self):
        return self._full_name

    @property
    def key(self):
        return self._key

    @property
    def name(self):
        return self._name

    @property
    def team_id(self):
        return self._team_id

    @property
    def sport_type(self):
        return self._sport_type

    @property
    def tags(self):
        return self._tags

    def _use_attributes(self, attributes: dict):
        tags = attributes.get("tags", {})
        if not isinstance(tags, dict):
            tags = {}

        self._team_id = attributes["teamId"]
        self._full_name = attributes["name"]
        self._key = get_team_key(self._full_name)
        self._name = strip_sponsor(self._full_name)

        self._sport_type = attributes.get("sportType")
        self._tags = tags

        super()._use_attributes(attributes)

    def __repr__(self):
        return f"<Team name={self.full_name} team_id={self.team_id}>"

    def get_players(self):
        def player_factory(requester, attributes) -> Player:
            return Player(requester, dict(team=self, **attributes))

        return List(
            player_factory, self._requester, "GET", f"/teams/{self.team_id}/players"
        )

    def add_player(self, person: Person, number: str) -> Player:
        data = self._requester.request(
            "POST",
            f"/teams/{self.team_id}/players",
            {"personId": person.person_id, "number": number},
        )

        # Add the data from the person object. The
        # players POST api doesn't return the person object
        data["person"] = dict(
            personId=person.person_id,
            firstName=person.first_name,
            lastName=person.last_name,
            gender=person.gender,
            tags=person.tags,
        )
        data["team"] = self
        return Player(self._requester, data)
