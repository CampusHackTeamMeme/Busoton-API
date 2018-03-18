import re
import sqlite3

import requests
from bs4 import BeautifulSoup
from flask import request
from flask_restful import Resource
from datetime import datetime, timedelta

BUS_STOP_URL = "http://nextbuses.mobi/WebView/BusStopSearch/BusStopSearchResults?id=%s"


class TimeTable(Resource):
    def __init__(self, file):
        self.DBfile = file

    def get(self):
        r = request.form.to_dict()

        html = requests.get(BUS_STOP_URL % r['stop'])
        parsed_html = BeautifulSoup(html.text, "lxml")
        bus_stops_table = parsed_html.body.find('table', attrs={'class': 'BusStops'})

        to_send = {}

        if not bus_stops_table:
            to_send[r['stop']] = [{'error': "No Bus Times Available"}]
            return to_send, 200

        bus_stops_rows = bus_stops_table.find_all("tr")

        data = {}

        conn = sqlite3.connect(self.DBfile)
        c = conn.cursor()

        for row in bus_stops_rows:
            cells = row.find_all("td")
            bus_regex = "(?P<dest>.*)at\s(?P<time>\d\d:\d\d)"
            bus_service = cells[0].find("a").text

            # Get bus operator
            query = c.execute('''SELECT routes.operator FROM stops
            INNER JOIN routes_stops ON stops.stop_id = routes_stops.stop_id
             INNER JOIN routes ON routes_stops.route_id = routes.route_id
             WHERE stops.stop_id = ? AND routes.service = ?''', (r['stop'], bus_service))

            bus_operator = query.fetchone()[0]

            bus_service = bus_operator + bus_service

            bus_return = re.search(bus_regex, cells[1].text)
            if bus_return is not None:
                bus_dest = bus_return.group('dest')
                bus_time = bus_return.group('time')
            else:
                bus_regex = "(?P<dest>.*)in\s(?P<time>[0-9]{0,3})\s"
                bus_return = re.search(bus_regex, cells[1].text)
                if bus_return is not None:
                    bus_dest = bus_return.group('dest')
                    bus_time = (datetime.now() + timedelta(minutes=int(bus_return.group('time')))).strftime("%H:%M")
                else:
                    bus_regex = "(?P<dest>.*)\s(?P<time>DUE)\s"
                    bus_return = re.search(bus_regex, cells[1].text, flags=re.IGNORECASE)
                    bus_dest = bus_return.group('dest')
                    bus_time = datetime.now().strftime("%H:%M")

            data.setdefault(bus_service, {}).setdefault("time", []).append(bus_time)
            data[bus_service].setdefault("destination", bus_dest)
            data[bus_service].setdefault("operator", bus_operator)

        to_send[r['stop']] = data

        return to_send, 200
