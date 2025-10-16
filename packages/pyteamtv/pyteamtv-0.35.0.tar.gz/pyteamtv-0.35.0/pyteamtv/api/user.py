from typing import Optional

from pyteamtv.infra.requester import Requester
from pyteamtv.models.list import List
from pyteamtv.models.membership import Membership
from pyteamtv.models.membership_list import MembershipList
from pyteamtv.models.sharing_group import SharingGroup

from .endpoint import API_ENDPOINT
from .token import decode
from ..exceptions import TeamNotFound, InputError
from ..models.access_requester import AccessRequester
from ..models.resource_group.team import TeamResourceGroup


class TeamTVUser(object):
    def __init__(self, jwt_token, use_cache: bool = False):
        self.jwt_token = jwt_token

        token = decode(
            jwt_token,
            verify=False,
        )

        self._requester = Requester(
            f"{API_ENDPOINT}/api", jwt_token, use_cache=use_cache
        )
        self.__token = token

    def get_access_requester(self) -> AccessRequester:
        print(self.__token)

    def get_membership_list(self):
        """
        :return: MembershipList
        """
        return MembershipList(
            Membership, self._requester, "GET", "/users/me/memberships"
        )

    def get_public_sharing_groups(self, sport_type: Optional[str] = None):
        return List(
            SharingGroup,
            self._requester,
            "GET",
            f"/sharingGroups?sportType={sport_type}"
            if sport_type
            else "/sharingGroups",
        )

    def get_team(
        self, name: Optional[str] = None, resource_group_id: Optional[str] = None
    ) -> TeamResourceGroup:
        membership_list = self.get_membership_list()
        if resource_group_id:
            membership = membership_list.get_membership_by_resource_group_id(
                resource_group_id
            )

            if not membership:
                raise TeamNotFound(
                    f"No team with resource group id '{resource_group_id}' found."
                )
        elif name:
            membership = membership_list.get_membership_by_name(name=name)

            if not membership:
                raise TeamNotFound(f"No team named '{name}' found.")
        else:
            raise InputError(f"Either `name` or `resource_group_id` must be specified.")

        return membership.resource_group

    def get_memberships(
        self, tenant_id: Optional[str] = None, type_: Optional[str] = None
    ) -> List[Membership]:
        return self.get_membership_list().get_memberships(tenant_id, type_)
