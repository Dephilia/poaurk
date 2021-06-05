#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 dephilia <dephilia@MacBook-Pro.local>
#
# Distributed under terms of the MIT license.

"""

"""

import unittest
from poaurk import (PlurkAPI, PlurkOAuth)

class TestOauthMethods(unittest.TestCase):
    def test_class(self):
        oauth = PlurkOAuth("z3kiB2tbqrlC", "u8mCwet8BQNjROfUZU8A6BHc1o9rx1AE")
        oauth.authorize()

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()
