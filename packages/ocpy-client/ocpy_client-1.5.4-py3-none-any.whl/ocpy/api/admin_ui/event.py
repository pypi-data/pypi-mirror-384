# -*- coding: utf-8 -*-
"""Opencast admin_ui EventAPI.

Base implementation of opencast admin_ui event api.
Please refer to und use external event API functions.

"""
import json
import mimetypes
import os
from pprint import pformat
from typing import Dict, Optional
from loguru import logger
import requests
from requests.auth import HTTPBasicAuth

from ocpy import OcPyRequestException
from ocpy.api.admin_ui.resources import ResourcesApi
from ocpy.api.api_client import OpenCastBaseApiClient


class EventApi(OpenCastBaseApiClient):
    """admin_ui.EventAPI class."""

    def __init__(self, user=None, password=None, server_url=None, **_kwargs):
        """Create new event API instance.

        Args:
            user: Opencast username
            password: Opencast password
            server_url: Base URL of Opencast Admin Node
        """
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/admin-ng/event"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.user, self.password)

    def get_new_metadata(self, timeout=10, **kwargs) -> str:
        """Return metadata required to fill metadata.

        Return:
            str: metadata
        Raises:
             OcPyRequestException: if metadata could not be retrieved
        """
        url = self.base_url + "/new/metadata"
        res = requests.get(
            url, timeout=timeout, auth=HTTPBasicAuth(self.user, self.password), **kwargs
        )
        if res.ok:
            return res.json()
        raise OcPyRequestException("could not get metadata tags!", response=res)

    def get_assets(self, event_id: str, timeout=10):
        """Return assets of a given event.

        Params:
            event_id: id of the event
        Return:
            str: metadata
        Raises:
             OcPyRequestException: if metadata could not be retrieved
        """
        url = f"{self.base_url}/{event_id}/asset/assets.json"
        res = requests.get(
            url, timeout=timeout, auth=HTTPBasicAuth(self.user, self.password)
        )
        if res.ok:
            return res.json()
        raise OcPyRequestException("could not get assets!", response=res)

    def get_attachments(self, event_id: str, timeout=10):
        """Return attachments of a given event.

        Params:
            event_id: id of the event
        Return:
            str: metadata
        Raises:
             OcPyRequestException: if metadata could not be retrieved
        """
        url = f"{self.base_url}/{event_id}/asset/attachment/attachments.json"
        res = requests.get(
            url, timeout=timeout, auth=HTTPBasicAuth(self.user, self.password)
        )
        if res.ok:
            return res.json()
        raise OcPyRequestException("could not get attachments!", response=res)

    def _available_event_upload_options_to_list(
        self, available_event_upload_options: Dict[str, Dict[str, str]]
    ):
        workflow_id = None
        option_list = []
        for o in available_event_upload_options.keys():
            try:
                option_list.append(
                    # {**available_event_upload_options[o], "title": o}
                    {
                        **available_event_upload_options[o],
                        "title": o,
                        "showsAs": "uploadAsset",
                    }
                )
            except TypeError:
                logger.debug(o)
                workflow_id = available_event_upload_options[o]

        return option_list, workflow_id

    def get_mime_type(self, file):
        """Return mime type of a given file (by guessing)."""
        mime_type = mimetypes.guess_type(file)[0]
        if not mime_type:
            mime_type = "application/octet-stream"
        return mime_type

    def post_attachment(
        self,
        event_id,
        attachment_name,
        file,
        publish_uploaded_assets_wf=None,
        available_event_upload_options: Optional[Dict] = None,
    ):
        """Adds an attachment to an event.
        If there is already an attachment with the same name, it will be overwritten.

        Args:
            event_id (string): The ID (UUID) of the event to which the attachment should be added.
            attachment_name (string): Name of the attachment (as configured in Opencast).
            file (string): Path to the file to be uploaded.
            publish_uploaded_assets_wf (string, optional):
                Name of the workflow to run after attachment was added. Defaults to None.
            available_event_upload_options (Optional[Dict], optional):
                Dict of available asset upload options. Defaults to None.

        Raises:
            OcPyRequestException: If file does not exist
            OcPyRequestException: If attachment_name does not exist / is not configured
            OcPyRequestException: If request failed

        Returns:
            string: Workflow ID
        """
        url = f"{self.base_url}/{event_id}/assets"

        if not os.path.isfile(file):
            raise OcPyRequestException(f"File {file} does not exist!")

        workflow_id = None
        if not available_event_upload_options:
            r_api = ResourcesApi()
            (
                available_event_upload_options,
                workflow_id,
            ) = self._available_event_upload_options_to_list(
                r_api.get_event_upload_options()
            )

        if publish_uploaded_assets_wf is None:
            if workflow_id:
                publish_uploaded_assets_wf = workflow_id
            else:
                publish_uploaded_assets_wf = "publish-uploaded-assets"

        try:
            event_upload_option = [
                available_event_upload_option
                for available_event_upload_option in available_event_upload_options
                if available_event_upload_option["id"] == attachment_name
            ].pop()
        except IndexError:
            event_upload_option = None
        if not event_upload_option:
            raise OcPyRequestException(
                f"Attachment {attachment_name} does not exist / is not configured!"
            )

        data = {
            "assets": {"options": available_event_upload_options},
            "processing": {
                "workflow": publish_uploaded_assets_wf,
                "configuration": {
                    "downloadSourceflavorsExist": "true",
                    "download-source-flavors": f"{event_upload_option['flavorType']}/{event_upload_option['flavorSubType']}",  # pylint: disable=line-too-long
                },
            },
        }
        logger.debug(pformat(data))

        with open(os.path.expanduser(file), "rb") as f:
            file_name = os.path.basename(file)
            mime_type = self.get_mime_type(file)
            files = {
                f"{attachment_name}.0": (file_name, f, mime_type)
            }  # a mime type (content type) is required!
            data = json.dumps(data)
            request = self.session.prepare_request(
                requests.Request(
                    method="POST", url=url, data={"metadata": data}, files=files
                )
            )
            # pretty_print_POST(request)
            res = self.session.send(request)
            if res.ok:
                logger.debug(f"{res.status_code}, {res.text}")
                return res.text
            logger.error(f"{res.status_code}, {res.text}")
            raise OcPyRequestException("could not post attachment!", response=res)

    def post_subtitles(
        self, event_id, file, language_code="de", publish_uploaded_assets_wf=None
    ):
        """Adds subtitles attachment to an event.
        If there is already a subtitles attachment for the language, it will be overwritten.

        Args:
            event_id (string): ID of the event to which the attachment should be added.
            file (string): Path to the file to be uploaded.
            language_code (str, optional): Language code of the subtitles. Defaults to "de".
            publish_uploaded_assets_wf (string, optional):
                Name of the workflow to run after attachment was added. Defaults to None.

        Raises:
            OcPyRequestException: Upload option for subtitles not found

        Returns:
            string: WF ID
        """
        r_api = ResourcesApi()
        (
            available_event_upload_options,
            workflow_id,
        ) = self._available_event_upload_options_to_list(
            r_api.get_event_upload_options()
        )
        # following line for OC < 15
        possible_upload_options = [
            option
            for option in available_event_upload_options
            if ("captions" in option["id"] or "track_subtitles_option" in option["id"])
            and (
                f"+{language_code}" in option["flavorSubType"]
                or f"lang:{language_code}" in option["tags"]
            )
        ]
        if len(possible_upload_options) == 0:
            logger.error(
                f"Only found these upload options: {pformat(available_event_upload_options)}"
            )
            raise OcPyRequestException("No upload option for subtitles found!")

        possible_upload_option = possible_upload_options[
            0
        ]  # pick the first (and hopefully only) option
        if not publish_uploaded_assets_wf:
            publish_uploaded_assets_wf = workflow_id
        return self.post_attachment(
            event_id, possible_upload_option["id"], file, publish_uploaded_assets_wf
        )
