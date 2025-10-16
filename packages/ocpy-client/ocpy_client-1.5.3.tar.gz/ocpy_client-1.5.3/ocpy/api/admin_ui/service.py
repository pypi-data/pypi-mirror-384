# -*- coding: utf-8 -*-
"""Opencast admin_ui ServiceAPI.

Base implementation of opencast admin_ui event api.
Please refer to und use external event API functions.
"""
import requests
from requests.auth import HTTPBasicAuth
import json
from pprint import pprint

from typing import List

from ocpy.api.api_client import OpenCastBaseApiClient


class Service:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_completed(self) -> int:
        return self.data["completed"]

    def get_hostname(self) -> str:
        """

        Returns:

        """
        return self.data["hostname"]

    def get_mean_queue_time(self) -> int:
        """

        Returns:

        """
        return self.data["meanQueueTime"]

    def get_mean_run_time(self) -> int:
        return self.data["meanRunTime"]

    def get_queued(self) -> int:
        return self.data["queued"]

    def get_running(self) -> int:
        return self.data["running"]

    def get_name(self) -> str:
        return self.data["name"]

    def get_status(self) -> str:
        return self.data["status"]


class Services:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_count(self) -> int:
        return self.data["count"]

    def get_limit(self) -> int:
        return self.data["limit"]

    def get_offset(self) -> int:
        return self.data["offset"]

    def get_total(self) -> int:
        return self.data["total"]

    def get_results(self) -> List[Service]:
        services = []
        for s in self.data["results"]:
            services.append(Service(s))
        return services


class AdminServiceApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/admin-ng/services"

    def get_services(self, **kwargs) -> dict:
        url = self.base_url + "/services.json"
        print(url)
        res = requests.get(url, auth=HTTPBasicAuth(self.user, self.password), **kwargs)
        print(res)
        if res.ok:
            return res.json()
        raise Exception("Could not get api version!")


def main():
    api = AdminServiceApi()
    pprint(api.get_services())


if __name__ == "__main__":
    main()
