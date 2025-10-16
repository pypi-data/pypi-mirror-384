#!/usr/bin/env python
# encoding: utf-8

import sys
import urllib.parse

from typing import Union
from openbayestool.jwt_client import JwtClient
from datetime import datetime

Number = Union[int, float]
Param = Union[int, float, str]


class Updater:
    def __init__(self, jwt_client: JwtClient, callback_url: str=None):
        self.jwt_client = jwt_client
        self.callback_url = callback_url

    def set_access_token(self, token):
        self.jwt_client.set_token(token)

    def get_access_token(self):
        return self.jwt_client.token

    def set_callback_url(self, callback_url):
        self.callback_url = callback_url

    def get_callback_url(self):
        return self.callback_url

    def clear_metric(self, key: str):
        if self.callback_url is None:
            print("WARNING: No callback url is given", file=sys.stderr)
            return

        clear_metrics_url = self.callback_url + "/metrics/" + urllib.parse.quote(key, safe="")
        try:
            status_code = self.jwt_client.delete(clear_metrics_url)
            if status_code >= 400:
                print("WARNING: Failed to clear metric {}: {}".format(key, status_code))
        except Exception as e:
            print("WARNING: Failed to clear metric to server")
            print(e)

    def clear_param(self, key):
        self.log_param(key, "")

    def log_metric(self, key: str, value):
        if self.callback_url is None:
            print("WARNING: No callback url is given", file=sys.stderr)
            return

        try:
            val = float(value)
        except ValueError:
            print("WARNING: The metric {}={} was not logged because the value is not a number.".format(key, value),
                  file=sys.stderr)
            return

        try:
            status_code = self.jwt_client.put(self.callback_url, json={
                'metrics': {
                    key: [{
                        'value': val,
                        'created_at': datetime.now().isoformat()
                    }]
                }
            })
            if status_code >= 400:
                print("WARNING: Failed to update metrics: {}".format(status_code))
        except Exception as e:
            print("WARNING: Failed to update metrics to server")
            print(e)

    def log_param(self, key: str, value: Param):
        if self.callback_url is None:
            print("WARNING: No callback url is given", file=sys.stderr)
            return

        if not isinstance(value, (int, float, str)):
            print("WARNING: The param {}={} was not logged because the value is not a number.".format(key, value),
                  file=sys.stderr)
            return

        try:
            status_code = self.jwt_client.put(self.callback_url, json={
                'parameters': {
                    key: value
                }
            })
            if status_code >= 400:
                print("WARNING: Failed to update param: {}".format(status_code))
        except Exception as e:
            print("WARNING: Failed to update param to server")
            print(e)
