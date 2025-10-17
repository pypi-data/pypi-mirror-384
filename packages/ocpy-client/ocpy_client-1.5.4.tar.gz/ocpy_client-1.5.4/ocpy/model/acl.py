#  Copyright (c) 2019. Tobias Kurze

from functools import total_ordering
import json
from typing import List


class Action:
    def __init__(self, action_string):
        self.action_string = action_string.lower()

    def __str__(self):
        return json.dumps({"action": self.action_string})

    def __repr__(self):
        return self.__str__()

    def get_action_string(self):
        return self.action_string.lower()

    @staticmethod
    def get_read_action():
        return Action("read")

    @staticmethod
    def get_write_action():
        return Action("write")


@total_ordering
class ACL:
    def __init__(self, allow: bool, role: str, action: Action):
        self.allow = allow
        self.role = role
        if isinstance(action, str):
            action = Action(action)
        self.action = action

    def __str__(self):
        return json.dumps(self.get_acl_dict())

    def __repr__(self):
        return self.__str__()

    def get_acl_dict(self):
        return {
            "allow": self.allow,
            "role": self.role,
            "action": self.action.get_action_string(),
        }

    def __eq__(self, other) -> bool:
        return (
            self.role.lower(),
            self.action.get_action_string().lower(),
            self.allow,
        ) == (
            other.role.lower(),
            other.action.get_action_string().lower(),
            other.allow,
        )

    def __lt__(self, other) -> bool:
        return (self.role.lower(), self.action.get_action_string().lower()) < (
            other.role.lower(),
            other.action.get_action_string().lower(),
        )

    @staticmethod
    def get_read_acl(role: str, as_list=True):
        if not as_list:
            return ACL(True, role, Action.get_read_action())
        return [ACL(True, role, Action.get_read_action())]

    @staticmethod
    def get_write_acl(role: str, as_list=True):
        if not as_list:
            return ACL(True, role, Action.get_write_action())
        return [ACL(True, role, Action.get_write_action())]

    @staticmethod
    def get_read_write_acls(role: str) -> List["ACL"]:
        return [ACL.get_read_acl(role, False), ACL.get_write_acl(role, False)]

    def get_role(self):
        return self.role

    def is_allowed(self):
        return self.allow

    def get_action(self):
        return self.action
