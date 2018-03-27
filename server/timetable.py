from flask_restful import Resource, reqparse
import requests
from xml.etree.ElementTree import Element, SubElement, tostring, fromstring

from datetime import datetime
import dateutil.parser
import re
from random import randint


API_URL = 'http://nextbus.mxdata.co.uk/nextbuses/1.0/1'

def generateXML(stop_id):
    top = Element('Siri', attrib={'version': '1.0', 'xmlns': 'http://www.siri.org.uk/'})
    ServiceRequest = SubElement(top, 'ServiceRequest')
    RequestTimestamp = SubElement(ServiceRequest, 'RequestTimestamp')
    RequestTimestamp.text = datetime.now().isoformat()
    RequestorRef = SubElement(ServiceRequest, 'RequestorRef')
    RequestorRef.text = 'TravelineAPI465'
    StopMonitoringRequest = SubElement(ServiceRequest, 'StopMonitoringRequest')
    RequestTimestamp2 = SubElement(StopMonitoringRequest, 'RequestTimestamp')
    RequestTimestamp2.text = datetime.now().isoformat()
    MessageIdentifier = SubElement(StopMonitoringRequest, 'MessageIdentifier')
    MessageIdentifier.text = str(randint(10000, 100000))
    MonitoringRef = SubElement(StopMonitoringRequest, 'MonitoringRef')
    MonitoringRef.text = str(stop_id)

    return tostring(top, encoding='UTF-8')


class TimeTable(Resource):
    def __init__(self, SQL, auth):
        self.login = SQL
        self.auth = auth
        
        self.getParser = reqparse.RequestParser(bundle_errors=True)
        self.getParser.add_argument('stop', required=True)


    def post(self):
        r = self.getParser.parse_args()

        headers = {'Content-Type': 'text/xml'}
        data = generateXML(r['stop'])
        
        r = requests.post(API_URL, auth=self.auth, headers=headers, data=data)

        if r.status_code is not 200:
            return {'ERROR': 'Failed fetching timetable'}, 500

        xmlstring = re.sub(' xmlns="[^"]+"', '', r.text, count=1)
        xml = fromstring(xmlstring)

        toSend = {}

        for bus in xml.iter('MonitoredVehicleJourney'):
            bus_service = 'None'
            bus_operator = 'None'
            bus_dest = 'None'
            bus_time = 'None'
            for child in bus.iter():
                if child.tag in 'PublishedLineName':
                    bus_service = child.text
                elif child.tag in 'OperatorRef':
                    bus_operator = child.text.strip('_noc_')
                elif child.tag in 'DirectionName':
                    bus_dest = child.text
                elif child.tag in 'AimedDepartureTime':
                    if bus_time in 'None':
                        bus_time = dateutil.parser.parse(child.text).strftime("%H:%M")
                elif child.tag in 'ExpectedDepartureTime':
                    bus_time = dateutil.parser.parse(child.text).strftime("%H:%M")

            if bus_service not in 'None':
                toSend.setdefault(bus_service, {}).setdefault("time", []).append(bus_time)
                toSend[bus_service].setdefault("destination", bus_dest)
                toSend[bus_service].setdefault("operator", bus_operator) 

        if len(toSend) == 0:
            return {'ERROR': "No Bus Times Available"}, 200
        return toSend, 200
