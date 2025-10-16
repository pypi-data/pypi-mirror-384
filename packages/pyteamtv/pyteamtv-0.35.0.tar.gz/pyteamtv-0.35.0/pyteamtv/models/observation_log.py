from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from pyteamtv.models.sporting_event import SportingEvent

from pyteamtv.infra.requester import Requester
from pyteamtv.models.list import List
from pyteamtv.models.observation import Observation


class ObservationLog(List[Observation]):
    def __init__(
        self,
        content_class: Type[Observation],
        requester: Requester,
        method: str,
        url: str,
        clock_id: str,
        sporting_event: "SportingEvent",
    ):
        super().__init__(content_class, requester, method, url)
        self._clock_id = clock_id
        self._sporting_event = sporting_event

    @property
    def sporting_event(self):
        return self._sporting_event

    def get_mapping_stats(self):
        stats = dict(success=0, failed=0)
        for observation in self:
            if observation.clock_id == self._clock_id:
                stats["success"] += 1
            else:
                stats["failed"] += 1
        return stats
