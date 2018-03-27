import psycopg2

def createStops(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS stops(
        stop_id TEXT PRIMARY KEY,
        name TEXT,
        lon DOUBLE PRECISION,
        lat DOUBLE PRECISION);
        ''')

    c.execute('''CREATE INDEX CONCURRENTLY IF NOT EXISTS 
         lon_lon_lat_lat ON stops(lon,lon,lat,lat);
         ''')
    
    conn.commit()


def createOps(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS operators(
        code TEXT PRIMARY KEY,
        operator TEXT);
        ''')

    conn.commit()


with open('postgres.config') as file:
    creds = file.read()

with psycopg2.connect(creds) as conn:
    createStops(conn)
    createOps(conn)