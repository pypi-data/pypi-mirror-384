import requests
from requests.auth import HTTPBasicAuth
import json
from pprint import pprint

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

    def get_email(self) -> str:
        return self.data["email"]

    def get_name(self) -> str:
        return self.data["name"]

    def get_provider(self) -> str:
        return self.data["provider"]

    def get_username(self) -> str:
        return self.data["username"]

    def get_user_role(self) -> str:
        return self.data["userRole"]


class InfoApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None, **_kwargs):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/info"

    def get_api_info(self, **kwargs) -> dict:
        res = requests.get(
            self.base_url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )
        if res.ok:
            return res.json()
        raise Exception("Could not get api info!")

    def get_components_info(self, **kwargs) -> dict:
        url = self.base_url + "/components.json"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )
        if res.ok:
            return res.json()
        raise Exception("Could not get api version!")

    def get_user_info(self, **kwargs) -> User:
        url = self.base_url + "/me.json"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )
        if res.ok:
            user = User(self.user, self.password, url, res.json())
            return user
        raise Exception("Could not get user info!")


def main():
    api = InfoApi()
    s = api.get_user_info()
    print(s)


if __name__ == "__main__":
    main()
