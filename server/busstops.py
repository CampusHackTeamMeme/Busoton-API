import sqlite3 as sql

from flask_restful import Resource, reqparse

class BusStops(Resource):
    def __init__(self, file):
        self.DBfile = file

        self.getParser = reqparse.RequestParser(bundle_errors=True)
        self.getParser.add_argument('startLon', type=float, required=True, location='form')
        self.getParser.add_argument('endLon', type=float, required=True, location='form')
        self.getParser.add_argument('startLat', type=float, required=True, location='form')
        self.getParser.add_argument('endLat', type=float, required=True, location='form')

    def get(self):
        r = self.getParser.parse_args()

        conn = sql.connect(self.DBfile)
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        c = conn.cursor()

        query = c.execute(
            '''SELECT stop_id, name, lat, lon FROM stops
                WHERE lon > ?
                AND lon < ?
                AND lat > ?
                AND lat < ?''',
            (r['startLon'], r['endLon'], r['startLat'], r['endLat']))

        data = query.fetchall()
        print('Returned {} bus stops'.format(len(data)))

        return {'data': data}, 200
