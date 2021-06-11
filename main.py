#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 dephilia <dephilia@microlabpc3.pme.nthu.edu.tw>
#
# Distributed under terms of the MIT license.

"""

"""

from poaurk import (PlurkAPI, PlurkOAuth)
plurk = PlurkAPI("hT0YpOH0vCj3", "PFXFOtcL27YmAgXZTr6QuTBeyE8obhno")

print(plurk.get_request_token())

