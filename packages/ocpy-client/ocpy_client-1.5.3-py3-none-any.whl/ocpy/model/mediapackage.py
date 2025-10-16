import json
from loguru import logger
from pprint import pprint
from typing import List, Optional

import xmltodict

from ocpy.model.publication import PublicationList
from ocpy.model.track import TrackList


class MediaPackage:
    def __init__(self, xml_data):
        self.xml_data = xml_data
        self.data = xmltodict.parse(xml_data)
        self.data = self.data["mediapackage"] if "mediapackage" in self.data else self.data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4,
                          separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_xml(self):
        return self.xml_data

    def get_id(self) -> str:
        return self.data["@id"]

    def get_start(self) -> str:
        return self.data["@start"]

    def get_xmlns(self) -> str:
        return self.data["@xmlns"]

    def get_attachments(self) -> str:
        return self.data["attachments"]

    def get_media(self) -> Optional[TrackList]:
        if self.data["media"] is None:
            logger.info(f"No media found in mediapackage {self.get_id()}")
            return TrackList([])
        tracks = self.data["media"].get("track",None)
        logger.trace(f"tracks: {tracks}")
        if tracks is None:
            return TrackList([])
        return TrackList(tracks)

    def get_metadata(self) -> str:
        return self.data["metadata"]

    def get_publications(self) -> PublicationList:
        publications = self.data["publications"].get("publication")
        return PublicationList(publications)
