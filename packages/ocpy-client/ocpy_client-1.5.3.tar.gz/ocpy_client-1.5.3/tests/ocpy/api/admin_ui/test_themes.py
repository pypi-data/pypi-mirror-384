import logging
import unittest
import pytest

from ocpy import OcPyRequestException
from ocpy.api.admin_ui.themes import ThemesApi


@pytest.mark.usefixtures("setup_oc_connection")
class TestThemesClass(unittest.TestCase):
    def test_get_services(self):
        themes_api = ThemesApi()
        self.assertIsNotNone(themes_api.get_all_themes())

    def test_delete_theme(self):
        themes_api = ThemesApi()
        with self.assertRaises(OcPyRequestException) as context:
            themes_api.delete_theme(234345873459)  # non existing theme
        self.assertIn("could not delete theme", str(context.exception))
