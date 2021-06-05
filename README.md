# poaurk

Plurk + Oauth Library modify from the work by (clsung's version)[https://github.com/clsung/plurk-oauth].

Replace python-oauth library to requests-oauthlib.

# Installation

```
pip install poaurk
```

# Example

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
