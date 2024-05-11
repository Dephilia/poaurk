# poaurk

Light plurk + Oauth Library

# Installation

```
pip install poaurk
```

# Example

## Authorize and get profile

```python
import asyncio

import aiohttp
from poaurk import OauthCred, PlurkOAuth

cred = OauthCred(customer_key='your key from plurk',
                 customer_secret='your secret from plurk',
                 token='optional token',
                 token_secret='optional token secret'
                 )


async def main():
    async with aiohttp.ClientSession() as session:
        oauth = PlurkOAuth(cred, session)
        await oauth.authorize()

        r = await oauth.request('/APP/Timeline/getPlurk', {'plurk_id': '123'})
        print(r)
asyncio.run(main())
```
