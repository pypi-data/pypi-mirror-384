from pyteamtv.infra.requester import Requester


class TeamTVObject(object):
    def __init__(self, requester: Requester, attributes: dict):
        self._requester = requester
        self.__attributes = attributes

        self._use_attributes(attributes)

    @property
    def raw_attributes(self):
        return self.__attributes

    @property
    def metadata(self):
        return self._metadata

    @property
    def is_local(self):
        return self._is_local

    def _use_attributes(self, attributes: dict):
        self._metadata = attributes.get("_metadata", {})

        shared_type = self._metadata.get("source", {}).get("type", {})
        self._is_local = (shared_type is None) or (shared_type == "ResourceGroup")

    def has_privilege(self, action: str) -> bool:
        for privilege, status in self.metadata.get("privilegesV2", {}).items():
            if privilege.endswith(":" + action):
                return status["ok"]
        return False
