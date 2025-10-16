from .person import Person
from .teamtv_object import TeamTVObject


class Player(TeamTVObject):
    @property
    def team(self):
        return self._team

    @property
    def number(self):
        return self._number

    @property
    def person(self):
        return self._person

    def _use_attributes(self, attributes: dict):
        self._person = Person(self._requester, attributes["person"])
        self._number = attributes["number"]
        self._team = attributes["team"]

        super()._use_attributes(attributes)

    def __repr__(self):
        return f"<Player name='{self.person.name}' team='{self.team.name}'>"
