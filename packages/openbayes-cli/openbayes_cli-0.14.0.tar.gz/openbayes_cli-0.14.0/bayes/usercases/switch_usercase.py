import validators
from bayes.client.status_client import health_check


def clean(end_point):
    if end_point.endswith('/'):
        end_point = end_point[:-1]

    return end_point


def is_exist(end_point):
    return health_check(end_point)
