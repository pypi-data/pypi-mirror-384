# encoding: utf-8

import sys

from openbayestool.updater import Updater
from openbayestool.jwt_client import JwtClient
from openbayestool.http_client import HttpClient
from openbayestool import config

def config_check(callback_url, job_access_token):
    if not callback_url:
        print("WARNING: No JOB_UPDATE_URL or OPENBAYES_JOB_URL is given", file=sys.stderr)
        return False
    
    if not job_access_token:
        print("WARNING: JOB_ACCESS_TOKEN or OPENBAYES_TOKEN is not given", file=sys.stderr)
        return False

    return True


class UpdateBuilder():
    def __init__(self, callback_url, job_access_token):
        self.callback_url = callback_url
        self.job_access_token = job_access_token
        self.updater = None

    def get_callback_url(self):
        return self.callback_url

    def set_callback_url(self, url):
        self.callback_url = url
        self.updater = None

    def get_job_access_token(self):
        return self.job_access_token

    def set_job_access_token(self, token):
        self.job_access_token = token
        self.updater = None

    def build(self):
        if self.updater is not None:
            return self.updater

        if not config_check(self.callback_url, self.job_access_token):
            return None
        
        jwtclient = JwtClient(self.job_access_token)
        self.updater = Updater(jwtclient, self.callback_url)
        return self.updater

_builder = UpdateBuilder(config.callback_url, config.job_access_token)

def get_updater():
    return _builder.build()


def log_param(key, value):
    updater = get_updater()

    if updater:
        updater.log_param(key, value)


def log_metric(key, value):
    updater = get_updater()

    if updater:
        updater.log_metric(key, value)


def clear_metric(key):
    updater = get_updater()

    if updater:
        updater.clear_metric(key)


def clear_param(key):
    updater = get_updater()

    if updater:
        updater.clear_param(key)
        

def set_callback_url(url):
    _builder.set_callback_url(url)


def get_callback_url():
    return _builder.get_callback_url()


def set_job_access_token(token):
    _builder.set_job_access_token(token)


def get_job_access_token():
    return _builder.get_job_access_token()