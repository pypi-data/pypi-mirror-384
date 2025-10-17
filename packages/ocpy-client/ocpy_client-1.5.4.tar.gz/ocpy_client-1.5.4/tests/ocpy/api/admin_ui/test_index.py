"""Test for the index API"""

import unittest
import pytest

from ocpy.api.external.index import IndexApi


@pytest.mark.usefixtures("setup_oc_connection")
# @pytest.mark.skip(reason="deprecated API")
class TestIndexClass(unittest.TestCase):
    """Test the index API."""

    def test_get_services(self):
        """Test recreating index services."""
        ix_api = IndexApi()
        out = ix_api.recreate_index()
        self.assertEqual(out, "ok")
