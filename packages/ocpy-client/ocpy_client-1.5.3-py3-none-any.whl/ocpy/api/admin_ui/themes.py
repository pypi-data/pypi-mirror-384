import requests
from loguru import logger
from requests.auth import HTTPBasicAuth
import json
from pprint import pprint

from typing import List

from ocpy import OcPyRequestException
from ocpy.api.api_client import OpenCastBaseApiClient


class Theme:
    def __init__(self, user, password, url, data):
        self.base_url = url
        self.user = user
        self.password = password
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_bumper_file(self):
        return self.data["bumperFile"]

    def get_title_slide_background(self):
        return self.data["titleSlideBackground"]

    def get_watermark_file_url(self):
        return self.data["watermarkFileUrl"]

    def get_license_slide_background(self):
        return self.data["licenseSlideBackground"]

    def get_bumper_file_name(self):
        return self.data["bumperFileName"]

    def is_trailer_active(self):
        return self.data["trailerActive"]

    def get_default(self):
        return self.data["default"]

    def get_bumper_file_url(self):
        return self.data["bumperFileUrl"]

    def is_license_slide_active(self):
        return self.data["licenseSlideActive"]

    def is_watermark_active(self):
        return self.data["watermarkActive"]

    def get_trailer_file_url(self):
        return self.data["trailerFileUrl"]

    def is_title_slide_active(self):
        return self.data["titleSlideActive"]

    def get_trailer_file_name(self):
        return self.data["trailerFileName"]

    def get_id(self):
        return self.data["id"]

    def get_creator(self):
        return self.data["creator"]

    def is_bumper_active(self):
        return self.data["bumperActive"]

    def get_title_slide_metadata(self):
        return self.data["titleSlideMetadata"]

    def get_watermark_position(self):
        return self.data["watermarkPosition"]

    def get_creation_date(self):
        return self.data["creationDate"]

    def get_license_slide_description(self):
        return self.data["licenseSlideDescription"]

    def get_watermark_file_name(self):
        return self.data["watermarkFileName"]

    def get_watermark_file(self):
        return self.data["watermarkFile"]

    def get_name(self):
        return self.data["name"]

    def get_usage(self):
        url = self.base_url + "/usage.json"
        res = requests.get(url, auth=HTTPBasicAuth(self.user, self.password))
        if res.ok:
            return res.json()
        raise OcPyRequestException("could not get theme usage!", response=res)

    def delete(self):
        res = requests.delete(
            self.base_url, auth=HTTPBasicAuth(self.user, self.password)
        )
        if res.ok:
            return "ok"
        raise OcPyRequestException("could not delete theme!", response=res)


class ThemesApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/admin-ng/themes"

    def get_theme(self, theme_id: int, **kwargs) -> Theme:
        url = self.base_url + "/{}.json".format(theme_id)
        res = requests.get(url, auth=HTTPBasicAuth(self.user, self.password), **kwargs)
        if res.ok:
            theme = res.json()
            return Theme(
                self.user, self.password, self.base_url + "/{}".format(theme_id), theme
            )
        raise OcPyRequestException("could not get theme!", response=res)

    def get_themes(
        self, limit=100, offset=0, sort=None, themes_filter=None, **kwargs
    ) -> List[Theme]:
        """
        :param limit:
        :param offset:
        :param sort:
        :param themes_filter:
        :param kwargs:
        :return: List[Event]
        """
        parameters = {"limit": limit, "offset": offset, "sort": sort}
        if themes_filter:
            if isinstance(themes_filter, ThemesApi.Filter):
                parameters["filter"] = themes_filter.get_filter_string()
            else:
                parameters["filter"] = themes_filter
        results = []
        res = requests.get(
            self.base_url + "/themes.json",
            auth=HTTPBasicAuth(self.user, self.password),
            params=parameters,
            **kwargs
        )
        if res.ok:
            for theme in res.json()["results"]:
                results.append(
                    Theme(
                        self.user,
                        self.password,
                        self.base_url + "/{}".format(theme["id"]),
                        theme,
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

    def get_all_themes(self) -> List[Theme]:
        result = []
        while True:
            res = self.get_themes(limit=100, offset=len(result))
            if res is None or len(res) <= 0:
                break
            result.extend(res)
        return result

    def create_theme(
        self,
        name: str,
        default: bool = False,
        description: str = None,
        bumper_active: bool = None,
        trailer_active: bool = None,
        title_slide_active: bool = None,
        license_slide_active: bool = None,
        watermark_active: bool = None,
        bumper_file: str = None,
        trailer_file: str = None,
        watermark_file: str = None,
        title_slide_background: str = None,
        license_slide_background: str = None,
        title_slide_metadata: str = None,
        license_slide_description: str = None,
        watermark_position: str = None,
        **kwargs
    ) -> Theme:
        data = {
            "name": name,
            "default": default,
            "description": description,
            "bumperActive": bumper_active,
            "trailerActive": trailer_active,
            "titleSlideActive": title_slide_active,
            "licenseSlideActive": license_slide_active,
            "watermarkActive": watermark_active,
            "bumperFile": bumper_file,
            "trailerFile": trailer_file,
            "watermarkFile": watermark_file,
            "titleSlideBackground": title_slide_background,
            "licenseSlideBackground": license_slide_background,
            "titleSlideMetadata": title_slide_metadata,
            "licenseSlideDescription": license_slide_description,
            "watermarkPosition": watermark_position,
        }
        clean_data = {key: data[key] for key in data if data[key] is not None}
        res = requests.post(
            self.base_url,
            data=clean_data,
            auth=HTTPBasicAuth(self.user, self.password),
            **kwargs
        )
        if res.ok:
            theme = res.json()
            return Theme(
                self.user,
                self.password,
                self.base_url + "/{}".format(theme["id"]),
                theme,
            )
        raise OcPyRequestException("could not delete theme!", response=res)

    def update_theme(
        self,
        theme_id: int,
        name: str,
        default: bool = False,
        description: str = None,
        bumper_active: bool = None,
        trailer_active: bool = None,
        title_slide_active: bool = None,
        license_slide_active: bool = None,
        watermark_active: bool = None,
        bumper_file: str = None,
        trailer_file: str = None,
        watermark_file: str = None,
        title_slide_background: str = None,
        license_slide_background: str = None,
        title_slide_metadata: str = None,
        license_slide_description: str = None,
        watermark_position: str = None,
        **kwargs
    ) -> Theme:
        url = self.base_url + "/{}".format(theme_id)
        data = {
            "name": name,
            "default": default,
            "description": description,
            "bumperActive": bumper_active,
            "trailerActive": trailer_active,
            "titleSlideActive": title_slide_active,
            "licenseSlideActive": license_slide_active,
            "watermarkActive": watermark_active,
            "bumperFile": bumper_file,
            "trailerFile": trailer_file,
            "watermarkFile": watermark_file,
            "titleSlideBackground": title_slide_background,
            "licenseSlideBackground": license_slide_background,
            "titleSlideMetadata": title_slide_metadata,
            "licenseSlideDescription": license_slide_description,
            "watermarkPosition": watermark_position,
        }
        clean_data = {key: data[key] for key in data if data[key] is not None}
        res = requests.put(
            url, data=clean_data, auth=HTTPBasicAuth(self.user, self.password), **kwargs
        )
        if res.ok:
            theme = res.json()
            return Theme(
                self.user,
                self.password,
                self.base_url + "/{}".format(theme["id"]),
                theme,
            )
        raise OcPyRequestException("could not delete theme!", response=res)

    def delete_theme(self, theme_id: int, **kwargs):
        url = self.base_url + "/{}".format(theme_id)
        res = requests.delete(
            url, auth=HTTPBasicAuth(self.user, self.password), **kwargs
        )
        if res.ok:
            return "ok"
        raise OcPyRequestException("could not delete theme!", response=res)

    class Filter:
        def __init__(self):
            self.filter_string = None

        def update_filter_string(self, update_string):
            if self.filter_string is None:
                self.filter_string = update_string
            else:
                self.filter_string += "," + update_string

        def set_name_filter(self, name):
            self.update_filter_string("name:{}".format(name))
            return self

        def set_creator_filter(self, creator):
            self.update_filter_string("creator:{}".format(creator))
            return self

        def get_filter_string(self):
            return self.filter_string


def main():
    api = ThemesApi()
    # pprint(api.get_theme(36351).get_usage())
    # pprint(api.create_theme(name="tolles tests theme"))

    themes = api.get_themes()
    pprint(themes)
    # print("delete tests:")
    # pprint(themes[-1].delete())
    # pprint(api.get_all_themes())


if __name__ == "__main__":
    main()
