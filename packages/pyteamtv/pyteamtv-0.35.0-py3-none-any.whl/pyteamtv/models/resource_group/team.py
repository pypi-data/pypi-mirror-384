from . import _ResourceGroup

from .capabilities import (
    _HasTeamsMixin,
    _HasSportingEventsMixin,
    _HasVideosMixin,
    _HasPersonsMixin,
)


class TeamResourceGroup(
    _ResourceGroup,
    _HasTeamsMixin,
    _HasSportingEventsMixin,
    _HasVideosMixin,
    _HasPersonsMixin,
):
    pass
