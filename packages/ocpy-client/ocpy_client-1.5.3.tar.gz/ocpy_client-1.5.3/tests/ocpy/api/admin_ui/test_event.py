"""Tests for Admin EventAPI"""

from pprint import pformat
import unittest
import pytest

from loguru import logger
from ocpy.api.admin_ui.event import EventApi


@pytest.mark.usefixtures("setup_oc_connection")
class TestEventsClass(unittest.TestCase):
    """Test class for Admin EventAPI"""

    def test_get_services(self):
        """Test get services call"""
        admin_ev_api = EventApi()
        meta = admin_ev_api.get_new_metadata()
        self.assertIsNotNone(meta)
        self.assertIsInstance(meta, list)

    def test_get_assets(self):
        """Test get assets"""
        admin_ev_api = EventApi()
        assets = admin_ev_api.get_assets("7ea01428-7be2-4a4f-b961-43a225f20dfd")
        logger.info(pformat(assets))
        self.assertIsNotNone(assets)
        self.assertIsInstance(assets, dict)

    def test_get_attachments(self):
        """Test get attachments"""
        admin_ev_api = EventApi()
        attachments = admin_ev_api.get_attachments(
            "7ea01428-7be2-4a4f-b961-43a225f20dfd"
        )
        logger.info(pformat(attachments))
        self.assertIsNotNone(attachments)
        self.assertIsInstance(attachments, list)

    def test_get_mime_type(self):
        """Test get mime type"""
        admin_ev_api = EventApi()
        mime = admin_ev_api.get_mime_type("tests/data/test.vtt")
        logger.info(mime)

    def test_post_attachment(self):
        """Test post attachment"""
        admin_ev_api = EventApi()
        wf_id = admin_ev_api.post_attachment(
            "8209008d-c6e1-4ff6-96e2-98228b2a2e1c",
            "track_subtitles_option_de",
            "tests/data/test.vtt",
        )
        logger.info(pformat(wf_id))
        self.assertIsNotNone(wf_id)

    def test_post_subtitiles(self):
        """Test post subtitiles"""
        admin_ev_api = EventApi()
        wf_id = admin_ev_api.post_subtitles(
            "8c421523-e769-40df-839d-a778b5b7f4bc", "tests/data/test2.vtt"
        )
        logger.info(pformat(wf_id))
        self.assertIsNotNone(wf_id)
