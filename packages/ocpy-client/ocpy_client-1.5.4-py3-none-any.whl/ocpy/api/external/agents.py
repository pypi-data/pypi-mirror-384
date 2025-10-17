import requests
from requests.auth import HTTPBasicAuth
import json
from pprint import pprint

from typing import List

from ocpy.api.api_client import OpenCastBaseApiClient


class Agent:
    def __init__(self, user, password, url, data):
        self.base_url = url
        self.user = user
        self.password = password
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_agent_id(self) -> str:
        return self.data["agent_id"]

    def get_status(self) -> str:
        return self.data["status"]

    def get_inputs(self) -> List[str]:
        return self.data["inputs"]

    def get_update(self) -> str:
        return self.data["update"]

    def get_url(self) -> str:
        return self.data["url"]


class AgentsApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None, **_kwargs):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/api/agents/"

    def get_agents(self, limit=100, offset=0, **kwargs) -> List[Agent]:
        """
        :param limit:
        :param offset:
        :param kwargs:
        :return: List[Series]
        """
        parameters = {"limit": limit, "offset": offset}
        results = []
        res = requests.get(
            self.base_url,
            auth=HTTPBasicAuth(self.user, self.password),
            params=parameters,
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            for a in res.json():
                results.append(
                    Agent(self.user, self.password, self.base_url + a["agent_id"], a)
                )
        return results

    def get_all_agents(self) -> List[Agent]:
        result = []
        while True:
            res = self.get_agents(limit=100, offset=len(result))
            if res is None or len(res) <= 0:
                break
            result.extend(res)
        return result
