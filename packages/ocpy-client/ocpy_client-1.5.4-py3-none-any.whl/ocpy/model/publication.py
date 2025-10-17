#  Copyright (c) 2019. Tobias Kurze

import json
import re
from collections import OrderedDict
from pprint import pprint
from typing import List, Optional

d = {
    "@id": "68e9fcb3-0662-43dd-a957-ba9bc1414195",
    "@type": "presentation/source",
    "audio": {
        "@id": "audio-1",
        "bitrate": "83050.0",
        "channels": "1",
        "device": None,
        "encoder": {
            "@type": "AAC (Advanced Audio Coding)"
        },
        "framecount": "261",
        "samplingrate": "48000"
    },
    "checksum": {
        "#text": "a3ac7ddabb263c2d00b73e8177d15c8d",
        "@type": "md5"
    },

    "duration": "5568",
    "live": "false",
    "mimetype": "video/mp4",
    "size": "383631",
    "tags": {
        "tag": "archive"
    },
    "url": "https://oc-bib-admin.bibliothek.kit.edu/assets/assets/983d0f7c-f81c-473a-80c2-e5a9b497ae99/68e9fcb3-0662-43dd-a957-ba9bc1414195/3/vid1_hqt.mp4",
    "video": {
        "@id": "video-1",
        "bitrate": "465641.0",
        "device": None,
        "encoder": {
            "@type": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10"
        },
        "framecount": "166",
        "framerate": "30.0",
        "resolution": "560x320"
    }
}


class Publication:
    def __init__(self, data):
        self.data = data
        self._fix_dict_keys()

    def __str__(self):
        return json.dumps(self.data)

    def __repr__(self):
        return self.__str__()

    def _fix_dict_keys(self, d: Optional[dict] = None):
        if d is None:
            d = self.data
        problematic_keys: List[str] = [k for k in d.keys() if
                                       any([s in k for s in ['#', '@']])]
        for p_k in problematic_keys:
            nice_key = p_k.replace('#', '').replace('@', '')
            d[nice_key] = d.pop(p_k)
        for k in d.keys():  # recurse
            if isinstance(d[k], dict) or isinstance(d[k], OrderedDict):
                self._fix_dict_keys(d[k])
            if isinstance(d[k], List) and len(d[k]) > 0 and isinstance(d[k][0], dict):
                [self._fix_dict_keys(e) for e in d[k]]

    def get_identifier(self):
        return self.data.get("identifier")

    def get_channel(self):
        return self.data.get("channel")

    def get_media(self):
        return self.data.get("media")

    def get_attachments(self):
        return self.data.get("attachments")

    def get_tags(self):
        return self.data.get("tags")

    def get_metadata(self):
        return self.data.get("metadata")

    def get_url(self):
        return self.data.get("url")


class PublicationList:
    def __init__(self, data: List[dict]):
        self.publications = []
        for p in data:
            self.publications.append(Publication(p))

    def get_publications(self) -> List[Publication]:
        return self.publications
    
    def get_publication_channels(self) -> List[str]:
        return [p.get_channel() for p in self.publications]

    def get_publication_by_channel(self, channel: str = "internal") -> \
    Optional[Publication]:
        for p in self.publications:
            if channel == p.get_channel():
                return p
        return None


if __name__ == '__main__':
    pprint(d)
    pprint(Publication(d).data)
