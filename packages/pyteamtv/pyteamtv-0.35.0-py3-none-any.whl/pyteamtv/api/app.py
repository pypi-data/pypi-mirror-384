from pyteamtv.infra.requester import Requester
from pyteamtv.models.resource_group.factory import factory as resource_group_factory
from .endpoint import API_ENDPOINT

from .token import decode
from ..models.access_requester import AccessRequester


class TeamTVApp(object):
    def __init__(self, jwt_token, app_id: str, use_cache: bool = False):
        self.jwt_token = jwt_token

        token = decode(jwt_token, app_id)

        self._requester = Requester(
            f"{API_ENDPOINT}/api", jwt_token, use_cache=use_cache
        )
        self.__token = token

    def get_resource_group(self):
        """
        :rtype: :class:`pyteamtv.resource_group.team.Team`
        """
        data = self._requester.request("GET", "/resourceGroups/current")

        return resource_group_factory(self._requester, data)

    def get_access_requester(self) -> AccessRequester:
        return AccessRequester(
            user_id=self.__token["sub"],
            tenant_id=self.__token["scope"]["tenantId"],
            role_names=self.__token["scope"]["roleNames"],
            resource_group_id=self.__token["scope"]["resourceGroupId"],
        )
