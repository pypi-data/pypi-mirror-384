from datetime import datetime
from .teamtv_object import TeamTVObject


class BulkObservation(TeamTVObject):
    @property
    def bulk_observation_id(self) -> str:
        return self._bulk_observation_id

    @property
    def description(self) -> str:
        return self._description

    @property
    def observation_count(self) -> int:
        return self._observation_count

    @property
    def created(self) -> datetime:
        return self._created

    def _use_attributes(self, attributes: dict):
        self._bulk_observation_id = attributes["bulkObservationId"]
        self._description = attributes["description"]
        self._observation_count = attributes["observationCount"]
        self._created = datetime.fromisoformat(
            attributes["created"].replace("Z", "+00:00")
        )

        super()._use_attributes(attributes)
