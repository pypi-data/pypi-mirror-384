import requests
from pprint import pprint
from requests.auth import HTTPBasicAuth

from ocpy import OcPyRequestException
from ocpy.api.api_client import OpenCastBaseApiClient


class OrgApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None, **_kwargs):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/org"

    def get_all_orgs(self, **kwargs):
        res = requests.get(
            self.base_url + "/all.json",
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.json()
        raise OcPyRequestException("could not get event!", response=res)

    def get_org(self, id: str, **kwargs):
        res = requests.get(
            self.base_url + "/{}.json".format(id),
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.json()
        raise OcPyRequestException("could not get event!", response=res)


def main():
    api = OrgApi()
    pprint(api.get_all_orgs())
    pprint(api.get_org("mh_default_org"))


if __name__ == "__main__":
    main()
