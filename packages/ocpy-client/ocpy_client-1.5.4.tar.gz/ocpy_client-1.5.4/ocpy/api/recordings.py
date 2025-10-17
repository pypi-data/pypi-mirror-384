"POST: https://oc9-dev-admin.bibliothek.kit.edu/admin-ng/event/new"
import json
from datetime import datetime
from types import NoneType

from loguru import logger
from typing import Union, Optional, List, Dict

import pendulum
import requests
from pendulum import DateTime
from requests.auth import HTTPBasicAuth

from ocpy import OcPyRequestException
from ocpy.api.api_client import OpenCastBaseApiClient
from ocpy.model.mediapackage import MediaPackage

"""
{
"metadata":[
    {
        "flavor":"dublincore/episode","title":"EVENTS.EVENTS.DETAILS.CATALOG.EPISODE",
        "fields":[{"id":"title","type":"text","value":"lala","tabindex":1,"$$hashKey":"object:544"},{"id":"subject","type":"text","value":"","tabindex":2,"$$hashKey":"object:545"},{"id":"description","type":"text_long","value":"","tabindex":3,"$$hashKey":"object:546"},{"translatable":true,"id":"language","type":"text","value":"","tabindex":4,"$$hashKey":"object:547"},{"id":"rightsHolder","type":"text","value":"","tabindex":5,"$$hashKey":"object:548"},{"translatable":true,"id":"license","type":"ordered_text","value":"","tabindex":6,"$$hashKey":"object:549"},{"translatable":false,"id":"isPartOf","type":"text","value":"","tabindex":7,"$$hashKey":"object:550"},{"translatable":false,"id":"creator","type":"mixed_text","value":[],"tabindex":8,"$$hashKey":"object:551"},{"translatable":false,"id":"contributor","type":"mixed_text","value":[],"tabindex":9,"$$hashKey":"object:552"},{"id":"publisher","type":"text","value":"Administrator","tabindex":10,"$$hashKey":"object:553"}]
    },
    {
        "fields":[{"translatable":true,"id":"content_type","type":"text","value":"","tabindex":1,"$$hashKey":"object:703"},{"id":"doi","type":"text","value":"","tabindex":2,"$$hashKey":"object:704"},{"id":"date","type":"date","value":"","tabindex":3,"$$hashKey":"object:705"},{"id":"institution","type":"text","value":"","tabindex":4,"$$hashKey":"object:706"},{"id":"keywords","type":"mixed_text","value":[],"tabindex":5,"$$hashKey":"object:707"},{"translatable":false,"id":"subject_classification","type":"text","value":"","tabindex":6,"$$hashKey":"object:708"}],
        "flavor":"kit/episode","title":"EVENTS.EVENTS.DETAILS.CATALOG.EPISODE"
    }
],
"processing":{"workflow":"fast","configuration":{"publish":"true"}},
"access":{"acl":{"ace":[{"action":"read","allow":true,"role":"ROLE_USER_ADMIN"},{"action":"write","allow":true,"role":"ROLE_USER_ADMIN"}]}},
"source":{
    "type":"SCHEDULE_MULTIPLE",
    "metadata":
    {
        "start":"2022-06-21T11:00:00Z",
        "device":"Test-SMP_KIT",
        "inputs":"defaults",
        "duration":"3300000",
        "end":"2022-06-21T11:55:00Z",
        "rrule":"FREQ=WEEKLY;BYDAY=TU,FR;BYHOUR=11;BYMINUTE=0"
    }
},
"assets":{"workflow":"publish-uploaded-assets","options":[{"id":"track_presenter","type":"track","flavorType":"presenter","flavorSubType":"source","multiple":false,"displayOrder":13,"accept":".avi,.flv,.m4v,.mkv,.mov,.mp4,.mpeg,.mpg,.ogv,.webm,.wmv,.flac,.m4a,.mp3,.ogg,.wav,.wma","title":"EVENTS.EVENTS.NEW.SOURCE.UPLOAD.NON_SEGMENTABLE"},{"id":"track_audio","type":"track","flavorType":"presenter-audio","flavorSubType":"source","multiple":false,"displayOrder":12,"accept":".flac,.m4a,.mp3,.ogg,.wav,.wma","title":"EVENTS.EVENTS.NEW.SOURCE.UPLOAD.AUDIO_ONLY"},{"id":"track_presentation","type":"track","flavorType":"presentation","flavorSubType":"source","multiple":false,"displayOrder":14,"accept":".avi,.flv,.m4v,.mkv,.mov,.mp4,.mpeg,.mpg,.ogv,.webm,.wmv,.flac,.m4a,.mp3,.ogg,.wav,.wma","title":"EVENTS.EVENTS.NEW.SOURCE.UPLOAD.SEGMENTABLE"},{"id":"attachment_captions_webvtt","type":"attachment","flavorType":"text","flavorSubType":"vtt","displayOrder":3,"accept":".vtt","title":"EVENTS.EVENTS.NEW.UPLOAD_ASSET.OPTION.CAPTIONS_WEBVTT"}]}}
"""


class RecordingsApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None, **kwargs):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/recordings"

    def get_event_count(self):
        url = self.base_url + "/eventCount"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
        )
        if res.ok:
            return res.text
        raise OcPyRequestException(res.content.decode("utf-8"),
                                   response=res)

    def get_upcoming_recording(self, agent_id: str):
        url = self.base_url + f"/capture/{agent_id}/upcoming"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
        )
        if res.ok:
            return res.json()
        raise OcPyRequestException(res.content.decode("utf-8"), response=res)

    @staticmethod
    def _build_default_agent_parameters_dict(agent_parameters: Optional[Dict[str, str]] = None,
                                             workflow_id: str = "fast",
                                             capture_device_names: str = "defaults"):
        if agent_parameters is None:
            agent_parameters = {}

        if "capture.device.names" not in agent_parameters and capture_device_names is not None:
            agent_parameters["capture.device.names"] = capture_device_names

        if "org.opencastproject.workflow.definition" not in agent_parameters and workflow_id is not None:
            agent_parameters["org.opencastproject.workflow.definition"] = workflow_id

        return agent_parameters

    @staticmethod
    def _build_properties_string(properties_dict_or_list: Union[Dict, List]) -> str:
        logger.debug(properties_dict_or_list)
        if isinstance(properties_dict_or_list, dict):
            properties_dict_or_list = [f"{k}={properties_dict_or_list[k]}" for k in properties_dict_or_list.keys()]
        if isinstance(properties_dict_or_list, list):
            properties_dict_or_list = "\n".join(properties_dict_or_list)
        if not isinstance(properties_dict_or_list, (str, NoneType)):
            logger.warning(f"properties_dict_or_list is not a string; neither string, nor dict nor list was provided! "
                           f"({type(properties_dict_or_list)})")

        return properties_dict_or_list

    def create_recording(self, agent_id: str, start: Union[str, DateTime], end: Union[str, DateTime],
                         media_package: str, source: Optional[str] = None, users: Optional[str] = None,
                         wf_properties: Optional[Dict[str, str]] = None,
                         agent_parameters: Optional[Dict[str, str]] = None,
                         workflow_id: str = "fast", capture_device_names: str = "defaults"):

        if isinstance(start, str):
            start = pendulum.parse(start)
        if isinstance(end, str):
            end = pendulum.parse(end)

        agent_parameters = RecordingsApi._build_default_agent_parameters_dict(agent_parameters,
                                                                              workflow_id=workflow_id,
                                                                              capture_device_names=capture_device_names)

        data = {
            "start": int(start.timestamp() * 1000),
            "end": int(end.timestamp() * 1000),
            "agent": agent_id,
            "mediaPackage": media_package,
            "users": users,
            "wfproperties": RecordingsApi._build_properties_string(wf_properties),
            "agentparameters": RecordingsApi._build_properties_string(agent_parameters),
            "source": source,
        }

        logger.info(data)

        res = requests.post(
            self.base_url + "/",
            auth=HTTPBasicAuth(self.user, self.password),
            data=data,
        )
        if res.ok:
            print(res)
            rec = res.text
            return rec
        raise OcPyRequestException(res.content.decode("utf-8"), response=res)

    def create_recurring_recording(self, agent_id: str, start: Union[str, DateTime], end: Union[str, DateTime],
                                   duration: int, rrule: str, template_mp: str, tz: str = "Europe/Berlin",
                                   source: Optional[str] = None,
                                   users: Optional[List[str]] = None,
                                   wf_properties: Optional[Dict[str, str]] = None,
                                   agent_parameters: Optional[Dict[str, str]] = None, workflow_id: str = "fast",
                                   capture_device_names: str = "defaults",
                                   **kwargs):

        if isinstance(start, str):
            start = pendulum.parse(start)
        if isinstance(end, str):
            end = pendulum.parse(end)

        agent_parameters = RecordingsApi._build_default_agent_parameters_dict(agent_parameters,
                                                                              workflow_id=workflow_id,
                                                                              capture_device_names=capture_device_names)
        data = {
            "rrule": rrule,
            "start": int(start.timestamp() * 1000),
            "end": int(end.timestamp() * 1000),
            "duration": duration,
            "tz": tz,
            "agent": agent_id,
            "templateMp": template_mp,
            "users": users,
            "wfproperties": RecordingsApi._build_properties_string(wf_properties),
            "agentparameters": RecordingsApi._build_properties_string(agent_parameters),
            "source": source,
        }

        res = requests.post(
            self.base_url + "/multiple",
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            data=data,
        )
        if res.ok:
            return "ok"
        raise OcPyRequestException(res.content.decode("utf-8"), response=res)


def main():
    api = RecordingsApi()
    print(api.get_event_count())


if __name__ == "__main__":
    main()
