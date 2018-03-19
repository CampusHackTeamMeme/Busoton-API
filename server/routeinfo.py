import sqlite3 as sql

from flask_restful import Resource, reqparse

class RouteInfo(Resource):
    def __init__(self, file):
        self.DBfile = file

        self.getParser = reqparse.RequestParser(bundle_errors=True)
        self.getParser.add_argument('stop', required=True)

    def post(self):
        r = self.getParser.parse_args()

        conn = sql.connect(self.DBfile)
        conn.row_factory = lambda c, r: r[0]
        c = conn.cursor()

        query = c.execute(
            '''SELECT DISTINCT routes.string_bus 
            FROM routes_stops
            INNER JOIN routes ON routes_stops.route_id = routes.route_id
            WHERE routes_stops.stop_id = ?
            ''', (r['stop'],))

        data = query.fetchall()

        return {'stop': data}, 200
