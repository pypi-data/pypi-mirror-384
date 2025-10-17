#  Copyright (c) 2019. Tobias Kurze
import os
from dotenv import load_dotenv
from loguru import logger

import pytest

from ocpy import setup_connection_config_from_yaml_file, get_connection_config
from ocpy.api import get_events_api_client, get_series_api_client
from ocpy.api.search import SearchApi
from ocpy.api.admin_ui.service import AdminServiceApi
from ocpy.api.sign import SigningApi
import tests

print("tada")

load_dotenv()  # alternative: to load local env


@pytest.fixture(scope="session", autouse=True)
def setup_oc_connection():
    # prepare something ahead of all tests
    print("setting up connection_config")
    setup_connection_config_from_yaml_file(os.path.abspath("tests/.test.creds.yml"))

    tests.EV_API = get_events_api_client()
    tests.SE_API = get_series_api_client()
    tests.SERVICE_API = AdminServiceApi()
    con_config = get_connection_config()
    if con_config is not None:
        tests.SIGN_API = SigningApi(**con_config)
    server = os.getenv("OC_PORTAL_SERVER")
    if server is None:
        logger.warning("OC_PORTAL_SERVER not set in environment")
    else:
        tests.SEARCH_API = SearchApi(
            user=os.getenv("OC_USER"), password=os.getenv("OC_PW"), server_url=server
        )


# setup_oc_connection()
