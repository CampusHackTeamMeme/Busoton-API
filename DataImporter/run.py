import psycopg2

from stops import importStops
from ops import importOps

if __name__ == "__main__":
    with open('postgres.config') as file:
        conn = psycopg2.connect(file.read())

    importStops(conn)
    importOps(conn)

    conn.close()
