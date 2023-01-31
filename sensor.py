import datetime
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_NAME, CONF_API_KEY, CONF_START, CONF_MISSION, CONF_LINE, call_api, line_to_code

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        voluptuous.Required(CONF_NAME): cv.string,
        voluptuous.Required(CONF_API_KEY): cv.string,
        voluptuous.Required(CONF_START): cv.string,
        voluptuous.Optional(CONF_MISSION): cv.string,
        voluptuous.Optional(CONF_LINE): cv.string
    }
)

log = logging.getLogger(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback, ) -> None:
    line = entry.data.get(CONF_LINE)

    if entry.options is not None and entry.options.get(CONF_LINE) is not None:
        line = entry.options.get(CONF_LINE)

    mission = entry.data.get(CONF_MISSION)

    if entry.options is not None and entry.options.get(CONF_MISSION) is not None:
        mission = entry.options.get(CONF_MISSION)

    async_add_entities([LineSensor(entry.data[CONF_NAME], entry.data[CONF_API_KEY], entry.data[CONF_START],
                                   mission, line)], True)


class LineSensor(SensorEntity):
    _attr_icon = 'mdi:train'
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, name, api_key, start, mission, line):
        self._name = name
        self.data = []
        self.api_key = api_key
        self.start = start
        self.mission = mission
        self.line = line
        self.minutes = None
        self.last_update = None
        self.start_name = None
        self._attr_unique_id = self.name + '_' + self.start

    def update(self):
        line_ref = line_to_code(self.line)
        response = call_api(self.api_key, self.start)

        if response.status_code == 200:
            body = response.json()
            self.data = []
            self.minutes = None

            if 'Siri' in body and 'ServiceDelivery' in body['Siri'] \
                    and 'StopMonitoringDelivery' in body['Siri']['ServiceDelivery'] \
                    and len(body['Siri']['ServiceDelivery']['StopMonitoringDelivery']) > 0 \
                    and 'MonitoredStopVisit' in body['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0] \
                    and len(body['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']) > 0:
                visits = body['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']

                for visit in visits:
                    if 'MonitoredVehicleJourney' in visit:
                        journey = visit['MonitoredVehicleJourney']

                        if 'LineRef' in journey and 'value' in journey['LineRef']:
                            line_value = journey['LineRef']['value']

                            if line_ref is None or line_value == line_ref:
                                if self.mission is None or (
                                        'JourneyNote' in journey and len(journey['JourneyNote']) > 0
                                        and 'value' in journey['JourneyNote'][0]):
                                    miss = (journey['JourneyNote'][0]['value']) if self.mission is not None else None

                                    if miss is None or (miss in self.mission):
                                        if 'MonitoredCall' in journey:
                                            call = journey['MonitoredCall']

                                            if 'DepartureStatus' in call and 'cancelled' != call['DepartureStatus']:
                                                if 'ExpectedDepartureTime' in call:
                                                    arrival = datetime.datetime \
                                                        .strptime(call['ExpectedDepartureTime'],
                                                                  '%Y-%m-%dT%H:%M:%S.%fZ').replace(
                                                        tzinfo=datetime.timezone.utc)

                                                    if arrival > datetime.datetime.now(datetime.timezone.utc):
                                                        result = {
                                                            'line': line_value.replace('STIF:Line::', '')[:-1],
                                                            'time': arrival,
                                                            'mission': miss
                                                        }

                                                        if 'ArrivalPlatformName' in call \
                                                                and 'value' in call['ArrivalPlatformName']:
                                                            platform = call['ArrivalPlatformName']['value']
                                                            result['platform'] = platform

                                                        if 'DestinationName' in journey \
                                                                and len(journey['DestinationName']) > 0 \
                                                                and 'value' in journey['DestinationName'][0]:
                                                            result['end'] = journey['DestinationName'][0]['value']

                                                        if self.start_name is None and 'StopPointName' in call \
                                                                and len(call['StopPointName']) > 0 \
                                                                and 'value' in call['StopPointName'][0]:
                                                            self.start_name = call['StopPointName'][0]['value']

                                                        self.data.append(result)

            self.data = sorted(self.data, key=lambda d: d['time'])
            self.last_update = datetime.datetime.now()

            if self.data is not None and len(self.data) > 0:
                self.minutes = round(
                    (self.data[0]['time'] - datetime.datetime.now(datetime.timezone.utc)).total_seconds() / 60)
        else:
            log.error('Error while calling IDFM api:', response.reason)

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self.minutes

    @property
    def extra_state_attributes(self):
        return {
            'last_update': self.last_update,
            'start_name': self.start_name,
            'mission': self.mission,
            'line': self.line,
            'minutes': self.minutes,
            'trains': self.data
        }
