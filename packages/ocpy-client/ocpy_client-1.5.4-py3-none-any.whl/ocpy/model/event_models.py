#  Copyright (c) 2019. Tobias Kurze

import json
from typing import List, Optional, Union

from ocpy.utils import camel_case_to_snake_case


class EventMetadataItem:
    def __init__(
        self,
        identifier: str,
        label: str,
        required: bool,
        read_only: bool,
        type: str,
        value: Union[str, int],
    ):
        self.id = identifier
        self.label = label
        self.read_only = read_only
        self.required = required
        self.type = type
        self.value = value

    def __str__(self):
        obj = self.get_as_dict()
        return json.dumps(obj, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_as_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "readOnly": self.read_only,
            "required": self.required,
            "type": self.type,
            "value": self.value,
        }


class EventMetadata:
    def __init__(
        self,
        metadata_item: Union[EventMetadataItem, List[EventMetadataItem]],
        flavor: str = "dublincore/episode",
        title: str = "EVENTS.EVENTS.DETAILS.CATALOG.EPISODE",
    ):
        self.flavor = flavor
        self.title = title
        self.meta_data_items = []
        self.add_metadata_item(metadata_item)

    def __str__(self):
        obj = self.get_metadata_as_dict(compact=False)
        return json.dumps(obj, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_metadata_as_dict(self, compact: bool = True):
        if compact:
            meta_result = dict()
            # merge metadata
            return {i["id"]: i["value"] for i in self.meta_data_items}
        else:
            return {
                "fields": self.meta_data_items,
                "flavor": self.flavor,
                "title": self.title,
            }

    def add_metadata_item(
        self, metadata_item: Union[EventMetadataItem, List[EventMetadataItem]]
    ):
        if isinstance(metadata_item, List):
            for i in metadata_item:
                if isinstance(i, dict):
                    self.meta_data_items.append(
                        EventMetadataItem(**self.rename_event_metadata_keys(i))
                    )
        else:
            if isinstance(metadata_item, dict):
                metadata_item = EventMetadataItem(
                    **self.rename_event_metadata_keys(metadata_item)
                )
            self.meta_data_items.append(metadata_item)

    @staticmethod
    def rename_event_metadata_keys(metadata_dict: dict):
        """
        Converts keys specified in camelCase form to snake_case form.
        :param metadata_dict:
        :return:
        """
        for key in metadata_dict.keys():
            metadata_dict[camel_case_to_snake_case(key)] = metadata_dict.pop(key)
        return metadata_dict


class PublicationMetadata:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_id(self):
        return self.data["id"]

    def get_checksum(self):
        return self.data["checksum"]

    def get_flavor(self):
        return self.data["flavor"]

    def get_mediatype(self):
        return self.data["mediatype"]

    def get_size(self):
        return self.data["size"]

    def get_tags(self):
        return self.data["tags"]

    def get_url(self):
        return self.data["url"]


class Media:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_id(self):
        return self.data["id"]

    def get_checksum(self):
        return self.data["checksum"]

    def get_bitrate(self):
        return self.data["bitrate"]

    def get_duration(self):
        return self.data["duration"]

    def get_description(self):
        return self.data["description"]

    def get_flavor(self):
        return self.data["flavor"]

    def get_framecount(self):
        return self.data["framecount"]

    def get_framerate(self):
        return self.data["framerate"]

    def has_audio(self):
        return self.data["has_audio"]

    def has_video(self):
        return self.data["has_video"]

    def get_height(self):
        return self.data["height"]

    def get_mediatype(self):
        return self.data["mediatype"]

    def get_size(self):
        return self.data["size"]

    def get_tags(self):
        return self.data["tags"]

    def get_url(self):
        return self.data["url"]

    def get_width(self):
        return self.data["width"]


class Attachment:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_checksum(self):
        return self.data["checksum"]

    def get_flavor(self):
        return self.data["flavor"]

    def get_id(self):
        return self.data["id"]

    def get_mediatype(self):
        return self.data["mediatype"]

    def get_ref(self):
        return self.data["ref"]

    def get_size(self):
        return self.data["size"]

    def get_tags(self):
        return self.data["tags"]

    def get_url(self):
        return self.data["url"]


class Publication:
    def __init__(self, user, password, url, data):
        self.base_url = url
        self.user = user
        self.password = password
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_attachments(self, raw=False):
        if raw:
            return self.data["attachments"]
        else:
            attachments = list()
            for a in self.data["attachments"]:
                attachments.append(Attachment(a))
            return attachments

    def get_attachments_presentation_segment_preview(self) -> List[Attachment]:
        attachments = list()
        for a in self.get_attachments():
            if a.get_flavor() == "presentation/segment+preview":
                attachments.append(a)
        return attachments

    def get_attachments_presentation_timeline_preview(self) -> List[Attachment]:
        attachments = list()
        for a in self.get_attachments():
            if a.get_flavor() == "presentation/timeline+preview":
                attachments.append(a)
        return attachments

    def get_attachments_presentation_search_preview(self) -> List[Attachment]:
        attachments = list()
        for a in self.get_attachments():
            if a.get_flavor() == "presentation/search+preview":
                attachments.append(a)
        return attachments

    def get_attachments_presenter_player_preview(self) -> List[Attachment]:
        attachments = list()
        for a in self.get_attachments():
            if a.get_flavor() == "presenter/player+preview":
                attachments.append(a)
        return attachments

    def get_channel(self):
        return self.data["channel"]

    def get_id(self):
        return self.data["id"]

    def get_media(self, raw=False) -> List[Media]:
        if raw:
            return self.data["media"]
        else:
            media = list()
            for m in self.data["media"]:
                media.append(Media(m))
            return media

    def get_presentation_delivery_media(self) -> Optional[Media]:
        media = self.get_media()
        for m in media:
            if m.get_flavor() == "presentation/delivery":
                return m
        return None

    def get_mediatype(self):
        return self.data["mediatype"]

    def get_metadata(self, raw=False):
        if raw:
            return self.data["metadata"]
        else:
            metadata = list()
            for m in self.data["metadata"]:
                metadata.append(PublicationMetadata(m))
            return metadata

    def get_metadata_dc_episode(self) -> Optional[List[PublicationMetadata]]:
        for m in self.get_metadata():
            if m.get_flavor() == "dublincore/episode":
                return m
        return None

    def get_metadata_dc_series(self) -> Optional[List[PublicationMetadata]]:
        for m in self.get_metadata():
            if m.get_flavor() == "dublincore/series":
                return m
        return None

    def get_metadata_mpeg7_text(self) -> Optional[List[PublicationMetadata]]:
        for m in self.get_metadata():
            if m.get_flavor() == "mpeg-7/text":
                return m
        return None

    def get_url(self):
        return self.data["url"]
