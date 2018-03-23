from flask import Flask
from flask_restful import Api
import psycopg2

from busstops import BusStops
# from routeinfo import RouteInfo
# -- from timetable import TimeTable
# from servicestops import ServiceStops
# -- from stoplocations import StopLocations
# from delays import Delays


app = Flask(__name__)
api = Api(app)

with open('postgres.config') as file:
    conn = psycopg2.connect(file.read())

api.add_resource(BusStops, '/api/busstops', resource_class_args=(conn,))
# api.add_resource(RouteInfo, '/api/routeinfo', resource_class_args=(DBfile,))
# api.add_resource(TimeTable, '/api/timetable', resource_class_args=(conn,))
# api.add_resource(ServiceStops, '/api/servicestops', resource_class_args=(DBfile,))
# api.add_resource(StopLocations, '/api/stoplocations', resource_class_args=(conn,))
# api.add_resource(Delays, '/api/delays', resource_class_args=(DBfile,))

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
