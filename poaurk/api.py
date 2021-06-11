# -*- coding: utf-8 -*-
import sys
import json
import requests
from .oauth import PlurkOAuth


class PlurkAPI:
    def __init__(self, key=None, secret=None,
                 access_token=None, access_secret=None):
        if not key or not secret:
            raise ValueError("Both CONSUMER_KEY and CONSUMER_SECRET need to be specified")
        self._oauth = PlurkOAuth(key, secret)
        self._authorized = False
        self._error = ""
        if access_token and access_secret:
            self.authorize(access_token, access_secret)

    @classmethod
    def fromfile(cls, filename="API.keys"):
        try:
            file = open(filename, 'r+')
        except IOError:
            print("You need to put key/secret in API.keys")
            raise
        except:
            print("Unexpected error:", sys.exc_info()[0])
        else:
            data = json.load(file)
            file.close()
            if not data["CONSUMER_KEY"] or not data["CONSUMER_SECRET"]:
                return cls()
            if data.get("ACCESS_TOKEN", None) and \
               data.get("ACCESS_TOKEN_SECRET", None):
                return cls(data["CONSUMER_KEY"], data["CONSUMER_SECRET"],
                           data["ACCESS_TOKEN"], data["ACCESS_TOKEN_SECRET"])
            else:
                return cls(data["CONSUMER_KEY"], data["CONSUMER_SECRET"])

    def is_authorized(self):
        return self._authorized

    def authorize(self, access_key=None, access_secret=None):
        try:
            self._oauth.authorize(access_key, access_secret)
            self._authorized = True
            return ( True, "")
        except requests.exceptions.RequestException as e:
            self._error = e
            return ( False, e)

    def callAPI(self, path, options={}, files={}):
        try:
            r = self._oauth.request(path, options, files)
            return ( True, r.json() )
        except requests.exceptions.RequestException as e:
            self._error = e
            return ( False, e )

    def error(self):
        return self._error

    def get_request_token(self):
        try:
            self._oauth.get_request_token()
            return ( True, {
                'key': self._oauth.token,
                'secret': self._oauth.token_secret,
            } )

        except requests.exceptions.RequestException as e:
            self._error = e
            return ( False, e)

    def set_request_token(self, request_key, request_secret):
        self._oauth.authorize(access_token_key=request_key, access_token_secret=request_secret)

    def get_verifier_url(self):
        return self._oauth.get_verifier_url()

    def get_access_token(self, verifier):
        try:
            self._oauth.get_access_token(verifier)
            return ( True, {
                'key': self._oauth.token,
                'secret': self._oauth.token_secret,
            } )

        except requests.exceptions.RequestException as e:
            self._error = e
