import requests
from homeassistant.const import Platform

DOMAIN = 'idfm'

API_URL = 'https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring'

CONF_NAME = 'name'
CONF_API_KEY = 'api_key'
CONF_START = 'start'
CONF_MISSION = 'mission'
CONF_LINE = 'line'

PLATFORMS = [Platform.SENSOR]


def call_api(api_key: str, stop: str) -> requests.Response:
    return requests.get(API_URL, params={'MonitoringRef': stop_to_code(stop)}, headers={'apiKey': api_key})


def stop_to_code(code: str) -> str:
    return 'STIF:StopPoint:Q:' + code + ':'


def line_to_code(code: str = None) -> str:
    return 'STIF:Line::' + code + ':' if code is not None else None
