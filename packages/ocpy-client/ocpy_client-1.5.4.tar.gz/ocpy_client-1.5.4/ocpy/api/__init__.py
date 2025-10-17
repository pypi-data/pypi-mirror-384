import yaml
from random import choice
from loguru import logger

from ocpy.api.service import ServiceApi, ServiceType
from ocpy.api.ingest import IngestApi
from ocpy.api.assets import AssetsApi
from ocpy.api.external.base import BaseApi
from ocpy.api.external.agents import AgentsApi
from ocpy.api.external.events import EventsApi
from ocpy.api.external.series import SeriesApi
from ocpy.api.external.workflows import WorkflowsApi
from ocpy.api.recordings import RecordingsApi

# from .series import GroupsApi
# from .series import SecurityApi

from ocpy import get_connection_config


def get_base_api_client() -> BaseApi:
    connection_config = get_connection_config()
    if connection_config is None:
        raise Exception(
            "please call >setup_connection_config< before using the API client(s)"
        )
    else:
        return BaseApi(**connection_config)


def get_agents_api_client() -> AgentsApi:
    connection_config = get_connection_config()
    if connection_config is None:
        raise Exception(
            "please call >setup_connection_config< before using the API client(s)"
        )
    else:
        return AgentsApi(**connection_config)


def get_events_api_client() -> EventsApi:
    connection_config = get_connection_config()
    if connection_config is None:
        raise Exception(
            "please call >setup_connection_config< before using the API client(s)"
        )
    else:
        return EventsApi(**connection_config)


def get_series_api_client() -> SeriesApi:
    connection_config = get_connection_config()
    if connection_config is None:
        raise Exception(
            "please call >setup_connection_config< before using the API client(s)"
        )
    else:
        return SeriesApi(**connection_config)


def get_workflows_api_client() -> WorkflowsApi:
    connection_config = get_connection_config()
    if connection_config is None:
        raise Exception(
            "please call >setup_connection_config< before using the API client(s)"
        )
    else:
        return WorkflowsApi(**connection_config)


def get_recordings_api_client() -> RecordingsApi:
    connection_config = get_connection_config()
    if connection_config is None:
        raise Exception(
            "please call >setup_connection_config< before using the API client(s)"
        )
    else:
        return RecordingsApi(**connection_config)


def get_service_api_client() -> ServiceApi:
    connection_config = get_connection_config()
    if connection_config is None:
        raise Exception(
            "please call >setup_connection_config< before using the API client(s)"
        )
    else:
        return ServiceApi(**connection_config)


def get_ingest_api_client() -> IngestApi:
    connection_config = get_connection_config()
    if connection_config is None:
        raise Exception(
            "please call >setup_connection_config< before using the API client(s)"
        )
    else:
        service_api = get_service_api_client()
        ingest_service = choice(service_api.get_available(ServiceType.ingest))
        return IngestApi(ingest_service.get_url(), **connection_config)

def get_assets_api_client() -> AssetsApi:
    connection_config = get_connection_config()
    if connection_config is None:
        raise Exception(
            "please call >setup_connection_config< before using the API client(s)"
        )
    else:
        return AssetsApi(**connection_config)

