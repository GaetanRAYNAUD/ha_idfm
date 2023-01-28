import datetime

import requests

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity

config = {
    'apiKey': '',
    'start': '43082',
    # Optional
    'end': '41194',
    # Optional
    'line': 'C01739'
    # 'line': 'C01742'
}

apiKey = config['apiKey']
start = config['start']
end = config['end'] if 'end' in config else None
line = config['line'] if 'line' in config else None

response = requests.get('https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring',
                        params={'MonitoringRef': 'STIF:StopPoint:Q:' + start + ':'}, headers={'apiKey': apiKey})
lineRef = 'STIF:Line::' + line + ':' if line is not None else None
endRef = 'STIF:StopPoint:Q:' + end + ':' if end is not None else None

if response.status_code == 200:
    body = response.json()

    if 'Siri' in body and 'ServiceDelivery' in body['Siri'] \
            and 'StopMonitoringDelivery' in body['Siri']['ServiceDelivery'] \
            and len(body['Siri']['ServiceDelivery']['StopMonitoringDelivery']) > 0 \
            and 'MonitoredStopVisit' in body['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0] \
            and len(body['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']) > 0:
        visits = body['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']
        results = []
        startName = None

        for visit in visits:
            if 'MonitoredVehicleJourney' in visit:
                journey = visit['MonitoredVehicleJourney']

                if 'LineRef' in journey and 'value' in journey['LineRef']:
                    lineValue = journey['LineRef']['value']

                    if lineRef is None or lineValue == lineRef:
                        if endRef is None or ('DestinationRef' in journey and 'value' in journey['DestinationRef']
                                              and endRef == journey['DestinationRef']['value']):
                            if 'MonitoredCall' in journey:
                                call = journey['MonitoredCall']

                                if 'DepartureStatus' in call and 'cancelled' != call['DepartureStatus']:
                                    if 'ExpectedArrivalTime' in call:
                                        arrival = datetime.datetime.fromisoformat(call['ExpectedArrivalTime'])

                                        if arrival > datetime.datetime.now().astimezone():
                                            result = {
                                                'line': lineValue.replace('STIF:Line::', '')[:-1],
                                                'time': arrival.isoformat()
                                            }

                                            if 'ArrivalPlatformName' in call and 'value' in call['ArrivalPlatformName']:
                                                platform = call['ArrivalPlatformName']['value']
                                                result['platform'] = platform

                                            if 'DestinationName' in journey and len(journey['DestinationName']) > 0 \
                                                    and 'value' in journey['DestinationName'][0]:
                                                result['end'] = journey['DestinationName'][0]['value']

                                            if startName is None and 'StopPointName' in call \
                                                    and len(call['StopPointName']) > 0 \
                                                    and 'value' in call['StopPointName'][0]:
                                                startName = call['StopPointName'][0]['value']

                                            results.append(result)

        print(startName)
        for result in results:
            print(result)
