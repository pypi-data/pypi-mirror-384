# -*- coding: utf-8 -*-
"""Opencast admin_ui Resource API.

Base implementation of opencast admin_ui resource api.
Please refer to und use external resource API functions.

"""

import json
import requests
from loguru import logger
from requests.auth import HTTPBasicAuth

from ocpy import OcPyRequestException
from ocpy.api.api_client import OpenCastBaseApiClient


class ResourcesApi(OpenCastBaseApiClient):
    """admin_ui.EventAPI class."""

    def __init__(self, user=None, password=None, server_url=None):
        """Create new event API instance.

        Args:
            user: Opencast username
            password: Opencast password
            server_url: Base URL of Opencast Admin Node
        """
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/admin-ng/resources"

    def get_event_upload_options(self, **kwargs) -> str:
        """Return metadata required to fill metadata.

        Return:
            str: metadata
        Raises:
             OcPyRequestException: if metadata could not be retrieved
        """
        url = self.base_url + "/eventUploadAssetOptions.json"
        res = requests.get(
            url, auth=HTTPBasicAuth(self.user, self.password), timeout=10, **kwargs
        )
        if res.ok:
            fixed_res = dict()
            for key, value in res.json().items():
                logger.debug(f"{key}: {value}")
                try:
                    fixed_res[key] = json.loads(value)
                except json.decoder.JSONDecodeError:
                    fixed_res[key] = value
            return fixed_res
        raise OcPyRequestException("could not get metadata tags!", response=res)
