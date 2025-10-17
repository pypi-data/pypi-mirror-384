import logging
import unittest

import pytest

from ocpy.api.admin_ui.service import AdminServiceApi


@pytest.mark.usefixtures("setup_oc_connection")
class TestServiceClass(unittest.TestCase):
    def test_get_services(self):
        service_api = AdminServiceApi()
        self.assertIsNotNone(service_api.get_services())
        self.assertIsInstance(service_api.get_services(), dict)
