"""Module: plurk_oauth_test.py.

This module contains unit tests for the Plurk OAuth functionality.
"""

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession
from poaurk import OauthCred, PlurkOAuth


@pytest.fixture
def oauth_cred():
    """Fixture function to provide OAuth credentials for testing.

    Returns
    -------
        OauthCred: An instance of OauthCred with dummy customer key and customer secret.

    """
    return OauthCred("customer_key", "customer_secret", None, None)


@pytest.fixture
async def session():
    """Fixture function to provide an async ClientSession for testing.

    Yields
    ------
        ClientSession: An asynchronous HTTP client session.

    """
    async with ClientSession() as session:
        yield session


@pytest.mark.asyncio
async def test_get_request_token(oauth_cred, session):
    """Test function for the get_request_token method of PlurkOAuth.

    Args:
    ----
        oauth_cred (OauthCred): OAuth credentials.
        session (ClientSession): An asynchronous HTTP client session.

    """
    with patch.object(PlurkOAuth, "request", new_callable=AsyncMock) as mocked_request:
        mocked_request.return_value = {
            "oauth_token": "fake_token",
            "oauth_token_secret": "fake_token_secret",
        }
        plurk_oauth = PlurkOAuth(oauth_cred, session)
        await plurk_oauth.get_request_token()
        assert oauth_cred.token == "fake_token"
        assert oauth_cred.token_secret == "fake_token_secret"
        mocked_request.assert_called_once_with(plurk_oauth.REQUEST_TOKEN_URL)


@pytest.mark.asyncio
async def test_get_verifier(oauth_cred, session):
    """Test function for the get_verifier method of PlurkOAuth.

    Args:
    ----
        oauth_cred (OauthCred): OAuth credentials.
        session (ClientSession): An asynchronous HTTP client session.

    """
    plurk_oauth = PlurkOAuth(oauth_cred, session)
    oauth_cred.token = "fake_token"
    oauth_cred.token_secret = "fake_token_secret"
    with patch("builtins.input", side_effect=["123456", "y"]):
        with patch("builtins.print") as mocked_print:
            verifier = plurk_oauth.get_verifier()
            assert verifier == "123456"
            assert mocked_print.call_count == 2  # noqa: PLR2004


@pytest.mark.asyncio
async def test_get_verifier_url(oauth_cred, session):
    """Test function for the get_verifier_url method of PlurkOAuth.

    Args:
    ----
        oauth_cred (OauthCred): OAuth credentials.
        session (ClientSession): An asynchronous HTTP client session.

    """
    plurk_oauth = PlurkOAuth(oauth_cred, session)
    with pytest.raises(Exception):
        plurk_oauth.get_verifier_url()
    oauth_cred.token = "fake_token"
    oauth_cred.token_secret = "fake_token_secret"
    assert (
        plurk_oauth.get_verifier_url()
        == f"{plurk_oauth.BASE_URL}{plurk_oauth.AUTHORIZATION_URL}?oauth_token={oauth_cred.token}"
    )


@pytest.mark.asyncio
async def test_get_access_token(oauth_cred, session):
    """Test function for the get_access_token method of PlurkOAuth.

    Args:
    ----
        oauth_cred (OauthCred): OAuth credentials.
        session (ClientSession): An asynchronous HTTP client session.

    """
    with patch.object(PlurkOAuth, "request", new_callable=AsyncMock) as mocked_request:
        mocked_request.return_value = {
            "oauth_token": "fake_access_token",
            "oauth_token_secret": "fake_access_token_secret",
        }
        plurk_oauth = PlurkOAuth(oauth_cred, session)
        await plurk_oauth.get_access_token("fake_verifier")
        assert oauth_cred.token == "fake_access_token"
        assert oauth_cred.token_secret == "fake_access_token_secret"
        mocked_request.assert_called_once_with(
            plurk_oauth.ACCESS_TOKEN_URL, data={"verifier": "fake_verifier"}
        )
