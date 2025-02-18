"""Module: plurk_oauth_test.py.

This module contains unit tests for the Plurk OAuth functionality.
"""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from aiohttp import ClientSession

from poaurk import CliUserInteraction, OAuthCred, PlurkOAuth


@pytest.fixture
def oauth_cred():
    """Provide OAuth credentials for testing."""
    return OAuthCred("customer_key", "customer_secret", None, None)


@pytest_asyncio.fixture
async def session():
    """Provide an async ClientSession for testing."""
    async with ClientSession() as session:
        yield session


@pytest.fixture
def plurk_oauth(oauth_cred, session):
    """Fixture to provide PlurkOAuth instance."""
    return PlurkOAuth(oauth_cred, session)


@pytest.mark.asyncio
async def test_get_request_token(plurk_oauth, oauth_cred):
    """Test get_request_token method."""
    with patch.object(PlurkOAuth, "request", new_callable=AsyncMock) as mocked_request:
        mocked_request.return_value = {
            "oauth_token": "fake_token",
            "oauth_token_secret": "fake_token_secret",
        }
        await plurk_oauth.get_request_token()
        assert oauth_cred.token == "fake_token"
        assert oauth_cred.token_secret == "fake_token_secret"
        mocked_request.assert_called_once_with(plurk_oauth._request_token_url)


@pytest.mark.asyncio
async def test_get_verifier(plurk_oauth, oauth_cred):
    """Test get_verifier method."""
    oauth_cred.token = "fake_token"
    oauth_cred.token_secret = "fake_token_secret"

    with patch.object(
        CliUserInteraction, "get_verification_code", new_callable=AsyncMock
    ) as mock_get_verifier:
        mock_get_verifier.return_value = "123456"
        verifier = await plurk_oauth.get_verifier()
        assert verifier == "123456"
        mock_get_verifier.assert_called_once()


@pytest.mark.asyncio
async def test_get_verifier_url(plurk_oauth, oauth_cred):
    """Test get_verifier_url method."""
    with pytest.raises(Exception):
        plurk_oauth.get_verifier_url()
    oauth_cred.token = "fake_token"
    oauth_cred.token_secret = "fake_token_secret"
    assert (
        plurk_oauth.get_verifier_url()
        == f"{plurk_oauth.base_url}{plurk_oauth._authorization_url}?oauth_token={oauth_cred.token}"
    )


@pytest.mark.asyncio
async def test_get_access_token(plurk_oauth, oauth_cred):
    """Test get_access_token method."""
    with patch.object(PlurkOAuth, "request", new_callable=AsyncMock) as mocked_request:
        mocked_request.return_value = {
            "oauth_token": "fake_access_token",
            "oauth_token_secret": "fake_access_token_secret",
        }
        await plurk_oauth.get_access_token("fake_verifier")
        assert oauth_cred.token == "fake_access_token"
        assert oauth_cred.token_secret == "fake_access_token_secret"
        mocked_request.assert_called_once_with(
            plurk_oauth._access_token_url, data={"verifier": "fake_verifier"}
        )
