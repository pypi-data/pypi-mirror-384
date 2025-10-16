#  Copyright (c) 2019. Tobias Kurze

import json

from ocpy.model.server import Server


class Organization:
    def __init__(self, id, name, servers, admin_role, anonymous_role, properties):
        self.id = id
        self.name = name
        self.servers = servers
        self.admin_role = admin_role
        self.anonymous_role = anonymous_role
        self.properties = properties

    def __str__(self):
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "servers": self.servers,
                "adminRole": self.admin_role,
                "anonymousRole": self.anonymous_role,
                "properties": self.properties,
            }
        )

    def __repr__(self):
        return self.__str__()

    def get_id(self) -> str:
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_servers(self):
        print(self.servers)
        servers = []
        if isinstance(self.servers, dict):
            servers.append(Server(**self.servers["server"]))
        else:
            for s in self.servers:
                servers.append(Server(**s["server"]))
        return servers

    def get_admin_role(self) -> str:
        return self.admin_role

    def get_anonymous_role(self) -> str:
        return self.anonymous_role

    def get_properties(self):
        return self.properties
