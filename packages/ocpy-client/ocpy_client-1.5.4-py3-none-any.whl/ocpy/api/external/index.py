# -*- coding: utf-8 -*-
"""Opencast admin_ui IndexApiAPI.

Base implementation of opencast admin_ui index API.
"""
import requests
from requests.auth import HTTPBasicAuth
from ocpy import OcPyException

from ocpy.api.api_client import OpenCastBaseApiClient


class IndexApi(OpenCastBaseApiClient):
    """API to manage the admin ui index.

    Basically for clearing and recreating the index.
    """

    def __init__(self, user: str = None, password: str = None, server_url: str = None):
        """Create new index API instance.

        Args:
            user (str): Opencast username
            password (str): Opencast password
            server_url (str): Base URL of Opencast Admin Node
        """
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/index"

    def clear_index(self, timeout=10, **kwargs):
        """Clear the index for the admin UI.

        This is useful if the UI returns
        events that don't exist anymore. There is another clearIndex function
        for the external API. Also the engage player uses another endpoint
        (the search endpoint) which can't be cleared, but single items can be
        deleted from search using the search
        endpoint's delete function.

        Returns:
            str: "ok" if everything went well
        Raises:
            Exception: if index could not be cleared; also in case of
            connection errors
        """
        url = self.base_url + "/clear"
        res = requests.post(
            url, timeout=timeout, auth=HTTPBasicAuth(self.user, self.password), **kwargs
        )
        if res.ok:
            return "ok"
        raise OcPyException(f"Could not get clear index! {res.text}")

    def recreate_index(self, service=None, timeout=10, **kwargs) -> str:
        """Recreate the index for the admin UI (or for a specific service).

        Allowed services are: Groups, Acl, Themes, Series, Scheduler,
        workflow, AssetManager and Comments. The service order (see above) is
        very important! Make sure, you do not run index rebuild for more than
        one service at a time! The service parameter can be omitted.

        This is useful if the UI returns events that don't exist anymore.
        There is another recreateIndex function for the external API. Also the
        engage player uses another endpoint (the search endpoint) which can't
        be recreated, but single items can be deleted from search using the
        search endpoint's delete function.

        Args:
            service (object):
        Returns:
            str: "ok" if everything went well
        Raises:
            Exception: if index could not be recreated; also in case of
            connection errors
        """
        url = self.base_url + "/rebuild"
        if service is not None:
            url += "/" + service
        res = requests.post(
            url, timeout=timeout, auth=HTTPBasicAuth(self.user, self.password), **kwargs
        )
        if res.ok:
            return "ok"
        raise OcPyException(f"Could not rebuild index! {res.text}")
