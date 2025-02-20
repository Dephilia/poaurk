"""Provide basic OAuth1 operations for Plurk API 2.0.

This module facilitates OAuth1 authentication for accessing the Plurk API 2.0.
It includes functionality for obtaining request tokens, authorizing access, and
retrieving access tokens.

Example usage:
    async with aiohttp.ClientSession() as session:
        cred = OAuthCred(
            customer_key="your_key",
            customer_secret="your_secret",
            token=None,
            token_secret=None
        )
        client = PlurkOAuth(cred, session)
        await client.authorize()
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urljoin

import aiofiles
import aiohttp
import oauthlib.oauth1
from aiohttp import FormData

# Set up logging
logger = logging.getLogger(__name__)


class PlurkOAuthError(Exception):
    """Base exception for Plurk OAuth errors."""

    pass


class PlurkNetworkError(PlurkOAuthError):
    """Raised when network communication fails."""

    pass


class PlurkAuthorizationError(PlurkOAuthError):
    """Raised when authorization fails."""

    pass


@dataclass
class OAuthCred:
    """OAuth Credentials Dataclass.

    Attributes
    ----------
    customer_key : str
        The consumer key provided by Plurk.
    customer_secret : str
        The consumer secret provided by Plurk.
    token : Optional[str]
        The OAuth token, initially None.
    token_secret : Optional[str]
        The OAuth token secret, initially None.

    """

    customer_key: str
    customer_secret: str
    token: str | None = None
    token_secret: str | None = None

    def to_client(self) -> oauthlib.oauth1.Client:
        """Convert OAuth credentials to OAuth client.

        Returns
        -------
        oauthlib.oauth1.Client
            Configured OAuth client ready for making authenticated requests.

        """
        return oauthlib.oauth1.Client(
            client_key=self.customer_key,
            client_secret=self.customer_secret,
            resource_owner_key=self.token,
            resource_owner_secret=self.token_secret,
        )


class UserInteraction(ABC):
    """Abstract base class for user interaction during OAuth flow."""

    @staticmethod
    @abstractmethod
    async def get_verification_code(url: str) -> str:
        """Get verification code from user.

        Parameters
        ----------
        url : str
            Authorization URL to be displayed to user.

        Returns
        -------
        str
            Verification code entered by user.

        """
        pass


class CliUserInteraction(UserInteraction):
    """Command-line implementation of user interaction."""

    @staticmethod
    async def get_verification_code(url: str) -> str:
        """Get verification code via command line.

        Parameters
        ----------
        url : str
            Authorization URL to be displayed to user.

        Returns
        -------
        str
            Verification code entered by user.

        Notes
        -----
        Uses asyncio.to_thread to prevent blocking the event loop.

        """
        print("Open the following URL and authorize it.")
        print(url)

        while True:
            verifier = await asyncio.to_thread(input, "Input the verification number: ")
            verified = await asyncio.to_thread(input, "Are you sure? (y/n) ")

            if verified.lower() == "y" and verifier:
                return verifier

            if verified.lower() != "n":
                print("Please answer 'y' or 'n'")


class PlurkOAuth:
    """Plurk OAuth Client.

    Handles OAuth authentication flow for Plurk API 2.0.
    """

    def __init__(
        self,
        cred: OAuthCred,
        session: aiohttp.ClientSession,
        user_interaction: UserInteraction | None = None,
        timeout: int = 60,
        base_url: str = "https://www.plurk.com/",
    ) -> None:
        """Initialize PlurkOAuth.

        Parameters
        ----------
        cred : OAuthCred
            OAuth credentials
        session : aiohttp.ClientSession
            Aiohttp client session
        user_interaction : Optional[UserInteraction]
            Interface for user interaction, defaults to CliUserInteraction
        timeout : int
            Request timeout in seconds
        base_url : str
            Base URL for Plurk API

        """
        self.cred = cred
        self.session = session
        self.user_interaction = user_interaction or CliUserInteraction()
        self.timeout = timeout
        self.base_url = base_url

        # API endpoints
        self._request_token_url = "OAuth/request_token"
        self._authorization_url = "OAuth/authorize"
        self._access_token_url = "OAuth/access_token"

    @staticmethod
    @asynccontextmanager
    async def _handle_request_errors():
        """Context manager for handling request errors.

        Raises
        ------
        PlurkNetworkError
            When network communication fails
        PlurkAuthorizationError
            When authorization fails
        PlurkOAuthError
            For other OAuth-related errors

        """
        try:
            yield
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise PlurkNetworkError(f"Failed to communicate with Plurk: {e}") from e
        except oauthlib.oauth1.OAuth1Error as e:
            logger.error(f"OAuth error: {e}")
            raise PlurkAuthorizationError(f"OAuth authorization failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise PlurkOAuthError(f"Unexpected error: {e}") from e

    async def authorize(self, access_token: tuple[str, str] | None = None) -> None:
        """Authorize access to Plurk API.

        Parameters
        ----------
        access_token : Optional[Tuple[str, str]]
            Tuple of (token, token_secret) if already available

        """
        async with self._handle_request_errors():
            if access_token:
                self.cred.token, self.cred.token_secret = access_token
            else:
                await self._complete_oauth_flow()

    async def _complete_oauth_flow(self) -> None:
        """Complete the OAuth flow by getting request token, verifier, and access token."""
        await self.get_request_token()
        verifier = await self.get_verifier()
        await self.get_access_token(verifier)

    async def request(
        self,
        method: str,
        data: dict[str, str] | None = None,
        files: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the Plurk API.

        Parameters
        ----------
        method : str
            The API endpoint
        data : Optional[Dict[str, str]]
            Request data
        files : Optional[Dict[str, str]]
            Files to upload

        Returns
        -------
        Dict[str, Any]
            Response data

        """
        async with self._handle_request_errors():
            client = self.cred.to_client()
            uri = urljoin(self.base_url, method)

            # Handle verifier in data
            if data and "verifier" in data:
                client.verifier = data.pop("verifier")

            # Prepare request data and headers
            headers, body = await self._prepare_request_data(data, files)

            # Sign the request
            uri, headers, body = client.sign(
                uri=uri,
                http_method="POST",
                body=body if body else {},
                headers=headers,
            )

            # Make the request
            async with self.session.post(
                uri,
                data=body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                response.raise_for_status()
                return await self._parse_response(response)

    @staticmethod
    async def _prepare_request_data(
        data: dict[str, str] | None, files: dict[str, str] | None
    ) -> tuple[dict[str, str], Any]:
        """Prepare request data and headers.

        Parameters
        ----------
        data : Optional[Dict[str, str]]
            Request data
        files : Optional[Dict[str, str]]
            Files to upload

        Returns
        -------
        Tuple[Dict[str, str], Any]
            Headers and body for the request

        """
        if files:
            headers = {}
            form_data = FormData()
            for key, filepath in files.items():
                async with aiofiles.open(filepath, mode="rb") as f:
                    form_data.add_field(key, f)
            if data:
                for key, value in data.items():
                    form_data.add_field(key, value)
            return headers, form_data

        return ({"Content-Type": "application/x-www-form-urlencoded"}, data)

    @staticmethod
    async def _parse_response(response: aiohttp.ClientResponse) -> dict[str, Any]:
        """Parse API response based on content type.

        Parameters
        ----------
        response : aiohttp.ClientResponse
            Response from Plurk API

        Returns
        -------
        Dict[str, Any]
            Parsed response data

        Raises
        ------
        TypeError
            When content type is not supported

        """
        if response.content_type == "application/json":
            return await response.json()
        if response.content_type == "text/html":
            return dict(parse_qsl(await response.text()))
        raise TypeError(f"Invalid content type: {response.content_type}")

    async def get_request_token(self) -> None:
        """Get OAuth request token."""
        self.cred.token = None
        self.cred.token_secret = None

        response = await self.request(self._request_token_url)
        self.cred.token = response["oauth_token"]
        self.cred.token_secret = response["oauth_token_secret"]

    def get_verifier_url(self) -> str:
        """Get verifier URL.

        Returns
        -------
        str
            URL for user authorization

        Raises
        ------
        PlurkAuthorizationError
            If tokens are not available

        """
        if not self.cred.token or not self.cred.token_secret:
            raise PlurkAuthorizationError("Please request a token first")
        return f"{self.base_url}{self._authorization_url}?oauth_token={self.cred.token}"

    async def get_verifier(self) -> str:
        """Get OAuth verifier code through user interaction.

        Returns
        -------
        str
            OAuth verifier code

        """
        return await self.user_interaction.get_verification_code(self.get_verifier_url())

    async def get_access_token(self, verifier: str) -> None:
        """Get OAuth access token using verifier.

        Parameters
        ----------
        verifier : str
            OAuth verifier code

        """
        response = await self.request(self._access_token_url, data={"verifier": verifier})
        self.cred.token = response["oauth_token"]
        self.cred.token_secret = response["oauth_token_secret"]
