#  Copyright (c) 2019. Tobias Kurze

from ocpy.model.acl import ACL, Action


def test_read_acl():
    acl = ACL(True, "ROLE_TEST", Action.get_read_action())
    assert str(acl) == '{"allow": true, "role": "ROLE_TEST", "action": "read"}'


def test_write_acl():
    acl = ACL.get_write_acl("ROLE_TEST", as_list=False)
    assert str(acl) == '{"allow": true, "role": "ROLE_TEST", "action": "write"}'


def test_read_write_acl():
    acls = ACL.get_read_write_acls("ROLE_TEST")
    assert len(acls) == 2
    assert str(acls[0]) == '{"allow": true, "role": "ROLE_TEST", "action": "read"}'
    assert str(acls[1]) == '{"allow": true, "role": "ROLE_TEST", "action": "write"}'
