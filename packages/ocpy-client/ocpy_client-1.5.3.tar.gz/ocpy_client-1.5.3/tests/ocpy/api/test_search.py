#  Copyright (c) 2023. Tobias Kurze
"""Search API tests."""
import pytest
import tests

from loguru import logger


@pytest.mark.usefixtures("setup_oc_connection")
class TestSearchApiClass:
    """Test the search API."""

    def test_search_api_episodes(self):
        """Get episodes from search API."""
        episodes = tests.SEARCH_API.get_episode(limit=1)
        logger.info(episodes)
        assert isinstance(episodes, dict)
        # test_acl = []

    @pytest.mark.skip(
        reason="deprecated call / format=xml not supported anymore or differently"
    )
    def test_search_api_episodes_xml(self):
        """Get episodes from search API in xml."""
        episodes = tests.SEARCH_API.get_episode(limit=1, format="xml")
        logger.info(episodes)
        assert isinstance(episodes, str)
        # test_acl = []

    def test_search_api_lucene(self):
        """Use lucene from search API."""
        episodes = tests.SEARCH_API.get_lucene(limit=1)
        logger.info(episodes)
        assert isinstance(episodes, dict)
        # test_acl = []

    def test_search_api_series(self):
        """Get series from search API."""
        episodes = tests.SEARCH_API.get_series(limit=1)
        logger.info(episodes)
        assert len(episodes) == 1
        # test_acl = []
