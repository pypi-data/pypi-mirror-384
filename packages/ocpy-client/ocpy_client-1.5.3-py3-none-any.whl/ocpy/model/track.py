#  Copyright (c) 2019. Tobias Kurze

import json
import re
from loguru import logger
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


class Track:
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
        try: 
            problematic_keys: List[str] = [k for k in d.keys() if any([s in k for s in ['#', '@']])]
            for p_k in problematic_keys:
                nice_key = p_k.replace('#', '').replace('@', '')
                d[nice_key] = d.pop(p_k)
            for k in d.keys():  # recurse
                if isinstance(d[k], dict):
                    self._fix_dict_keys(d[k])
        except AttributeError as e:
            logger.error(f"AttributeError: {e}")

    def get_type(self):
        return self.data.get("type", None)

    def get_audio(self):
        return self.data.get("audio", None)

    def get_video(self):
        return self.data.get("video", None)


class TrackList:
    def __init__(self, data: List[dict]):
        self.tracks = []
        for t in data:
            if isinstance(t, dict):
                self.tracks.append(Track(t))

    def get_tracks(self) -> List[Track]:
        return self.tracks

    def get_tracks_by_flavor(self, flavor: re = r'.*/source') -> List[Track]:
        tracks = []
        for t in self.tracks:
            t_type = t.get_type()
            regexp = re.compile(flavor)
            if regexp.search(t_type):
                tracks.append(t)
        return tracks


if __name__ == '__main__':
    pprint(d)
    pprint(Track(d).data)
