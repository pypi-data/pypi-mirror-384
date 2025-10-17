import os

import requests
from loguru import logger
from requests.auth import HTTPBasicAuth
from typing import List, Optional, Union
import json
from pprint import pprint

from ocpy.api.api_client import OpenCastBaseApiClient
from ocpy import OcPyRequestException
from ocpy.model.event_models import Publication
from ocpy.model.acl import ACL, Action


class WorkflowInstance:
    def __init__(self, user, password, url, data):
        self.base_url = url
        self.user = user
        self.password = password
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4,
                          separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_creator(self):
        return self.data["creator"]

    def get_description(self):
        return self.data["description"]

    def get_event_identifier(self):
        return self.data["event_identifier"]

    def get_identifier(self):
        return self.data["identifier"]

    def get_state(self):
        return self.data["state"]

    def get_title(self):
        return self.data["title"]

    def get_workflow_definition_identifier(self):
        return self.data["workflow_definition_identifier"]

    def get_configuration(self) -> Union[dict, None]:
        return self.data.get("configuration", None)

    def get_operations(self) -> Union[dict, None]:
        return self.data.get("operations", None)

    def delete(self, **kwargs):
        url = self.base_url
        res = requests.delete(url,
                              auth=HTTPBasicAuth(self.user, self.password),
                              timeout=kwargs.pop("timeout", 30),)
        if res.ok:
            return "ok"
        raise Exception(
            "Could not delete event (" + self.get_identifier() + ")! (" + res.text + ")"
        )


class WorkflowsApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None, **kwargs):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/api/workflows"

    def get_workflow_instances(
            self,
            method="GET",
            limit=100,
            offset=0,
            sign=True,
            with_acl=False,
            with_metadata=False,
            with_publications=False,
            events_filter=None,
            **kwargs
    ) -> List[WorkflowInstance]:
        """
        :param method:
        :param limit:
        :param offset:
        :param sign:
        :param with_acl:
        :param with_metadata:
        :param with_publications:
        :param events_filter:
        :param kwargs:
        :return: List[Event]
        """
        parameters = {
            "limit": limit,
            "offset": offset,
            "sign": sign,
            "withacl": with_acl,
            "withmetadata": with_metadata,
            "withpublications": with_publications,
        }
        if events_filter:
            if isinstance(events_filter, WorkflowsApi.Filter):
                parameters["filter"] = events_filter.get_filter_string()
            else:
                parameters["filter"] = events_filter
        results = []
        res = requests.request(
            method,
            self.base_url,
            auth=HTTPBasicAuth(self.user, self.password),
            params=parameters,
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            for wfi in res.json():
                pprint(wfi)
                results.append(
                    WorkflowInstance(
                        self.user,
                        self.password,
                        self.base_url + "/" + str(wfi["identifier"]),
                        wfi,
                    )
                )
        else:
            if res.status_code == 500:
                logger.warning(
                    "Opencast responded with an internal server error (500)."
                )
            else:
                logger.error(
                    "Request to Opencast resulted in an error (code: {}): {}".format(
                        res.status_code, res.content
                    )
                )
            raise OcPyRequestException(res.content.decode("utf-8"),
                                       response=res)
        return results

    def get_workflow_instance(
            self, wfi_id: int, with_operations=False, with_configuration=False,
            **kwargs
    ) -> WorkflowInstance:
        parameters = {
            "withoperations": with_operations,
            "withconfiguration": with_configuration,
        }
        res = requests.get(
            self.base_url + "/" + str(wfi_id),
            auth=HTTPBasicAuth(self.user, self.password),
            params=parameters,
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            wfi = res.json()
            return WorkflowInstance(
                self.user,
                self.password,
                self.base_url + "/" + str(wfi["identifier"]),
                wfi,
            )
        raise OcPyRequestException("could not get wfi!", response=res)

    def create_workflow_instance(
            self,
            event_identifier,
            workflow_definition_identifier,
            configuration=None,
            with_operations=False,
            with_configuration=False,
            **kwargs
    ) -> WorkflowInstance:

        if configuration is not None:
            if not isinstance(configuration, str):
                configuration = json.dumps(configuration)

        data = {
            "event_identifier": event_identifier,
            "workflow_definition_identifier": workflow_definition_identifier,
            "configuration": configuration,
            "with_operations": with_operations,
            "with_configuration": with_configuration,
        }

        res = requests.post(
            self.base_url + "/",
            auth=HTTPBasicAuth(self.user, self.password),
            data=data,
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            wfi = res.json()
            return WorkflowInstance(
                self.user,
                self.password,
                self.base_url + "/" + str(wfi["identifier"]),
                wfi,
            )
        raise OcPyRequestException(
            "could not create workflow instance! (" + res.text + ")",
            response=res
        )

    def delete_workflow_instance(self, wfi_id, **kwargs):
        res = requests.delete(
            self.base_url + "/" + str(wfi_id),
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return "ok"
        raise OcPyRequestException(
            "could not delete event! (" + res.text + ")")

    class Filter:
        def __init__(self):
            self.filter_string = None

        def update_filter_string(self, update_string):
            if self.filter_string is None:
                self.filter_string = update_string
            else:
                self.filter_string += "," + update_string

        def set_contributors_filter(self, contributors):
            self.update_filter_string("contributors:{}".format(contributors))
            return self

        def set_location_filter(self, location):
            self.update_filter_string("location:{}".format(location))
            return self

        def set_series_filter(self, series):
            self.update_filter_string("series:{}".format(series))
            return self

        def set_subject_filter(self, subject):
            self.update_filter_string("subject:{}".format(subject))
            return self

        def set_text_filter_filter(self, text_filter):
            self.update_filter_string("textFilter:{}".format(text_filter))
            return self

        def get_filter_string(self):
            return self.filter_string
