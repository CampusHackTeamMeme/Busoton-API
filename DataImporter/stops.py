from zipfile import ZipFile
import requests
import os
import shutil
import csv
import time
import psycopg2


def importStops(conn):
    csvURL = 'http://naptan.app.dft.gov.uk/DataRequest/Naptan.ashx?format=csv'

    print('Downloading the CSV file')
    start = time.time()

    csvData = requests.get(csvURL, stream=True)
    dump = csvData.raw

    if not os.path.exists('./data/'):
        os.mkdir('data')

    with open('stops.zip', 'wb') as location:
        shutil.copyfileobj(dump, location)

    dir = os.path.abspath('./data/')
    with ZipFile('stops.zip') as file:
        file.extractall(dir)

    os.remove('stops.zip')

    print('Downloaded and extracted CSV file in {} seconds'.format(round(time.time()-start,1)))
    start = time.time()
    print('Reading in the CSV to filter')

    csvFile = os.path.abspath('./data/Stops.csv')
    with open(csvFile, newline='', encoding='latin1') as file:
        reader = csv.reader(file, delimiter=',')

        head = next(reader)
        stop_id = head.index('ATCOCode')
        name = head.index('CommonName')
        lon = head.index('Longitude')
        lat = head.index('Latitude')

        filtered = []
        for row in reader:
            filtered.append((row[stop_id], row[name], row[lon], row[lat]))

    print('Writing out the filtered CSV to a file')
    count = 0
    with open('filteredStops.csv', 'w') as file:
        writer = csv.writer(file, delimiter='\t')
        for row in filtered:
            writer.writerow(row)
            count += 1
    shutil.rmtree(os.path.abspath('./data/'))

    print('Imported {} Bus stops in {} seconds'.format(count, round(time.time()-start,1)))
    start = time.time()

    c = conn.cursor()

    c.execute('''DELETE FROM stops''')
    conn.commit()
    print('Deleted all entries from stops table')

    with open('filteredStops.csv') as file:
        c.copy_from(file, 'stops', sep='\t')

    conn.commit()
    print('Copied {} entries to the stop database \n'.format(count))

    c.close()
