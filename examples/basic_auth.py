import asyncio
import os

from aiohttp import ClientSession

from poaurk import OAuthCred, PlurkOAuth


async def main() -> None:
    """Program main entry."""
    oauth_cred = OAuthCred(
        os.environ["POAURK_TEST_KEY"], os.environ["POAURK_TEST_SECRET"], None, None
    )

    async with ClientSession() as session:
        plurk_oauth = PlurkOAuth(oauth_cred, session)

        # Step 1: Get request token
        await plurk_oauth.get_request_token()
        print(f"Request Token: {oauth_cred.token}")
        print(f"Token Secret: {oauth_cred.token_secret}")

        # Step 2: Get verification URL
        verifier_url = plurk_oauth.get_verifier_url()
        print(f"Visit this URL to authorize: {verifier_url}")

        # Step 3: Get user input for verifier code
        verifier_code = await plurk_oauth.get_verifier()

        # Step 4: Get access token
        await plurk_oauth.get_access_token(verifier_code)
        print(f"Access Token: {oauth_cred.token}")
        print(f"Access Token Secret: {oauth_cred.token_secret}")

        # Step 5: Test request
        app_users_me = await plurk_oauth.request("/APP/Users/me")
        print(app_users_me)


if __name__ == "__main__":
    asyncio.run(main())
