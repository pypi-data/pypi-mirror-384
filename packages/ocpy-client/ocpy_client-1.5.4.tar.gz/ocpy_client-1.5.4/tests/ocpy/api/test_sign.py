#  Copyright (c) 2023. Tobias Kurze
"""Search API tests."""
import pytest
import tests

from loguru import logger

TEST_URL = "https://oc-alpha-delivery-1.bibliothek.kit.edu/staticfiles/mh_default_org/engage-player/ea248461-b144-4349-9c12-da22633c14d4/8e25b7d9-b501-4e21-a74e-b956d31fccdc/CS_10_50_Bauingenieu_gro_er_hs_test_reihe_20230119_160500_S1R1.mp4"


@pytest.mark.usefixtures("setup_oc_connection")
class TestSignApiClass:
    """Test the search API."""

    def test_sign_api_accepts_url(self):
        """Get episodes from search API."""
        accepts = tests.SIGN_API.accepts(TEST_URL)
        logger.info(accepts)
        assert isinstance(accepts, bool)

    def test_sign_api_sign_url(self):
        """Get episodes from search API."""
        url = tests.SIGN_API.sign(TEST_URL)
        logger.info(url)
        assert isinstance(url, str)
