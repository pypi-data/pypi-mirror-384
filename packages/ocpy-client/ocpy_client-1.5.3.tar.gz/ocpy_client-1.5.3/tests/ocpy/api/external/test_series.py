#  Copyright (c) 2019. Tobias Kurze

from typing import Union

import pytest

from ocpy.api.external import series
from ocpy.model.acl import ACL
import tests

_test_series: Union[None, series.Series] = None


@pytest.mark.usefixtures("setup_oc_connection")
class TestSeriesClass:
    def create_test_series(self):
        test_meta = [
            {
                "fields": [
                    {
                        "id": "title",
                        "label": "EVENTS.SERIES.DETAILS.METADATA.TITLE",
                        "type": "text",
                        "value": "Testserie_pytest",
                    }
                ],
                "flavor": "dublincore/series",
            }
        ]

        test_acl = ACL.get_read_write_acls("ROLE_TEST_USER")
        # test_acl = []

        return tests.SE_API.create_series(acl=test_acl, metadata=test_meta)

    def test_series_creation(self):
        print("testing series creation")
        seriess = tests.SE_API.get_all_series(generator=False)
        num_series = len(seriess)
        print(f"num_series before: {num_series}")
        new_series = self.create_test_series()
        new_s = tests.SE_API.get_all_series(generator=False)
        assert len(new_s) > num_series
        print(f"num_series after: {len(tests.SE_API.get_all_series(generator=False))}")
        new_series.delete()
        assert len(tests.SE_API.get_all_series(generator=False)) == num_series


"""
def setup_func():
    global test_event
    print("setup func ...")
    test_event = create_test_series()


def teardown_func():
    print("teardown func ...")
    global test_event
    print(test_event.delete())


@with_setup(setup_func, teardown_func)
def test_acl_add():
    return
    from pprint import pprint
    pprint(test_event.get_acl())
    num_acls = len(test_event.get_acl())
    print(num_acls)
    # new events can't be modified immediately (e.g. ACL), so wait...
    failed = False
    try_counter = 0
    while not failed:
        try:
            test_event.add_to_acl(ACL.get_read_acl("ROLE_ANONYMOUS"))
        except OcPyRequestException as e:
            if e.get_code() == 403:
                print("event may be processing ... can't modify ACL -> have to try again...(sleeping)")
                time.sleep(10)
                try_counter += 1
                if try_counter > 10:
                    failed = True
            else:
                failed = True
    assert len(test_event.get_acl()) > num_acls
"""

# @with_setup(setup_func, teardown_func)
# def tests():
#    ev_api.get_all_events()
