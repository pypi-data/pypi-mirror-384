#  Copyright (c) 2019. Tobias Kurze

import requests
from urllib.parse import urlparse
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime

from typing import List, Optional

from ocpy import OcPyRequestException
from ocpy.api.api_client import OpenCastBaseApiClient
from ocpy.model.organization import Organization


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

    def get_name(self) -> str:
        return self.data["name"]

    def get_username(self) -> str:
        return self.data["username"]

    def get_email(self) -> Optional[str]:
        try:
            return self.data["email"]
        except KeyError:
            return None

    def get_provider(self):
        return self.data["provider"]

    def get_manageable(self) -> bool:
        return self.data["manageable"]

    def get_roles(self):
        return self.data["roles"]

    def get_organization(self):
        data = self.data["organization"]
        data["admin_role"] = data["adminRole"]
        del data["adminRole"]
        data["anonymous_role"] = data["anonymousRole"]
        del data["anonymousRole"]
        return Organization(**self.data["organization"])


class UsersApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None, internal_api=True, **kwargs):
        """
        :param user:
        :param password:
        :param server_url:
        :param internal_api: if set to false, also external users will be displayed
        """
        super().__init__(user, password, server_url)
        if internal_api:
            self.base_url = self.server_url + "/user-utils"
        else:
            self.base_url = self.server_url + "/users"

    def get_users(
        self, method="GET", limit=100, offset=0, query="", **kwargs
    ) -> List[User]:
        """
        :param method:
        :param limit:
        :param offset:
        :param query:
        :param kwargs:
        :return: List[Series]
        """
        parameters = {"limit": limit, "offset": offset, "query": query}

        results = []
        print(self.base_url + "/users.json")
        res = requests.request(
            method,
            self.base_url + "/users.json",
            auth=HTTPBasicAuth(self.user, self.password),
            params=parameters,
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            for u in res.json()["users"]["user"]:
                results.append(
                    User(
                        self.user,
                        self.password,
                        self.base_url + "/" + u["username"] + ".json",
                        u,
                    )
                )
        else:
            raise OcPyRequestException(res.content.decode("utf-8"), res.status_code)
        return results

    def get_user_by_name(self, user_name, **kwargs) -> User:
        res = requests.get(
            self.base_url + "/" + user_name + ".json",
            auth=HTTPBasicAuth(self.user, self.password),
            **kwargs
        )
        if res.ok:
            user = res.json()
            return User(
                self.user, self.password, self.base_url + "/" + user["identifier"], user
            )
        raise Exception("could not get event!")

    def create_user(
        self,
        user_name: str,
        password: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        roles: Optional[List[str]] = None,
        **kwargs
    ):
        if "user-utils" not in self.base_url:
            raise NotImplementedError("can't create user when using external API.")

        res = requests.delete(
            self.base_url + "/" + user_name + ".json",
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )

    def delete_user(self, user_name: str, **kwargs):
        if "user-utils" not in self.base_url:
            raise NotImplementedError("can't delete user when using external API.")

        res = requests.delete(
            self.base_url + "/" + user_name + ".json",
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
        )
        if res.ok:
            return "OK"

    def update_user(self, user_name: str):
        if "user-utils" not in self.base_url:
            raise NotImplementedError("can't update user when using external API.")


def main():
    api = UsersApi(internal_api=True)
    # api.create_user()
    users = api.get_users()
    # print(users)

    for u in users:
        print(u.get_name())
        print(u.get_username())
        # print(u.get_roles())
        print(u.get_manageable())


if __name__ == "__main__":
    main()
