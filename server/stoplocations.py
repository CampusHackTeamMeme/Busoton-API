import sqlite3 as sql

from flask import request
from flask_restful import Resource


class StopLocations(Resource):
    def __init__(self, file):
        self.DBfile = file

    def get(self):
        r = request.form.to_dict()
        req = r['stops'].strip('[').strip(']').split(',')
        print(req)

        conn = sql.connect(self.DBfile)
        c = conn.cursor()

        toSend = {}
        keys = ('stop_id', 'lon', 'lat')

        for stop in req:
            query = c.execute('''
                SELECT stop_id, lon, lat FROM stops 
                WHERE stop_id = ?''',
                              (stop,))
            data = dict(zip(keys, query.fetchall()[0]))

            toSend[data['stop_id']] = {
                'lon': data['lon'],
                'lat': data['lat']
            }

        return toSend, 200
