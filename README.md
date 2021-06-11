# poaurk

Plurk + Oauth Library modify from the work by [clsung's version](https://github.com/clsung/plurk-oauth).

Replace python-oauth library to requests-oauthlib.

# Installation

```
pip install poaurk
```

# Example

## Authorize and get profile

```python
# import package
from poaurk import (PlurkAPI, PlurkOAuth)

# Init a new plurk object
plurk = PlurkAPI("<consumer key>", "<consumer secret>")

# Authorize if no token
status, data = plurk.authorize()
if not status:
    # Failed
    print(data)

# Call api
status, data = plurk.callAPI('/APP/Profile/getOwnProfile') # status = True if successful
print(data)

```

## Init from json file

Copy `api.keys.example` to yout project, modified it.

```python
from poaurk import PlurkAPI

# Init
plurk = PlurkAPI.fromfile("api.keys")

# Get own profile
status, data = plurk.callAPI('/APP/Profile/getOwnProfile')
if status:
    doSomething(data)
else:
    log.error(data) # Print error to your log

# Get Public Profile from user_id
# User id can obtain from other api
status, data = plurk.callAPI('/APP/Profile/getPublicProfile', options={'user_id': '<user id>'})
if status:
    doSomething(data)
else:
    log.error(data) # Print error to your log

# Upload picture
status, data = plurk.callAPI('/APP/Timeline/uploadPicture', files={'image': '<image path>'})
if status:
    doSomething(data)
else:
    log.error(data) # Print error to your log
```
