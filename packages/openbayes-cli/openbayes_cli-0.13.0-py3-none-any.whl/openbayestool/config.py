# encoding: utf-8

import os

callback_url = os.getenv('JOB_UPDATE_URL', None)
if not callback_url:
    callback_url = os.getenv('OPENBAYES_JOB_URL', None)
    
job_access_token = os.getenv('JOB_ACCESS_TOKEN', None)
if not job_access_token:
    job_access_token = os.getenv('OPENBAYES_TOKEN', None)
    
uaa_token_url = os.getenv('UAA_TOKEN_URL', None)
uaa_username = os.getenv("UAA_USERNAME", None)
uaa_password = os.getenv("UAA_PASSWORD", None)