from psycopg2.extras import RealDictCursor

from flask_restful import Resource, reqparse

class BusStops(Resource):
    def __init__(self, conn):
        self.conn = conn

        self.getParser = reqparse.RequestParser(bundle_errors=True)
        self.getParser.add_argument('startLon', type=float, required=True)
        self.getParser.add_argument('endLon', type=float, required=True)
        self.getParser.add_argument('startLat', type=float, required=True)
        self.getParser.add_argument('endLat', type=float, required=True)

    def post(self):
        r = self.getParser.parse_args()

        c = self.conn.cursor(cursor_factory = RealDictCursor)

        c.execute(
            '''SELECT stop_id, name, lat, lon FROM stops
                WHERE lon > %s
                AND lon < %s
                AND lat > %s
                AND lat < %s''',
            (r['startLon'], r['endLon'], r['startLat'], r['endLat']))

        data = c.fetchall()
        print('Returned {} bus stops'.format(len(data)))

        return {'data': data}, 200
