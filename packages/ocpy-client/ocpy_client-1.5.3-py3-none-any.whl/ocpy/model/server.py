#  Copyright (c) 2019. Tobias Kurze

import json


class Server:
    def __init__(self, name: str, port: str):
        self.name = name
        self.port = port

    def __str__(self):
        return json.dumps({"name": self.name, "port": self.port})

    def __repr__(self):
        return self.__str__()

    def get_name(self):
        return self.name

    def get_port(self):
        return self.port
