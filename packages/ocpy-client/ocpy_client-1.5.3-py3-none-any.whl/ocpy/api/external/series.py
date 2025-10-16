"""API Client for the (external) series endpoint of the Opencast API."""

from urllib.parse import urlparse
import json
from typing import Generator, List, Optional, Union
from datetime import datetime
import pendulum
import requests
from requests.auth import HTTPBasicAuth
from loguru import logger


from ocpy import OcPyRequestException
from ocpy.api.api_client import OpenCastBaseApiClient
from ocpy.model.acl import ACL, Action


class Series:
    """Class represnting a series in Opencast."""

    def __init__(self, user, password, url, data) -> None:
        self.base_url = url
        self.user = user
        self.password = password
        self.data = data

        self._augment_data()

    def __str__(self) -> str:
        return json.dumps(
            self.data,
            sort_keys=True,
            indent=4,
            separators=(",", ": "),
            default=str,
        )

    def __repr__(self) -> str:
        return self.__str__()

    def _augment_data(self) -> None:
        if "created" in self.data:
            self.data["created"] = pendulum.parse(self.data["created"])

    def get_acl(self, **kwargs) -> Optional[List[ACL]]:
        res = self.data.get("acl", None)
        if res is None:
            url = self.base_url + "/acl"
            res = requests.get(
                url,
                timeout=kwargs.pop("timeout", 30),
                auth=HTTPBasicAuth(self.user, self.password),
            )
            if not res.ok:
                return None
            res = res.json()
            self.data["acl"] = res
        acls = []
        for a in res:
            acls.append(ACL(a["allow"], a["role"], Action(a["action"])))
        return acls

    def get_metadata(self, raw=False, **kwargs):
        url = self.base_url + "/metadata"
        res = requests.get(
            url,
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
        )
        if res.ok:
            if raw:
                return res.json()
            meta_result = dict()
            for r in res.json():
                # merge metadata
                meta_result = {
                    **meta_result,
                    **{m["id"]: m["value"] for m in r["fields"] if "value" in m},
                }
            return meta_result
        return None

    def set_acl(self, acl_list, override=False, **kwargs):
        url = self.base_url + "/acl"
        if isinstance(acl_list, List):
            acls = []
            for a in acl_list:
                if isinstance(a, ACL):
                    acls.append(a.get_acl_dict())
                else:
                    acls.append(a)
            acl_list = acls
        if isinstance(acl_list, ACL):
            acl_list = [acl_list.get_acl_dict()]

        data = {
            "acl": json.dumps(acl_list),
            "override": "true" if override else "false",
            # "override": True if override else False,
        }
        logger.debug(f"set acl data: {data}")
        res = requests.put(
            url,
            timeout=kwargs.pop("timeout", 30),
            data=data,
            auth=HTTPBasicAuth(self.user, self.password),
        )
        if res.ok:
            return res.json()
        raise OcPyRequestException(
            "could not set ACL! ("
            + res.text
            + " ["
            + str(res.status_code)
            + "])"
            + "acl: "
            + json.dumps(acl_list)
        )

    def add_to_acl(self, acl: Union[ACL, List[ACL]], override=False):
        logger.debug(f"adding to acl: {acl}")
        actual_acl = self.get_acl()
        if not isinstance(acl, List):
            acl = [acl]
        for n_a in acl:
            found = False
            for a_a in actual_acl:
                if a_a == n_a:
                    found = True
                    break
            if not found:
                actual_acl.append(n_a)

        return self.set_acl(actual_acl, override=override)

    def remove_from_acl(self, acl: ACL):
        actual_acl = self.get_acl()

        if not isinstance(acl, List):
            acl = [acl]
        for aa in actual_acl:
            for na in acl:
                if aa == na:
                    actual_acl.remove(na)
        return self.set_acl(actual_acl)

    def get_properties(self, **kwargs):
        url = self.base_url + "/properties"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
        )
        if res.ok:
            return res.json()
        return None

    def get_contributors(self):
        return self.data["contributors"]

    def get_created(self):
        return self.data["created"]

    def get_creator(self):
        return self.data["creator"]

    def get_identifier(self):
        return self.data["identifier"]

    def get_organizers(self):
        return self.data["organizers"]

    def get_publishers(self):
        return self.data["publishers"]

    def get_subjects(self):
        return self.data["subjects"]

    def get_title(self):
        return self.data["title"]

    def get_events(self, limit=100, **kwargs):
        from ocpy.api import EventsApi  # pylint: disable=import-outside-toplevel

        parsed_url = urlparse(self.base_url)
        url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        ev_api = EventsApi(self.user, self.password, url)
        return ev_api.get_events_part_of(self, limit, **kwargs)

    def delete(self):
        res = requests.delete(
            self.base_url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=30,
        )
        if res.ok:
            return "ok"
        raise OcPyRequestException("could not delete series!", response=res)


