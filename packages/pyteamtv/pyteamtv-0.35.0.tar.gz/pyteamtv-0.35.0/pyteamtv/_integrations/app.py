import os
from typing import Optional, MutableMapping

from pyteamtv import TeamTVUser, TeamTVApp
from pyteamtv.exceptions import TokenMissing, ConfigurationError
from pyteamtv.models.access_requester import AccessRequester
from pyteamtv.models.resource_group.team import TeamResourceGroup


class App:
    def __init__(self, api):
        self.api = api

        self._current_resource_group: Optional[TeamResourceGroup] = None
        self._membership_list = None

        self.observation_logs = dict()
        self.sporting_events = dict()

    @property
    def current_resource_group(self) -> Optional[TeamResourceGroup]:
        if isinstance(self.api, TeamTVUser):
            return None

        if self._current_resource_group is None:
            self._current_resource_group: TeamResourceGroup = (
                self.api.get_resource_group()
            )

        return self._current_resource_group

    @property
    def membership_list(self):
        if not isinstance(self.api, TeamTVUser):
            return None

        if self._membership_list is None:
            self._membership_list = self.api.get_membership_list()

        return self._membership_list

    def get_access_requester(self) -> AccessRequester:
        return self.api.get_access_requester()

    def should_refresh(self, token: Optional[str]):
        if not token:
            return False
        return token != self.api.jwt_token

    def reset(self):
        self.observation_logs = dict()
        self.sporting_events = dict()

    def set_team(self, name: str):
        if not self.membership_list:
            raise Exception("Cannot set_team in TeamTVApp")

        if not self.current_resource_group or self.current_resource_group.name != name:
            self.current_resource_group = self.membership_list.get_membership_by_name(
                name=name
            ).resource_group  # type: TeamResourceGroup
            self.reset()

    def get_sporting_events(self):
        if not self.sporting_events:
            self.sporting_events = {
                sporting_event.sporting_event_id: sporting_event
                for sporting_event in sorted(
                    self.current_resource_group.get_sporting_events(),
                    key=lambda sporting_event: sporting_event.scheduled_at,
                    reverse=True,
                )
            }
        return self.sporting_events.values()

    def get_sporting_event(self, sporting_event_id: str):
        if sporting_event_id not in self.sporting_events:
            self.sporting_events[
                sporting_event_id
            ] = self.current_resource_group.get_sporting_event(sporting_event_id)
        return self.sporting_events[sporting_event_id]

    def get_observation_log(self, sporting_event_id: str):
        if sporting_event_id not in self.observation_logs:
            sporting_event = self.get_sporting_event(sporting_event_id)
            self.observation_logs[
                sporting_event_id
            ] = sporting_event.get_observation_log()
        return self.observation_logs[sporting_event_id]

    def get_sports_type(self) -> Optional[str]:
        tenant_id = self.current_resource_group.tenant_id
        for sports_type in [
            "korfball",
            "soccer",
            "hockey",
            "tennis",
            "handball",
            "volleybal",
        ]:
            if sports_type in tenant_id:
                return sports_type
        return None


def _get_current_app(
    app_id: Optional[str],
    session: MutableMapping,
    token: Optional[str],
    use_cache: bool = False,
    raise_on_missing_token: bool = True,
) -> Optional[App]:
    current_app: Optional[App] = session.get("current_app")

    if not current_app or current_app.should_refresh(token):
        if "TEAMTV_TOKEN" in os.environ:
            api = TeamTVUser(jwt_token=os.environ["TEAMTV_TOKEN"], use_cache=use_cache)
        else:
            if not app_id:
                app_id = os.environ.get("TEAMTV_APP_ID")
                if not app_id:
                    raise ConfigurationError("app_id must be set")

            if token:
                api = TeamTVApp(jwt_token=token, app_id=app_id, use_cache=use_cache)
            elif raise_on_missing_token:
                raise TokenMissing("Token not set")
            else:
                return None

        session["current_app"] = App(api=api)

    return session["current_app"]
