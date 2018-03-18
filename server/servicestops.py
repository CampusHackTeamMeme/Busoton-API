import sqlite3 as sql

from flask import request
from flask_restful import Resource


class ServiceStops(Resource):
    def __init__(self, file):
        self.DBfile = file

    def get(self):
        r = request.form.to_dict()
        print(r)

        conn = sql.connect(self.DBfile)
        c = conn.cursor()

        if request.args.get('operator'):
            query = c.execute('''SELECT DISTINCT stops.stop_id, routes.operator FROM stops 
            INNER JOIN routes_stops ON stops.stop_id = routes_stops.stop_id
            INNER JOIN routes ON routes_stops.route_id = routes.route_id
            WHERE service = ? AND routes.operator = ?''', (r['service'], r['operator']))
        else:
            query = c.execute('''SELECT DISTINCT stops.stop_id, routes.operator FROM stops 
            INNER JOIN routes_stops ON stops.stop_id = routes_stops.stop_id
            INNER JOIN routes ON routes_stops.route_id = routes.route_id
            WHERE routes.string_bus = ?''', (r['service'],))

        data = {"service": []}
        for i in query.fetchall():
            list_exits = False
            if request.args.get('clean'):
                for operator in data["service"]:
                    if operator["operator"] == i[1]:
                        list_exits = True
                        operator.setdefault("stops", []).append(i[0])
                if not list_exits:
                    data["service"].append({
                        "operator": i[1],
                        "stops": [i[0]],
                    })
            else:
                if not list_exits:
                    data["service"].append(i[0])

        return data, 200
