"""Module for OC Event API (external API)"""

import os
import json
from typing import Generator, List, Optional, Union

import pendulum
import requests
from loguru import logger
from pendulum.parsing import ParserError
from requests.auth import HTTPBasicAuth

from ocpy.api.api_client import OpenCastBaseApiClient
from ocpy import OcPyRequestException
from ocpy.model.event_models import Publication
from ocpy.model.publication import PublicationList
from ocpy.model.acl import ACL, Action
from ocpy.model.scheduling import Scheduling


class Event:
    """Class for Opencast events"""

    def __init__(self, user, password, url, data):
        self.base_url = url
        self.user = user
        self.password = password
        self.data: dict = data
        self._augment_data()

    def __str__(self):
        return json.dumps(
            self.data,
            sort_keys=True,
            indent=4,
            separators=(",", ": "),
            default=str,
        )

    def __repr__(self):
        return self.__str__()

    def _augment_data(self):
        if "created" in self.data and self.data["created"]:
            try:
                if isinstance(self.data["created"], str):
                    self.data["created"] = pendulum.parse(self.data["created"])
            except ParserError:
                pass
            except ValueError:
                pass
        if "start" in self.data and self.data["start"]:
            try:
                if isinstance(self.data["start"], str):
                    self.data["start"] = pendulum.parse(self.data["start"])
            except ParserError:
                pass
            except ValueError:
                pass
        if "duration" in self.data and self.data["duration"]:
            try:
                self.data["duration"] = int(self.data["duration"])
            except ValueError:
                pass

    def get_archive_version(self):
        return self.data.get("archive_version")

    def get_contributor(self):
        return self.data.get("contributor")

    def get_created(self):
        return self.data.get("created")

    def get_creator(self):
        return self.data.get("creator")

    def get_description(self):
        return self.data.get("description")

    def get_duration(self):
        return self.data.get("duration")

    def has_previews(self):
        return self.data.get("has_previews")

    def get_identifier(self):
        return self.data.get("identifier")

    def get_is_part_of(self):
        return self.data.get("is_part_of", None)

    def get_series_name(self):
        return self.data.get("series", None)

    def get_location(self):
        return self.data.get("location")

    def get_presenter(self):
        return self.data.get("presenter")

    def get_processing_state(self):
        return self.data.get("processing_state")

    def get_publication_status(self):
        return self.data.get("publication_status")

    def get_status(self):
        return self.data.get("status")

    def get_start(self):
        return self.data.get("start")

    def get_subjects(self):
        return self.data.get("subjects")

    def get_title(self):
        return self.data.get("title")

    def get_acl(self, **kwargs) -> Optional[List[ACL]]:
        res = self.data.get("acl", None)
        if res is None:
            url = self.base_url + "/acl"
            res = requests.get(
                url,
                timeout=kwargs.pop("timeout", 30),
                auth=HTTPBasicAuth(self.user, self.password),
            )
            if res.ok:
                res = res.json()
            else:
                return None
        acls = []
        for a in res:
            acls.append(ACL(a["allow"], a["role"], Action(a["action"])))
        return acls

    def set_acl(self, acl_list, **kwargs):
        url = self.base_url + "/acl"
        if isinstance(acl_list, List):
            acls = []
            for a in acl_list:
                if isinstance(a, ACL):
                    acls.append(a.get_acl_dict())
                else:
                    acls.append(a)
            acl_list = acls
        if isinstance(acl_list, ACL):
            acl_list = [acl_list.get_acl_dict()]

        data = {
            "acl": json.dumps(acl_list),
        }
        logger.debug(f"set acl data: {data}")
        res = requests.put(
            url,
            timeout=kwargs.pop("timeout", 30),
            data=data,
            auth=HTTPBasicAuth(self.user, self.password),
        )
        if res.ok:
            return "ok"
        raise OcPyRequestException(
            "could not set ACL! ("
            + res.text
            + " ["
            + str(res.status_code)
            + "])"
            + "acl: "
            + json.dumps(acl_list)
        )

    def add_to_acl(self, acl: Union[ACL, List[ACL]]):
        logger.debug(f"adding to acl: {acl}")
        actual_acl = self.get_acl()
        if not isinstance(acl, List):
            acl = [acl]
        for n_a in acl:
            found = False
            for a_a in actual_acl:
                if a_a == n_a:
                    found = True
                    break
            if not found:
                actual_acl.append(n_a)

        return self.set_acl(actual_acl)

    def remove_from_acl(self, acl: ACL):
        actual_acl = self.get_acl()

        if not isinstance(acl, List):
            acl = [acl]
        for aa in actual_acl:
            for na in acl:
                if aa == na:
                    actual_acl.remove(na)
        return self.set_acl(actual_acl)

    def get_metadata(self, raw=False, force_update=False, **kwargs):
        if "metadata" in self.data and not force_update:
            return self.data["metadata"]
        url = self.base_url + "/metadata"
        res = requests.get(
            url,
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
        )
        if res.ok:
            if raw:
                return res.json()
            meta_result = dict()
            for r in res.json():
                # merge metadata
                meta_result = {
                    **meta_result,
                    **{m["id"]: m["value"] for m in r["fields"] if "value" in m},
                }
            return meta_result
        return None

    def delete_metadata(self, **kwargs):
        url = self.base_url + "/metadata"
        params = {"type": "dublincore/episode"}
        res = requests.delete(
            url,
            timeout=kwargs.pop("timeout", 30),
            params=params,
            auth=HTTPBasicAuth(self.user, self.password),
        )
        if res.ok:
            return "ok"
        raise OcPyRequestException(
            "Could not delete metadata for event ("
            + self.get_identifier()
            + ")! ("
            + res.text
            + ")"
        )

    def get_publications(self, force_update=False, **kwargs) -> List[Publication]:
        if "publications" in self.data and not force_update:
            return [
                Publication(self.user, self.password, self.base_url + "/" + p["id"], p)
                for p in self.data["publications"]
            ]
        results = []
        url = self.base_url + "/publications"
        res = requests.get(
            url,
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
        )
        if res.ok:
            for p in res.json():
                results.append(
                    Publication(
                        self.user,
                        self.password,
                        self.base_url + "/" + p["id"],
                        p,
                    )
                )
        return results

    def get_publication(self, publication_id, **kwargs) -> Optional[Publication]:
        url = self.base_url + "/publications/" + publication_id
        res = requests.get(
            url,
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
        )
        if res.ok:
            p = res.json()
            return Publication(
                self.user, self.password, self.base_url + "/" + p["id"], p
            )
        return None

    def get_publication_by_channel(self, channel_name) -> Optional[Publication]:
        publications = self.get_publications()
        for p in publications:
            if p.get_channel() == channel_name:
                return p
        return None

    def get_api_channel_publication(self) -> Publication:
        return self.get_publication_by_channel("api")

    def get_engage_player_publication(self) -> Publication:
        return self.get_publication_by_channel("engage-player")

    def get_oai_pmh_default_publication(self) -> Publication:
        return self.get_publication_by_channel("oaipmh-default")

    def get_scheduling(self, force_update=False, **kwargs):
        if "scheduling" in self.data and not force_update:
            return self.data["scheduling"]
        url = self.base_url + "/scheduling"
        res = requests.get(
            url,
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
        )
        if res.ok and res.status_code != 204:
            return Scheduling(**res.json())
        return None

    def set_scheduling(self, scheduling: Scheduling, **kwargs):
        url = self.base_url + "/scheduling"
        res = requests.put(
            url,
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
            json=scheduling.get_scheduling_dict(),
            **kwargs,
        )
        if res.ok:
            return None
        raise OcPyRequestException("could not set event scheduling!", response=res)

    def delete(self, **kwargs):
        url = self.base_url
        res = requests.delete(
            url,
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
        )
        if res.ok:
            return "ok"
        raise OcPyRequestException(
            "Could not delete event (" + self.get_identifier() + ")! (" + res.text + ")"
        )


class EventsApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None, **kwargs):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/api/events"

    def get_events(
        self,
        method="GET",
        limit=100,
        offset=0,
        sort="",
        sign=True,
        with_acl=False,
        with_metadata=False,
        with_scheduling=False,
        with_publications=False,
        events_filter=None,
        **kwargs,
    ) -> List[Event]:
        """
        :param method:
        :param limit:
        :param offset:
        :param sort:
        :param sign:
        :param with_acl:
        :param with_metadata:
        :param with_scheduling:
        :param with_publications:
        :param events_filter:
        :param kwargs:
        :return: List[Event]
        """
        parameters = {
            "limit": limit,
            "offset": offset,
            "sort": sort,
            "sign": sign,
            "withacl": with_acl,
            "withmetadata": with_metadata,
            "withscheduling": with_scheduling,
            "withpublications": with_publications,
        }
        if events_filter:
            if isinstance(events_filter, EventsApi.Filter):
                parameters["filter"] = events_filter.get_filter_string()
            else:
                parameters["filter"] = events_filter
        results = []
        res = requests.request(
            method,
            self.base_url,
            timeout=kwargs.pop("timeout", 60),
            auth=HTTPBasicAuth(self.user, self.password),
            params=parameters,
            **kwargs,
        )
        if res.ok:
            for event in res.json():
                results.append(
                    Event(
                        self.user,
                        self.password,
                        self.base_url + "/" + event["identifier"],
                        event,
                    )
                )
        else:
            if res.status_code == 500:
                logger.warning(
                    "Opencast responded with an internal server error (500)."
                )
            else:
                logger.error(
                    "Request to Opencast resulted in an error (code: {}): {}".format(
                        res.status_code, res.content
                    )
                )
            raise OcPyRequestException(res.content.decode("utf-8"), response=res)
        return results

    def get_all_events(
        self,
        sign=True,
        with_acl=False,
        with_metadata=False,
        with_scheduling=False,
        with_publications=False,
        sort=None,
        events_filter=None,
        batch_size=100,
        print_progress=False,
        initial_offset=0,
        generator=False,
    ) -> List[Event] | Generator[Event, None, None]:
        events_generator = self.get_all_events_generator(
            sign=sign,
            with_acl=with_acl,
            with_metadata=with_metadata,
            with_scheduling=with_scheduling,
            with_publications=with_publications,
            sort=sort,
            events_filter=events_filter,
            batch_size=batch_size,
            print_progress=print_progress,
            initial_offset=initial_offset,
        )
        if generator:
            return events_generator
        return list(events_generator)

    def get_all_events_generator(
        self,
        sign=True,
        with_acl=False,
        with_metadata=False,
        with_scheduling=False,
        with_publications=False,
        sort=None,
        events_filter=None,
        batch_size=100,
        print_progress=False,
        initial_offset=0,
    ) -> Generator[Event, None, None]:
        count = initial_offset
        while True:
            if print_progress:
                logger.info(f"requesting {batch_size} starting from offset {count}")
            res = self.get_events(
                sign=sign,
                with_acl=with_acl,
                sort=sort,
                with_metadata=with_metadata,
                with_scheduling=with_scheduling,
                with_publications=with_publications,
                events_filter=events_filter,
                limit=batch_size,
                offset=count,
            )
            if res is None or len(res) <= 0:
                logger.debug(
                    f"DONE; got 0 resuts; retrieved a total of {len(res)} events"
                )
                break
            logger.debug(f"got {len(res)} events")
            count += len(res)
            for r in res:
                yield r
        return

    def get_event(
        self,
        event_id,
        with_acl=False,
        with_metadata=False,
        with_scheduling=False,
        with_publications=False,
        **kwargs,
    ) -> Event:
        parameters = {
            "withacl": with_acl,
            "withmetadata": with_metadata,
            "withpublications": with_publications,
            "withscheduling": with_scheduling,
        }
        res = requests.get(
            self.base_url + "/" + event_id,
            timeout=kwargs.pop("timeout", 60),
            auth=HTTPBasicAuth(self.user, self.password),
            params=parameters,
            **kwargs,
        )
        if res.ok:
            event = res.json()
            return Event(
                self.user,
                self.password,
                self.base_url + "/" + event["identifier"],
                event,
            )
        logger.error(res.text)
        raise OcPyRequestException("could not get event!", response=res)

    def get_event_acl(self, event_id, **kwargs) -> List[ACL]:
        res = requests.get(
            self.base_url + f"/{event_id}/acl",
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
            **kwargs,
        )
        acls = []
        if res.ok:
            for a in res.json():
                acls.append(ACL(a["allow"], a["role"], Action(a["action"])))
            return acls
        raise OcPyRequestException("could not get event acls!", response=res)

    def get_event_metadata(self, event_id, **kwargs) -> dict:
        res = requests.get(
            self.base_url + f"/{event_id}/metadata",
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
            **kwargs,
        )
        if res.ok:
            return res.json()
        raise OcPyRequestException("could not get event metadata!", response=res)

    def get_event_publications(self, event_id, **kwargs) -> PublicationList:
        res = requests.get(
            self.base_url + f"/{event_id}/publications",
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
            **kwargs,
        )
        if res.ok:
            return PublicationList(res.json())
        raise OcPyRequestException("could not get event publications!", response=res)

    def get_event_scheduling(self, event_id, **kwargs) -> dict:
        res = requests.get(
            self.base_url + f"/{event_id}/scheduling",
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
            **kwargs,
        )
        if res.ok:
            return res.json()
        raise OcPyRequestException("could not get event scheduling!", response=res)

    def set_event_scheduling(self, event_id, scheduling: Scheduling, **kwargs) -> None:
        res = requests.put(
            self.base_url + f"/{event_id}/scheduling",
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
            json=scheduling.get_scheduling_dict(),
            **kwargs,
        )
        if res.ok:
            return None
        raise OcPyRequestException("could not set event scheduling!", response=res)

    def create_event(
        self, acl, metadata, processing, presenter_file, **kwargs
    ) -> Event:
        if isinstance(acl, List):
            acls = []
            for a in acl:
                if isinstance(a, ACL):
                    acls.append(a.get_acl_dict())
                else:
                    acls.append(a)
            acl = acls
        if isinstance(acl, ACL):
            acl = acl.get_acl_dict()
        data = {
            "acl": json.dumps(acl),
            "metadata": json.dumps(metadata),
            "processing": json.dumps(processing),
        }
        with open(presenter_file, "rb") as presenter_f:

            res = requests.post(
                self.base_url + "/",
                timeout=kwargs.pop("timeout", 30),
                auth=HTTPBasicAuth(self.user, self.password),
                data=data,
                files={"presenter": presenter_f},
                **kwargs,
            )
        if res.ok:
            event = res.json()
            return Event(
                self.user,
                self.password,
                self.base_url + "/" + event["identifier"],
                event,
            )
        logger.error(data)
        raise OcPyRequestException(
            "could not create event! (" + res.text + ")", response=res
        )

    def schedule_event(
        self, acl, metadata, scheduling, processing, **kwargs
    ) -> Union[Event, List[Event]]:
        """
        Creates a single event for a single scheduled recording. *It is not possible to schedule multiple recordings
        with this function / API endpoint, or is it?!*
        """
        if isinstance(acl, ACL):
            acl = [acl]
        if isinstance(acl, List):
            acls = []
            for a in acl:
                if isinstance(a, ACL):
                    acls.append(a.get_acl_dict())
                else:
                    acls.append(a)
            acl = acls

        data = {
            "acl": json.dumps(acl),
            "metadata": json.dumps(metadata),
            "processing": json.dumps(processing),
            "scheduling": json.dumps(scheduling),
        }
        logger.debug(f"sending {data} ")

        res = requests.post(
            self.base_url + "/",
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
            data=data,
            files=data,
            **kwargs,
        )
        if res.ok:
            event = res.json()
            if isinstance(event, list):
                evs = []
                for e in event:
                    evs.append(
                        Event(
                            self.user,
                            self.password,
                            self.base_url + "/" + e["identifier"],
                            e,
                        )
                    )
                return evs
            return Event(
                self.user,
                self.password,
                self.base_url + "/" + event["identifier"],
                event,
            )
        logger.error(f"status code: {res.status_code}", res.text)
        info = ""
        if res.status_code == 409:
            info = (
                "Additional info: (409) Conflict: (probably) conflicting events found)"
            )
        raise OcPyRequestException(
            f"could not create event! ({res.text}) - {info}",
            response=res,
            code=res.status_code,
        )

    def delete_event(self, event_id, **kwargs):
        res = requests.delete(
            self.base_url + "/" + event_id,
            timeout=kwargs.pop("timeout", 30),
            auth=HTTPBasicAuth(self.user, self.password),
            **kwargs,
        )
        if res.ok:
            return "ok"
        raise OcPyRequestException("could not delete event! (" + res.text + ")")

    def get_events_part_of(self, series, limit=100, **kwargs) -> List[Event]:
        if not isinstance(series, str):
            series = series.get_identifier()
        return self.get_events(
            limit=limit,
            events_filter=EventsApi.Filter().set_series_filter(series),
            **kwargs,
        )

    def add_track(
        self,
        event_id: str,
        flavor: str,
        track_file,
        tags: List[str],
        overwrite_existing=False,
        **kwargs,
    ) -> str:
        """Adds a track to an event using a POST request and form data.
        Args:
            event_id (str): The ID of the event to which the track will be added.
            flavor (str): The flavor of the track (e.g., "captions/test").
            track_file (str): The path to the track file to be uploaded.
            tags (List[str]): A list of tags to be associated with the track.
            overwrite_existing (bool): Whether to overwrite an existing track with the same flavor. - Sadly this seems to not work
            yet, so you have to delete the track first if you want to overwrite it.
            **kwargs: Additional keyword arguments for the request.
        """

        url = f"{self.base_url}/{event_id}/track"
        files = {"track": (os.path.basename(track_file), open(track_file, "rb"))}
        data = {
            "eventId": event_id,
            "overwriteExisting": overwrite_existing,
            "flavor": flavor,
            "tags": ",".join(tags) if tags else "",
        }
        try:
            res = requests.post(
                url,
                timeout=kwargs.pop("timeout", 30),
                auth=HTTPBasicAuth(self.user, self.password),
                files=files,
                data=data,
                **kwargs,
            )
            if res.ok:
                return True
            raise OcPyRequestException(
                f"Could not add track to event {event_id}! ({res.text})",
                response=res,
            )
        except FileNotFoundError as e:
            raise OcPyRequestException(
                f"File not found: {track_file}. Please check the file path."
            ) from e
        except requests.RequestException as e:
            raise OcPyRequestException(
                f"An error occurred while adding the track: {str(e)}"
            ) from e

    class Filter:
        def __init__(self):
            self.filter_string = None

        def update_filter_string(self, update_string):
            if self.filter_string is None:
                self.filter_string = update_string
            else:
                self.filter_string += "," + update_string

        def set_contributors_filter(self, contributors):
            self.update_filter_string("contributors:{}".format(contributors))
            return self

        def set_location_filter(self, location):
            self.update_filter_string("location:{}".format(location))
            return self

        def set_series_filter(self, series):
            self.update_filter_string("series:{}".format(series))
            return self

        def set_subject_filter(self, subject):
            self.update_filter_string("subject:{}".format(subject))
            return self

        def set_start_filter(
            self,
            start_from: str | pendulum.DateTime,
            start_to: str | pendulum.DateTime,
        ):
            # example filter – start:2022-07-25T11:00:00.000Z/2022-07-25T14:00:00.000Z,subject:SS222182740
            if isinstance(start_from, pendulum.DateTime):
                start_from = start_from.isoformat()
            if isinstance(start_to, pendulum.DateTime):
                start_to = start_to.isoformat()
            self.update_filter_string(f"start:{start_from}/{start_to}")
            return self

        def set_text_filter_filter(self, text_filter):
            self.update_filter_string("textFilter:{}".format(text_filter))
            return self

        def get_filter_string(self):
            return self.filter_string
