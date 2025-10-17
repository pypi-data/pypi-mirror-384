import requests
from requests.auth import HTTPBasicAuth
import json
from pprint import pprint

from typing import List

from ocpy.api.api_client import OpenCastBaseApiClient


class User:
    def __init__(self, user, password, url, data):
        self.base_url = url
        self.user = user
        self.password = password
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_roles(self, **kwargs) -> list:
        url = self.base_url + "/roles"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.json()
        raise Exception("Could not get user roles!")

    def get_email(self) -> str:
        return self.data["email"]

    def get_name(self) -> str:
        return self.data["name"]

    def get_provider(self) -> str:
        return self.data["provider"]

    def get_username(self) -> str:
        return self.data["username"]

    def get_user_role(self) -> str:
        return self.data["userrole"]


class Organization:
    def __init__(self, user, password, url, data):
        self.base_url = url
        self.user = user
        self.password = password
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_admin_role(self) -> str:
        return self.data["adminRole"]

    def get_anonymous_role(self) -> str:
        return self.data["anonymousRole"]

    def get_id(self) -> List[str]:
        return self.data["id"]

    def get_name(self) -> str:
        return self.data["name"]

    def get_properties(self, **kwargs) -> list:
        url = self.base_url + "/properties"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.json()
        raise Exception("Could not get user roles!")


class BaseApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None, **kwargs):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/api"

    def get_api_info(self, **kwargs) -> dict:
        res = requests.get(
            self.base_url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.json()
        raise Exception("Could not get api info!")

    def get_api_version(self, **kwargs) -> dict:
        url = self.base_url + "/version"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.json()
        raise Exception("Could not get api version!")

    def get_default_api_version(self, **kwargs) -> dict:
        url = self.base_url + "/version/default"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.json()
        raise Exception("Could not get default api version!")

    def get_user_info(self, **kwargs) -> User:
        url = self.base_url + "/info/me"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            user = User(self.user, self.password, url, res.json())
            return user
        raise Exception("Could not get user info!")

    def get_organization_info(self, **kwargs) -> Organization:
        url = self.base_url + "/info/organization"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            orga = Organization(self.user, self.password, url, res.json())
            return orga
        raise Exception("Could not get organization info!")

    def clear_index(self, **kwargs):
        """Clears the index for the external API. This is useful if the API returns events that don't exist anymore.
        There is another clearIndex function for the admin ui. Also the engage player uses another endpoint
        (the search endpoint) which can't be cleared, but single items can be deleted from search using the search
        endpoint's delete function."""
        url = self.base_url + "/clearIndex"
        res = requests.post(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return "ok"
        raise Exception("Could not get clear index!")

    def recreate_index(self, service=None, **kwargs):
        """Recreates the index for the external API (optionally for a specific service). Allowed services are:
        Groups, Acl, Themes, Series, Scheduler, Workflow, AssetManager and Comments.
        The service order (see above) is very important! Make sure, you do not run index rebuild for
        more than one service at a time!
        The service parameter can be omitted.

        This is useful if the API returns events that don't exist anymore.
        There is another recreateIndex function for the admin ui. Also the engage player uses another endpoint
        (the search endpoint) which can't be recreated, but single items can be deleted from search using the search
        endpoint's delete function."""
        url = self.base_url + "/recreateIndex"
        if service is not None:
            url += "/" + service
        res = requests.post(url, auth=HTTPBasicAuth(self.user, self.password), **kwargs)
        if res.ok:
            return "ok"
        raise Exception("Could not get clear index!")


def main():
    api = BaseApi()
    info = api.get_api_info()
    pprint(info)
    pprint(api.get_api_version())
    pprint(api.get_default_api_version())
    user = api.get_user_info()
    pprint(user)
    pprint(user.get_roles())
    pprint(api.get_organization_info())
    pprint(api.get_organization_info().get_properties())
    print(api.clear_index())
    print(api.recreate_index())


if __name__ == "__main__":
    main()
