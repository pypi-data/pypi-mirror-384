import json
from random import randrange
from pprint import pprint
from typing import List
from enum import Enum, auto
import requests
from loguru import logger
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import xmltodict
from ocpy.api.api_client import OpenCastBaseApiClient


class Service:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_url(self):
        return self.get_host() + self.get_path()

    def is_active(self) -> bool:
        return self.data["active"]

    def is_jobproducer(self) -> bool:
        return self.data["jobproducer"]

    def is_maintenance(self) -> bool:
        return self.data["maintenance"]

    def is_online(self) -> bool:
        return self.data["online"]

    def get_error_state_trigger(self) -> str:
        return self.data["error_state_trigger"]

    def get_host(self) -> str:
        return self.data["host"]

    def get_onlinefrom(self) -> str:
        return self.data["onlinefrom"]

    def get_path(self) -> str:
        return self.data["path"]

    def get_service_state(self) -> str:
        return self.data["service_state"]

    def get_state_changed(self) -> str:
        return self.data["state_changed"]

    def get_type(self) -> str:
        return self.data["type"]

    def get_warning_state_trigger(self) -> int:
        return self.data["warning_state_trigger"]


class Host:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def is_active(self) -> bool:
        return self.data["active"]

    def is_in_maintenance(self) -> bool:
        return self.data["maintenance"]

    def is_online(self) -> bool:
        return self.data["online"]

    def get_address(self) -> str:
        return self.data["address"]

    def get_base_url(self) -> str:
        return self.data["base_url"]

    def get_cores(self) -> int:
        return self.data["core"]

    def get_max_load(self) -> int:
        return self.data["max_load"]

    def get_memory(self) -> int:
        return self.data["memory"]

    def get_memory_mb(self) -> int:
        return int(self.get_memory() / (1024 * 1024))


class ServiceType(Enum):
    adminui_endpoint_AclEndpoint = auto()
    adminui_endpoint_GroupsEndpoint = auto()
    adminui_endpoint_JobEndpoint = auto()
    adminui_endpoint_ListProvidersEndpoint = auto()
    adminui_endpoint_PresetsEndpoint = auto()
    adminui_endpoint_SeriesEndpoint = auto()
    adminui_endpoint_ServerEndpoint = auto()
    adminui_endpoint_ServicesEndpoint = auto()
    adminui_endpoint_TasksEndpoint = auto()
    adminui_endpoint_ThemesEndpoint = auto()
    adminui_endpoint_UserSettingsEndpoint = auto()
    adminui_endpoint_UsersEndpoint = auto()
    adminui_endpoint_event = auto()
    adminui_endpoint_index = auto()
    adminui_endpoint_tools = auto()
    adminui_i18n = auto()
    annotation = auto()
    assetmanager = auto()
    authorization_xacml_manager = auto()
    caption = auto()
    capture_admin = auto()
    composer = auto()
    coverimage = auto()
    distribution_acl = auto()
    distribution_aws_s3 = auto()
    distribution_download = auto()
    distribution_streaming = auto()
    engage_plugin_manager = auto()
    execute = auto()
    external = auto()
    external_events = auto()
    external_groups = auto()
    external_security = auto()
    feed_impl_FeedServiceImpl = auto()
    fles = auto()
    fileupload = auto()
    groups = auto()
    incident = auto()
    info = auto()
    ingest = auto()
    inspection = auto()
    kernel_bundleinfo = auto()
    message_broker_endpoint = auto()
    nop = auto()
    oaipmhinfo = auto()
    organization = auto()
    publication_oaipmh = auto()
    publication_youtube = auto()
    scheduler = auto()
    search = auto()
    series = auto()
    serviceregistry = auto()
    silencedetection = auto()
    smil = auto()
    sox = auto()
    staticfiles = auto()
    textanalyzer = auto()
    timelinepreviews = auto()
    transcription_ibmwatson = auto()
    userdirectory_endpoint_UserEndpoint = auto()
    userdirectory_roles = auto()
    userdirectory_users = auto()
    usertracking = auto()
    videoeditor = auto()
    videosegmenter = auto()
    waveform = auto()
    workflow = auto()

    def to_name(self, prefix="org.opencastproject."):
        return prefix + self.name.replace("_", ".")


class ServiceApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None, **_kwargs):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/services"

    def get_active_jobs(self, **kwargs) -> dict:
        url = self.base_url + "/activeJobs.json"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.json()
        if res is not None:
            raise Exception(str(res))
        raise Exception("Could not get active jobs!")

        # TODO job children (in job)
        # GET /job/{id}.json
        # and GET /job/{id}/children.json

    def get_available(self, service_type: ServiceType, **kwargs) -> List[Service]:
        services_res = []
        if isinstance(service_type, ServiceType):
            service_type = service_type.to_name()
        else:
            if "org.opencastproject." not in service_type:
                service_type = "org.opencastproject." + service_type
        url = self.base_url + "/available.json"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            params={"serviceType": service_type},
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            services = res.json()["services"]
            pprint(services)
            if isinstance(services["service"], list):
                for s in services["service"]:
                    services_res.append(Service(s))
            else:
                services_res.append(Service(services["service"]))
            return services_res
        raise Exception("Could not get available services!")

    def get_count(self, **kwargs) -> int:
        url = self.base_url + "/count"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.json()
        raise Exception("Could not service count!")

    def get_current_load(self, **kwargs) -> int:
        url = self.base_url + "/currentload"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return xmltodict.parse(res.content)
        raise Exception("Could not current load!")

    def get_health(self, **kwargs) -> int:
        url = self.base_url + "/health.json"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.json()
        raise Exception("Could not get health!")

    def get_hosts(self, **kwargs) -> List[Host]:
        res_hosts = []
        url = self.base_url + "/hosts.json"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            hosts = res.json()["hosts"]
            if isinstance(hosts["host"], dict):
                res_hosts.append(Host(hosts["host"]))
                return res_hosts
            for h in hosts["host"]:
                res_hosts.append(Host(h))
            return res_hosts
        raise Exception("Could not get health!")

    def get_max_concurrent_jobs(self, **kwargs) -> int:
        url = self.base_url + "/maxconcurrentjobs"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.content
        raise Exception("Could not get max concurrent jobs!")

    def get_max_load(self, **kwargs) -> int:
        url = self.base_url + "/maxload"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.content
        raise Exception("Could not get max load!")

    def get_own_load(self, **kwargs) -> float:
        url = self.base_url + "/ownload"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return float(res.content)
        raise Exception("Could not get own load!")

    def get_services(
        self, service_type: ServiceType = None, host: str = None, **kwargs
    ):
        if "service_type" in kwargs and service_type is None:
            service_type = kwargs.get("service_type")
        if "host" in kwargs and host is None:
            host = kwargs.get("host")
        if isinstance(service_type, ServiceType):
            service_type = service_type.to_name()
        else:
            if service_type is not None and "org.opencastproject." not in service_type:
                service_type = "org.opencastproject." + service_type
        params = {}
        if service_type is not None:
            params["serviceType"] = service_type
        if host is not None:
            params["host"] = host
        url = self.base_url + "/services.json"
        res = requests.get(
            url, auth=HTTPBasicAuth(self.user, self.password), params=params, **kwargs
        )
        if res.ok:
            return res.json()
        raise Exception("Could not get services!")

    def get_service_warnings(self, **kwargs) -> int:
        url = self.base_url + "/servicewarnings"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return int(res.content)
        raise Exception("Could not get service warnings!")

    def get_statistics(self, **kwargs) -> str:
        url = self.base_url + "/statistics.json"
        res = requests.get(
            url,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs
        )
        if res.ok:
            return res.json()
        raise Exception("Could not get statistics!")

    def create_job(self):
        pass

    def delete_job(self):
        pass


def main():
    api = ServiceApi()
    api = ServiceApi(server_url="http://opencast-dev.bibliothek.kit.edu:8080")
    api = ServiceApi(
        server_url="http://localhost:8080", user="admin", password="opencast"
    )
    # pprint(api.get_active_jobs())
    # services = api.get_available("ingest")

    services = api.get_available(ServiceType.workflow)
    print(services)
    api = services.pop().get_url()

    print(api)
    exit()

    # services = api.get_available(ServiceType.distribution_aws_s3)
    # services = api.get_available(ServiceType.kernel_bundleinfo)
    # pprint(services)
    for s in services:
        print(s.get_url())
    service = services[randrange(0, len(services))]
    logger.info("Selecting ingest service to use: " + str(service))

    url = service.get_url() + "/createMediaPackage"
    print(url)
    # res = requests.get(url, auth=HTTPDigestAuth("admin", "opencast"), headers={'X-Requested-Auth': 'Digest'})
    # res = requests.get(url)
    res = requests.get(
        url,
        auth=HTTPDigestAuth("opencast_system_account", "CHANGE_ME"),
        headers={"X-Requested-Auth": "Digest"},
    )
    if res.ok:
        print(res.content)
        print(res)
    else:
        print(res)

    exit()
    # pprint(api.get_services(host='http://opencast-dev.bibliothek.kit.edu:8080'))

    print(api.get_current_load())
    pprint(api.get_health())
    hosts = api.get_hosts()
    print("hosts: " + str(hosts))
    for h in hosts:
        print(h.get_address())
        pprint(h.get_memory())

    pprint(api.get_max_concurrent_jobs())
    pprint(api.get_max_load())
    pprint(api.get_own_load())
    pprint(api.get_service_warnings())
    pprint(api.get_statistics())


if __name__ == "__main__":
    main()