class SeriesApi(OpenCastBaseApiClient):
    """API Client for the (external) series endpoint of the Opencast API."""

    def __init__(self, user=None, password=None, server_url=None, **_kwargs):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/api/series"

    def get_series(
        self,
        limit=100,
        offset=0,
        with_acl=False,
        series_filter=None,
        only_with_write_access=False,
        **kwargs,
    ) -> List[Series]:
        """
        :param limit:
        :param offset:
        :param with_acl:
        :param series_filter:
        :param onlyWithWriteAccess:
        :param kwargs:
        :return: List[Series]
        """
        url = self.base_url.rstrip("/") + "/"
        logger.trace(f"getting series url: {url}")
        parameters = {
            "limit": limit,
            "offset": offset,
            "sort": "",
            "filter": "",
            "withacl": str(with_acl).lower(),
            "onlyWithWriteAccess": str(only_with_write_access).lower(),
        }
        parameters = {k: v for k, v in parameters.items() if v != ""}

        logger.trace(f"getting series parameters: {parameters}")
        if series_filter:
            if isinstance(series_filter, SeriesApi.Filter):
                parameters["filter"] = series_filter.get_filter_string()
            else:
                parameters["filter"] = series_filter
        results = []
        req = requests.Request(
            method="GET",
            url=url,
            auth=HTTPBasicAuth(self.user, self.password),
            params=parameters,
            **kwargs,
        )
        prepared = req.prepare()
        logger.trace(f"getting series prepared url: {prepared.url}")
        res = requests.Session().send(
            prepared,
            timeout=kwargs.pop("timeout", 30),
        )
        if res.ok:
            for e in res.json():
                results.append(
                    Series(
                        self.user,
                        self.password,
                        url + e["identifier"],
                        e,
                    )
                )
            return results
        raise OcPyRequestException("could not get series!", response=res)

    def get_all_series(
        self,
        with_acl=False,
        only_with_write_access=False,
        series_filter=None,
        batch_size=100,
        print_progress=False,
        generator=False,
    ) -> Union[List[Series], Generator[Series, None, None]]:
        series_generator = self.get_all_series_generator(
            with_acl=with_acl,
            only_with_write_access=only_with_write_access,
            series_filter=series_filter,
            batch_size=batch_size,
            print_progress=print_progress,
        )
        if generator:
            return series_generator
        return list(series_generator)

    def get_all_series_generator(
        self,
        with_acl=False,
        only_with_write_access=False,
        series_filter=None,
        batch_size=100,
        print_progress=False,
    ) -> Generator[Series, None, None]:
        count = 0
        while True:
            if print_progress:
                logger.info(f"requesting {batch_size} starting from offset {count}")
            res = self.get_series(
                with_acl=with_acl,
                only_with_write_access=only_with_write_access,
                series_filter=series_filter,
                limit=batch_size,
                offset=count,
            )

            if res is None or len(res) <= 0:
                logger.debug("DONE; got no more series")
                break
            count += len(res)
            for r in res:
                yield r
        return

    def get_series_acl(self, series_id, **kwargs) -> List[ACL]:
        res = requests.get(
            self.base_url + f"/{series_id}/acl",
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )
        acls = []
        if res.ok:
            for a in res.json():
                acls.append(ACL(a["allow"], a["role"], Action(a["action"])))
            return acls
        raise OcPyRequestException("could not get series acls!", response=res)

    def get_series_by_id(
        self,
        series_id,
        with_acl=False,
        **kwargs,
    ) -> Series:
        parameters = {"withacl": with_acl}
        res = requests.get(
            self.base_url + "/" + series_id,
            auth=HTTPBasicAuth(self.user, self.password),
            params=parameters,
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )
        if res.ok:
            series = res.json()
            return Series(
                self.user,
                self.password,
                self.base_url + "/" + series["identifier"],
                series,
            )
        logger.error(f"{res.status_code}: {res.text}")
        raise OcPyRequestException("could not get series!", response=res)

    def create_series(self, acl, metadata, theme=None, **kwargs) -> Series:
        if isinstance(acl, List):
            acls = []
            for a in acl:
                if isinstance(a, ACL):
                    acls.append(a.get_acl_dict())
                else:
                    acls.append(a)
            acl = acls
        if isinstance(acl, ACL):
            acl = acl.get_acl_dict()
        data = {
            "acl": json.dumps(acl),
            "metadata": json.dumps(metadata),
            "theme": theme,
        }

        res = requests.post(
            self.base_url + "/",
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
            data=data,
            **kwargs,
        )
        if res.ok:
            series = res.json()
            return Series(
                self.user,
                self.password,
                self.base_url + "/" + series["identifier"],
                series,
            )
        raise OcPyRequestException(
            "could not create event! (" + res.text + ")", response=res
        )

    class Filter:
        """Filter class for series."""

        def __init__(self):
            self.filter_string = None

        def update_filter_string(self, update_string):
            if self.filter_string is None:
                self.filter_string = update_string
            else:
                self.filter_string += "," + update_string

        def set_contributors_filter(self, contributors):
            self.update_filter_string(f"contributors:{contributors}")
            return self

        def set_creator_filter(self, creator):
            self.update_filter_string(f"creator:{creator}")
            return self

        def set_creation_date_filter(self, date1: datetime, date2):
            d1 = str(date1).replace("+00:00", "Z")
            d2 = str(date2).replace("+00:00", "Z")
            self.update_filter_string(f"creationDate:{d1}/{d2}")
            return self

        def set_language_filter(self, language):
            self.update_filter_string(f"language:{language}")
            return self

        def set_license_filter(self, oc_license):
            self.update_filter_string(f"license:{oc_license}")
            return self

        def set_organizers_filter(self, organizers):
            self.update_filter_string(f"organizers:{organizers}")
            return self

        def set_managed_acl_filter(self, managed_acl):
            self.update_filter_string(f"managedAcl:{managed_acl}")
            return self

        def set_subject_filter(self, subject):
            self.update_filter_string(f"subject:{subject}")
            return self

        def set_text_filter_filter(self, text_filter):
            self.update_filter_string(f"textFilter:{text_filter}")
            return self

        def set_title_filter(self, title):
            self.update_filter_string(f"title:{title}")
            return self

        def get_filter_string(self):
            return self.filter_string
