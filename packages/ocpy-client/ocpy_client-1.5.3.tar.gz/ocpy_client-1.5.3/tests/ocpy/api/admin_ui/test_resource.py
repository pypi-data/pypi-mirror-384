from pprint import pformat
from loguru import logger
import unittest
import pytest

from ocpy.api.admin_ui.resources import ResourcesApi


@pytest.mark.usefixtures("setup_oc_connection")
class TestResourceClass(unittest.TestCase):
    def test_get_services(self):
        admin_ev_api = ResourcesApi()
        event_upload_options = admin_ev_api.get_event_upload_options()
        logger.debug(pformat(event_upload_options))
        self.assertIsNotNone(event_upload_options)
        self.assertIsInstance(event_upload_options, dict)
