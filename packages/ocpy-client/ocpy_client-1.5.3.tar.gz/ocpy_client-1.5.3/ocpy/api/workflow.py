#!/usr/bin/env python3
from typing import Optional

from loguru import logger
from requests import Session
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from pprint import pprint

from ocpy.api.api_client import OpenCastDigestBaseApiClient, OpenCastBaseApiClient, OpenCastApiService


class WorkflowApi(OpenCastApiService, OpenCastBaseApiClient,
                  OpenCastDigestBaseApiClient):
    def __init__(self,
                 service_url,
                 user=None,
                 password=None,
                 digest_user=None,
                 digest_password=None,
                 use_digest_auth=False,
                 **_kwargs):
        OpenCastApiService.__init__(self, service_url)
        OpenCastBaseApiClient.__init__(self, user, password)
        OpenCastDigestBaseApiClient.__init__(self, digest_user,
                                             digest_password, optional=True)

        self.use_digest_auth = self.use_digest_auth

        self.session = Session()
        if self.use_digest_auth:
            self.session.auth = HTTPDigestAuth(self.digest_user,
                                               self.digest_password)
            self.session.headers.update({"X-Requested-Auth": "Digest"})
        else:
            self.session.auth = HTTPBasicAuth(self.user, self.password)

    def get_count(self, **kwargs) -> int:
        url = self.base_url + "/count"
        res = self.session.get(
            url,
            **kwargs
        )
        if res.ok:
            return int(res.text)

        raise Exception("Could not get workflow count!")

    def get_definitions(self, as_json=True):
        if as_json:
            url = self.base_url + "/definitions.json"
        else:
            url = self.base_url + "/definitions.xml"
        res = self.session.get(url)
        if res.ok:
            if as_json:
                return res.json()
            else:
                return res.content.decode("utf-8")
        raise Exception("Could not get workflow definitions!")

    def get_handlers(self):
        url = self.base_url + "/handlers.json"
        res = self.session.get(url)
        if res.ok:
            return res.json()
        raise Exception("Could not get workflow definitions!")

    def get_statistics(self, as_json=True):
        if as_json:
            url = self.base_url + "/statistics.json"
        else:
            url = self.base_url + "/statistics.xml"
        res = self.session.get(url)
        if res.ok:
            if as_json:
                return res.json()
            else:
                return res.content.decode("utf-8")
        raise Exception("Could not get workflow definitions!")

    def get_instances(self, as_json=True):
        if as_json:
            url = self.base_url + "/instances.json"
        else:
            url = self.base_url + "/instances.xml"
        res = self.session.get(url)
        if res.ok:
            if as_json:
                return res.json()
            else:
                return res.content.decode("utf-8")
        raise Exception("Could not get workflow definitions!")

    def get_instance(self, id: str, as_json=True):
        if as_json:
            url = self.base_url + "/instances.json"
        else:
            url = self.base_url + "/instances.xml"
        res = self.session.get(url)
        if res.ok:
            if as_json:
                return res.json()
            else:
                return res.content.decode("utf-8")
        raise Exception("Could not get workflow definitions!")


def main():
    from ocpy.api.service import ServiceApi, ServiceType

    s_api = ServiceApi(server_url="http://opencast-dev.bibliothek.kit.edu:8080")
    s_api = ServiceApi(
        server_url="http://localhost:8080", user="admin", password="opencast"
    )
    # s_api = ServiceApi()
    wf_service = s_api.get_available(ServiceType.workflow)[0]

    print(wf_service)
    print(type(wf_service))
    api = WorkflowApi(wf_service)
    print(api)
    print(api.get_count())
    # print(api.get_definitions(as_json=False))
    # pprint(api.get_definitions())
    # pprint(api.get_handlers())
    pprint(api.get_instances())


if __name__ == "__main__":
    main()
