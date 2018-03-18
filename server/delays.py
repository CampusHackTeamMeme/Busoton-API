import sqlite3 as sql

from flask import request
from flask_restful import Resource
import time

# time in seconds that data is reliable for
reliableTime = 600

class Delays(Resource):
    def __init__(self, file):
        self.DBfile = file

    def put(self):
        r = request.form.to_dict()
        print(r)

        conn = sql.connect(self.DBfile)
        c = conn.cursor()

        c.execute('''INSERT INTO delays VALUES (?,?,?)''',
            (r['service'], time.time(), int(r['delay'])))

        conn.commit()

    def get(self):
        r = request.form.to_dict()
        print(r)

        conn = sql.connect(self.DBfile)
        c = conn.cursor()

        timeSince = time.time() - reliableTime

        query = c.execute('''
            SELECT round(avg(delay), 0) FROM delays
            WHERE unix > ? AND service = ?''',
            (timeSince, r['service']))
        
        return dict(zip(('delay',), query.fetchone()))
