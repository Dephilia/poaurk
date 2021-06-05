# -*- coding: utf-8 -*-
import requests
from requests_oauthlib import OAuth1
from urllib.parse import parse_qsl, parse_qs, urlencode

class PlurkOAuth:
    def __init__(self, customer_key, customer_secret):
        # Must provide customer information
        self.base_url = 'https://www.plurk.com'
        self.request_token_url = '/OAuth/request_token'
        self.authorization_url = '/OAuth/authorize'
        self.access_token_url = '/OAuth/access_token'

        self.customer_key = customer_key
        self.customer_secret = customer_secret

        self.token = None
        self.token_secret = None

    def __str__(self):
        pass

    def __unicode__(self):
        return self.base_url

    def authorize(self, access_token_key=None, access_token_secret=None):
        if access_token_key and access_token_secret:
            self.token = access_token_key
            self.token_secret = access_token_secret

        else:
            self.get_request_token()
            verifier = self.get_verifier()
            self.get_access_token(verifier)


    def request(self, url, data={}, files={}):
        """ Return: status code, json object, status reason """
        oauth = OAuth1(self.customer_key,
                       client_secret = self.customer_secret,
                       resource_owner_key = self.token,
                       resource_owner_secret = self.token_secret)

        req_files = {}
        if files:
            for (name, fpath) in files.items():
                req_files[name] = open(fpath, 'rb')

        r = requests.post(url= self.base_url + url, 
                          auth=oauth,
                          data=data,
                          files=req_files if req_files else None)

        for name, ofile in req_files.items():
             ofile.close()

        r.raise_for_status() # Raise for error

        return r


    def get_request_token(self):
        oauth = OAuth1(self.customer_key, client_secret = self.customer_secret)
        r = requests.post(url=self.base_url + self.request_token_url, auth=oauth)
        r.raise_for_status() # Raise for error

        token = dict(parse_qsl(r.content))
        self.token = token[b"oauth_token"].decode('ascii')
        self.token_secret = token[b"oauth_token_secret"].decode('ascii')

    def get_verifier(self):

        # Setup
        print("Open the following URL and authorize it.")
        print(self.get_verifier_url())

        verified = 'n'
        while verified.lower() == 'n':
            verifier = input('Input the verification number: ')
            verified = input('Are you sure? (y/n) ')
        return verifier

    def get_verifier_url(self):
        if self.token==None or self.token_secret==None:
            raise Exception('Please request a token first')
        return f'{self.base_url}{self.authorization_url}?oauth_token={self.token}'

    def get_access_token(self, verifier):
        oauth = OAuth1(self.customer_key,
                       client_secret = self.customer_secret,
                       resource_owner_key = self.token,
                       resource_owner_secret = self.token_secret,
                       verifier=verifier)

        r = requests.post(url= self.base_url + self.access_token_url, auth=oauth)
        r.raise_for_status() # Raise for error

        token = dict(parse_qsl(r.content))
        self.token = token[b"oauth_token"].decode('ascii')
        self.token_secret = token[b"oauth_token_secret"].decode('ascii')

