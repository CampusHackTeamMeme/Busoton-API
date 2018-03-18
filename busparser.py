import argparse
import os
import sqlite3

import requests

ROUTES_URL = 'http://api.bus.southampton.ac.uk/dump/routes'
STOPS_URL = 'http://api.bus.southampton.ac.uk/dump/stops'
OPERATORS_URL = 'http://api.bus.southampton.ac.uk/dump/operators'


def create_stops_and_routes(conn):
    c = conn.cursor()

    # Create history table
    c.execute('''
    CREATE TABLE stops(
        stop_id TEXT PRIMARY KEY NOT NULL,
        name TEXT,
        lat REAL,
        lon REAL
    )''')
    c.execute('''
    CREATE TABLE operators(
        operator_id TEXT PRIMARY KEY NOT NULL,
        label TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE routes(
        route_id TEXT PRIMARY KEY NOT NULL,
        desc TEXT,
        operator TEXT,
        direction TEXT,
        service TEXT,
        string_bus TEXT,
        FOREIGN KEY (operator) REFERENCES operators(operator_id)
          ON DELETE CASCADE ON UPDATE NO ACTION
    )''')
    c.execute('''
    CREATE TABLE routes_stops(
        route_id TEXT NOT NULL,
        stop_id TEXT NOT NULL,
        PRIMARY KEY (route_id, stop_id),
        FOREIGN KEY (route_id) REFERENCES routes (route_id)
          ON DELETE CASCADE ON UPDATE NO ACTION,
        FOREIGN KEY (stop_id) REFERENCES stops (stop_id)
          ON DELETE CASCADE ON UPDATE NO ACTION
    )''')
    c.execute('''
    CREATE INDEX geo_stops_index
      on stops (lat, lon);
    ''')

    # Save (commit) the changes
    conn.commit()


def create_delays(conn):
    c = conn.cursor()
    c.execute('''
    CREATE TABLE delays(
        service TEXT,
        unix REAL PRIMARY KEY NOT NULL,
        delay REAL
    )''')


def create_db(conn):
    create_stops_and_routes(conn)
    create_delays(conn)


def delete_db(conn):
    delete_stops_and_routes(conn)
    delete_delays(conn)


def delete_stops_and_routes(conn):
    c = conn.cursor()
    c.execute('''DROP TABLE stops''')
    c.execute('''DROP TABLE routes''')
    c.execute('''DROP TABLE routes_stops''')
    conn.commit()


def delete_delays(conn):
    c = conn.cursor()
    c.execute('''DROP TABLE delays''')
    conn.commit()


def insert_stops(conn, stops_data):
    c = conn.cursor()
    stops_length = len(stops_data)
    print("INSERTING STOPS 0/%d" % stops_length, end="\r")
    count = 0
    for stop in stops_data:
        count += 1
        if count % 10 == 0:
            print("INSERTING STOPS %d/%d" % (count, stops_length), end="\r")
        c.execute(
            'INSERT OR REPLACE INTO stops (stop_id, name, lat, lon) VALUES (?,?,?,?)',
            (stop['id'], stop['label'], float(stop['lat']), float(stop['lon']))
        )
    print("%d STOPS INSERTED" % stops_length)


def insert_routes(conn, routes_data):
    c = conn.cursor()
    routes_length = len(routes_data)
    print("INSERTING Routes 0/%d" % routes_length, end="\r")
    count = 0
    for route in routes_data:
        count += 1
        if count % 10 == 0:
            print("INSERTING ROUTES %d/%d" % (count, routes_length), end="\r")
        c.execute(
            'INSERT OR REPLACE INTO routes (route_id, desc, operator, direction, service, string_bus) VALUES (?,?,?,?,?,?)',
            (route['id'], route['label'], route['operator'], route['direction'], route['service'],
             (route['operator'] + ' ' + route['service']))
        )
        c.executemany(
            'INSERT OR REPLACE INTO routes_stops (route_id, stop_id) VALUES (?,?)',
            [(route['id'], stop) for stop in route['stops']]
        )
    print("%d ROUTES INSERTED" % routes_length)


def insert_operators(conn, operators_data):
    c = conn.cursor()
    operators_length = len(operators_data)
    print("INSERTING OPERATORS 0/%d" % operators_length, end="\r")
    count = 0
    for operator in operators_data:
        count += 1
        if count % 10 == 0:
            print("INSERTING OPERATORS %d/%d" % (count, operators_length), end="\r")
        c.execute(
            'INSERT OR REPLACE INTO operators (operator_id, label) VALUES (?,?)',
            (operator['id'], operator['label'])
        )
    print("%d OPERATORS INSERTED" % operators_length)


def import_data(conn):
    print("Getting stops JSON")
    stops_resp = requests.get(STOPS_URL, timeout=30)
    stops_data = stops_resp.json()

    insert_stops(conn, stops_data)

    print("Getting operators JSON")
    operators_resp = requests.get(OPERATORS_URL, timeout=30)
    operators_data = operators_resp.json()

    insert_operators(conn, operators_data)

    print("Getting routes JSON")
    routes_resp = requests.get(ROUTES_URL, timeout=30)
    routes_data = routes_resp.json()

    insert_routes(conn, routes_data)


def main(db_name, should_create_db):
    exists = os.path.isfile(db_name)
    with sqlite3.connect(db_name) as conn:
        # Init the DB
        if not exists:
            create_db(conn)
            print("Database file '{}' didn't exist, created.".format(db_name))
        elif should_create_db:
            delete_db(conn)
            create_db(conn)
            print("Deleted database and recreated.")

        import_data(conn)
        conn.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--create_db", action='store_true')
    parser.add_argument("--database", "-d", default="bus_finder.db")
    args = parser.parse_args()
    main(args.database, args.create_db)
