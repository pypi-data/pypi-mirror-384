from enum import Enum
from ..teamtv_object import TeamTVObject
from .capabilities import _HasStorage


class SportType(Enum):
    KORFBALL = "korfball"
    SOCCER = "soccer"
    HOCKEY = "hockey"
    HANDBALL = "handball"
    VOLLEYBALL = "volleyball"
    ATHLETICS = "athletics"
    TENNIS = "tennis"
    BASKETBALL = "basketball"
    RUGBY = "rugby"
    OTHER = "other"

    @classmethod
    def from_sport_name(cls, sport_name: str) -> "SportType":
        """Create SportType from sport name like 'korfball', 'handball', etc.
        Returns SportType.OTHER for unknown sport types."""
        sport_name_lower = sport_name.lower()
        for sport_type in cls:
            if sport_type.value == sport_name_lower:
                return sport_type
        return cls.OTHER

    @classmethod
    def from_tenant_id(cls, tenant_id: str) -> "SportType":
        """Create SportType from tenant_id like 'nl_korfball_rustroest'."""
        parts = tenant_id.split("_")
        if len(parts) < 2:
            raise ValueError(f"Invalid tenant_id format: {tenant_id}")

        sport_name = parts[1]
        return cls.from_sport_name(sport_name)


class _ResourceGroup(TeamTVObject, _HasStorage):
    def _use_attributes(self, attributes: dict):
        super()._use_attributes(attributes)

        self._name = attributes["targetResourceName"]
        self._tenant_id = attributes["tenantId"]
        self._resource_group_id = attributes["resourceGroupId"]
        self._tags = attributes.get("tags", {})
        self._sport_type_value = attributes.get("sportType")

    @property
    def resource_group_id(self):
        return self._resource_group_id

    @property
    def name(self):
        return self._name

    @property
    def tenant_id(self):
        return self._tenant_id

    @property
    def tags(self):
        return self._tags

    @property
    def sport_type(self) -> SportType:
        if self._sport_type_value:
            return SportType.from_sport_name(self._sport_type_value)
        return SportType.OTHER

    def __repr__(self):
        return f"<ResourceGroup name='{self.name}'>"

    def __eq__(self, other):
        if not isinstance(other, _ResourceGroup):
            return False

        return other.resource_group_id == self.resource_group_id
