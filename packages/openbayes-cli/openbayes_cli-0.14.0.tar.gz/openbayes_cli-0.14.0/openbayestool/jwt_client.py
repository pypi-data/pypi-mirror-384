#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests


class JwtClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json"
        }

    def set_token(self, token):
        self.token = token
        self.headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json"
        }

    def get(self, url, **kwargs):
        response = requests.get(url, headers=self.headers, timeout=5, **kwargs)
        return response.status_code, response.content

    def post(self, url, *args, **kwargs):
        response = requests.post(url, *args, headers=self.headers, timeout=5, **kwargs)
        return response.status_code, response.headers

    def put(self, url, *args, **kwargs):
        response = requests.put(url, *args, headers=self.headers, timeout=5, **kwargs)
        return response.status_code

    def delete(self, url, *args, **kwargs):
        response = requests.delete(url, *args, headers=self.headers, timeout=5, **kwargs)
        return response.status_code