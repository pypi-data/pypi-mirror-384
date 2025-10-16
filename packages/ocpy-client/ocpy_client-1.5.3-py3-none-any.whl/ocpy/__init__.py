# -*- coding: utf-8 -*-
"""Copyright (c) 2018. Tobias Kurze
This module demonstrates documentation as specified by the `Google Python
Style Guide`_. Docstrings may extend over multiple lines. Sections are created
with a section header and a colon followed by a block of indented text.

Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::

        $ python example_google.py

Section breaks are created by resuming unindented text. Section breaks
are also implicitly created anytime a new section starts.

Attributes:
    module_level_variable1 (int): Module level variables may be documented in
        either the ``Attributes`` section of the module docstring, or in an
        inline docstring immediately following the variable.

        Either form is acceptable, but the two should not be mixed. Choose
        one convention to document module level variables and be consistent
        with it.

Todo:
    * For module TODOs
    * You have to also use ``sphinx.ext.todo`` extension

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html
"""
import os
from typing import Optional

import yaml
from loguru import logger
from requests import Response
from dotenv import load_dotenv

NAME = "ocpy"
CONNECTION_CONFIG = None


def get_connection_config():
    """Returns the connection parameters, that are being used by all get_*_api_client methods."""
    global CONNECTION_CONFIG  # pylint: disable=global-statement
    if CONNECTION_CONFIG is None:
        logger.warning(
            "connection_config is not set – please call >setup_connection_config< before using the API client(s)"
        )
        logger.info("trying to setup connection_config from environment...")
        CONNECTION_CONFIG = setup_connection_config_from_env()
    return CONNECTION_CONFIG


def setup_connection_config(
    user: str = "admin",
    password: str = None,
    server_url: str = "http://opencast.ubka.uni-karlsruhe.de:8080",
    digest_user: str = "opencast_system_account",
    digest_password: str = None,
):
    """Sets up the connection parameters, that are being used by all get_*_api_client methods.

    Args:
        user (str): username to use for the connection
        password (str): password to use for the connection
        server_url (str): base server_url (incl. port if non standard) to use for the connection
        digest_user (str): username for digest authentication – needed for certain APIs / tasks
        digest_password (str): password of user for digest authentication

    Returns:
        dict: the connection_config dictionary
    """
    global CONNECTION_CONFIG  # pylint: disable=global-statement
    if server_url[-1] == "/":
        server_url = server_url[0:-1]
    CONNECTION_CONFIG = {
        "user": user,
        "password": password,
        "server_url": server_url,
        "digest_user": digest_user,
        "digest_password": digest_password,
    }
    return CONNECTION_CONFIG


def setup_connection_config_from_yaml_file(config_yaml: str, encoding="utf-8") -> dict:
    """Setup the connection parameters from a provided config file in yaml format.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        config_yaml (str): Config file path

    Returns:
        dict: the connection_config dictionary

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
    try:
        with open(config_yaml, "r", encoding=encoding) as stream:
            try:
                return setup_connection_config(**yaml.safe_load(stream))
            except yaml.YAMLError:
                logger.exception("Invalid yaml file")
            except TypeError:
                logger.exception(
                    "Invalid settings in YAML file – user, password, server_url must be specified"
                )
    except FileNotFoundError:
        logger.exception(f"Specified file {config_yaml} not found!")


def setup_connection_config_from_env(read_dotenv: bool = True) -> dict:
    """Setup the connection parameters from environment variables."""
    if read_dotenv:
        load_dotenv()

    oc_user = os.getenv("OC_USER", "admin")
    oc_password = os.getenv("OC_PASSWORD", os.getenv("OC_PW", None))
    oc_url = os.getenv("OC_URL", os.getenv("OC_SERVER", None))
    oc_digest_user = os.getenv("OC_DIGEST_USER", "opencast_system_account")
    oc_digest_user_password = os.getenv("OC_DIGEST_USER_PASSWORD", None)

    if oc_password is None or oc_url is None:
        raise ValueError("OC_PASSWORD or OC_URL is not set")
    if oc_digest_user_password is None:
        logger.warning("OC_DIGEST_USER_PASSWORD is not set")

    return setup_connection_config(
        user=oc_user,
        password=oc_password,
        server_url=oc_url,
        digest_user=oc_digest_user,
        digest_password=oc_digest_user_password,
    )


class OcPyException(Exception):
    """Base class for exceptions in this module."""


class OcPyRequestException(OcPyException):
    """Exception raised for errors in this module linked to requests."""

    def __init__(
        self, message, code: Optional[int] = None, response: Optional[Response] = None
    ):
        super().__init__(message)
        self.code = code
        self.response = response
        if response is not None:
            if self.code is None:
                self.code = response.status_code

    def get_code(self) -> Optional[int]:
        """Return the exception code."""
        return self.code

    def is_opencast_error(self) -> bool:
        """Return True if the exception is an error returned by Opencast (http: 500)."""
        return self.code == 500

    def get_response(self) -> Optional[Response]:
        """Return the response object."""
        return self.response
