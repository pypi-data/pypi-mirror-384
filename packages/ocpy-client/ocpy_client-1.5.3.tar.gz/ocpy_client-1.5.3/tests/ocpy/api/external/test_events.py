#  Copyright (c) 2019. Tobias Kurze
import logging
import os
import time
import types
import unittest
from typing import Union

import pytest

from ocpy import OcPyRequestException
from ocpy.api import get_events_api_client
from ocpy.api.external import events
from ocpy.api.external.events import Event, EventsApi
from ocpy.model.acl import ACL
import tests

_test_event: Union[None, Event] = None


@pytest.fixture(autouse=False, scope="class")
def create_test_event():
    global _test_event
    logging.info("XXX test_event fixture")
    test_meta = [
        {
            "fields": [
                {
                    "id": "title",
                    "label": "EVENTS.EVENTS.DETAILS.METADATA.TITLE",
                    "readOnly": False,
                    "required": True,
                    "type": "text",
                    "value": "Testevent",
                }
            ],
            "flavor": "dublincore/episode",
        }
    ]

    test_acl = ACL.get_read_write_acls("ROLE_TEST_USER")
    # test_acl = []

    processing_info = {
        "configuration": {
            "comment": "false",
            "publishLive": "false",
            "publishToMediaModule": "true",
            "publishToOaiPmh": "true",
        },
        "workflow": "fast",
    }
    # "workflow": "import"
    # "workflow": "fast"}

    test_video_file = os.path.abspath(
        os.path.join(tests.__file__, os.path.pardir, "assets", "test_video.m4v")
    )
    _test_event = tests.EV_API.create_event(
        test_acl, test_meta, processing_info, test_video_file
    )
    yield _test_event
    print("XXX deleting")
    _test_event.delete()


@pytest.mark.usefixtures("setup_oc_connection")
class TestEventsClass(unittest.TestCase):
    @pytest.mark.skip(reason="skipped while event creation is disabled")
    def test_acl_add(self):
        ev = _test_event
        self.assertIsNotNone(ev, "Event must not be None")
        num_acls = len(ev.get_acl())
        logging.info(num_acls)
        # new events can't be modified immediately (e.g. ACL), so wait...
        failed = False
        try_counter = 0
        while not failed:
            try:
                ev.add_to_acl(ACL.get_read_acl("ROLE_ANONYMOUS"))
            except OcPyRequestException as e:
                if e.get_code() == 403:
                    logging.warning(
                        "event may be processing... can't modify ACL -> have to try again...(sleeping 30s)"
                    )
                    time.sleep(30)
            try_counter += 1
            if try_counter > 10:
                failed = True

        assert len(ev.get_acl()) > num_acls

    def test_get_one_event(self):
        ev = tests.EV_API.get_events(limit=1, offset=0)
        self.assertGreaterEqual(len(ev), 1)

    def test_event_filter(self):
        evs = tests.EV_API.get_events(
            events_filter=EventsApi.Filter().set_text_filter_filter("bunny")
        )
        self.assertGreaterEqual(len(evs), 1)

    def test_get_all_events_non_generator(self):
        evs = tests.EV_API.get_all_events(generator=False)
        self.assertGreaterEqual(len(evs), 1)

    def test_get_all_events_generator(self):
        evs = tests.EV_API.get_all_events(batch_size=2, generator=True)
        self.assertIsInstance(evs, types.GeneratorType)
        ev = next(evs)
        self.assertIsInstance(ev, Event)

    def test_add_caption_track(self):
        ev: Event = tests.EV_API.get_event("f4095f6c-5182-4647-a3ce-3d183b00dedb")

        self.assertIsNotNone(ev, "Event must not be None")
        self.assertIsInstance(ev, Event, "Event must be an instance of Event")
        logging.info(f"Event: {ev.get_identifier()}")
        caption_file = os.path.abspath(
            os.path.join(tests.__file__, os.path.pardir, "assets", "test.vtt")
        )
        ok = tests.EV_API.add_track(
            event_id=ev.get_identifier(),
            overwrite_existing=True,
            flavor="captions/test",
            track_file=caption_file,
            tags=[
                "archive",
                "subtitles",
                "lang:de",
                "type:subtitle",
                "generator-type:auto",
            ],
        )
        self.assertTrue(ok, "Adding caption track failed")
        logging.info("all good")


"""
def setup_func():
    global test_event
    print("setup func ...")
    test_event = create_test_event()


def teardown_func():
    print("teardown func ...")
    global test_event
    print(test_event.delete())
"""

# @with_setup(setup_func, teardown_func)
# def tests():
#    ev_api.get_all_events()
