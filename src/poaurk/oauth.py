"""Provide basic OAuth1 operations for Plurk API 2.0.

This module facilitates OAuth1 authentication for accessing the Plurk API 2.0. It includes functionality for obtaining request tokens, authorizing access, and retrieving access tokens.

Attributes
----------
    BASE_URL (str): The base URL for Plurk API endpoints.
    REQUEST_TOKEN_URL (str): The endpoint for requesting OAuth request tokens.
    AUTHORIZATION_URL (str): The endpoint for user authorization.
    ACCESS_TOKEN_URL (str): The endpoint for exchanging request tokens for access tokens.

"""

from dataclasses import dataclass
from urllib.parse import parse_qsl, urljoin

import aiohttp
import oauthlib.oauth1


@dataclass
class OauthCred:
    """OAuth Credentials Dataclass.

    Attributes
    ----------
        customer_key (str): The consumer key.
        customer_secret (str): The consumer secret.
        token (str | None): The OAuth token.
        token_secret (str | None): The OAuth token secret.

    """

    customer_key: str
    customer_secret: str
    token: str | None
    token_secret: str | None

    def to_client(self) -> oauthlib.oauth1.Client:
        """Convert OAuth credentials to OAuth client.

        Returns
        -------
            oauthlib.oauth1.Client: OAuth client.

        """
        return oauthlib.oauth1.Client(
            client_key=self.customer_key,
            client_secret=self.customer_secret,
            resource_owner_key=self.token,
            resource_owner_secret=self.token_secret,
        )


class PlurkOAuth:
    """Plurk OAuth Client.

    Attributes
    ----------
        BASE_URL (str): The base URL for Plurk API endpoints.
        REQUEST_TOKEN_URL (str): The endpoint for requesting OAuth request tokens.
        AUTHORIZATION_URL (str): The endpoint for user authorization.
        ACCESS_TOKEN_URL (str): The endpoint for exchanging request tokens for access tokens.

    """

    BASE_URL: str = "https://www.plurk.com/"
    REQUEST_TOKEN_URL: str = "/OAuth/request_token"
    AUTHORIZATION_URL: str = "/OAuth/authorize"
    ACCESS_TOKEN_URL: str = "/OAuth/access_token"

    def __init__(self, cred: OauthCred, session: aiohttp.ClientSession):
        """Initialize PlurkOAuth.

        Args:
        ----
            cred (OauthCred): OAuth credentials.
            session (aiohttp.ClientSession): Aiohttp client session.

        """
        self.cred = cred
        self.session = session

    async def authorize(self, access_token: tuple[str, str] | None = None):
        """Authorize access.

        Args:
        ----
            access_token (tuple[str, str] | None): Access token and secret.

        Returns:
        -------
            None

        """
        if access_token:
            self.cred.token, self.cred.token_secret = access_token
        else:
            await self.get_request_token()
            verifier = self.get_verifier()
            await self.get_access_token(verifier)

    async def request(
        self,
        method: str,
        data: dict[str, str] | None = None,
        files: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Make a request to the Plurk API.

        Args:
        ----
            method (str): The API endpoint.
            data (dict[str, str] | None): Request data.
            files (dict[str, str] | None): Files to upload.

        Returns:
        -------
            dict[str, str]: Response data.

        """
        client = self.cred.to_client()

        # Verifier cannot take as data
        if data and "verifier" in data:
            client.verifier = data["verifier"]
            data.pop("verifier")

        uri = urljoin(self.BASE_URL, method)
        http_method = "POST"

        # Handle files
        if files:
            headers = {}
            form_data = aiohttp.FormData()
            for key, value in files.items():
                form_data.add_field(key, open(value, "rb"))
            if data:
                for key, value in data.items():
                    form_data.add_field(key, value)
        else:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            form_data = data

        uri, headers, body = client.sign(
            uri=uri,
            http_method=http_method,
            body=form_data if form_data else {},
            headers=headers,
        )

        async with self.session.post(
            uri,
            data=body,
            headers=headers,
            raise_for_status=True,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as r:
            if r.content_type == "application/json":
                return await r.json()
            if r.content_type == "text/html":
                return dict(parse_qsl(await r.text()))
            raise TypeError("Invalid content type:", r.content_type)

    async def get_request_token(self) -> None:
        """Get OAuth request token.

        Returns
        -------
            None

        """
        # Clear token
        self.cred.token = None
        self.cred.token_secret = None

        r = await self.request(self.REQUEST_TOKEN_URL)
        self.cred.token = r["oauth_token"]
        self.cred.token_secret = r["oauth_token_secret"]

    def get_verifier(self) -> str:
        """Get OAuth verifier.

        Returns
        -------
            str: OAuth verifier.

        """
        print("Open the following URL and authorize it.")
        print(self.get_verifier_url())

        verified: str = "n"
        verifier: str | None = None
        while verified.lower() == "n":
            verifier = input("Input the verification number: ")
            verified = input("Are you sure? (y/n) ")
        if not verifier:
            raise ValueError("Unavailable verifier.")
        return verifier

    def get_verifier_url(self) -> str:
        """Get verifier URL.

        Returns
        -------
            str: Verifier URL.

        """
        if self.cred.token is None or self.cred.token_secret is None:
            raise Exception("Please request a token first")
        return f"{self.BASE_URL}{self.AUTHORIZATION_URL}?oauth_token={self.cred.token}"

    async def get_access_token(self, verifier: str) -> None:
        """Get OAuth access token by verifier.

        Args:
        ----
            verifier (str): OAuth verifier.

        Returns:
        -------
            None

        """
        r = await self.request(self.ACCESS_TOKEN_URL, data={"verifier": verifier})
        self.cred.token = r["oauth_token"]
        self.cred.token_secret = r["oauth_token_secret"]
