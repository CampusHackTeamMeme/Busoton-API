from zipfile import ZipFile
import requests
import os
import shutil
import csv
import time
import psycopg2

def importOps(conn):
    csvURL = 'http://www.travelinedata.org.uk/wp-content/themes/desktop/nocadvanced_download.php?reportFormat=csvFlatFile&allTable%5B%5D=table_noc_table&submit=Submit'

    print('Downloading the CSV file')
    start = time.time()

    csvData = requests.get(csvURL, stream=True)
    dump = csvData.raw

    if not os.path.exists('./data/'):
        os.mkdir('data')

    with open('ops.zip', 'wb') as location:
        shutil.copyfileobj(dump, location)

    dir = os.path.abspath('./data/')
    with ZipFile('ops.zip') as file:
        file.extractall(dir)

    os.remove('ops.zip')

    print('Downloaded and extracted CSV file in {} seconds'.format(round(time.time()-start,1)))
    start = time.time()
    print('Reading in the CSV to filter')

    csvFile = os.path.abspath('./data/NOCTable.csv')
    with open(csvFile, newline='', encoding='latin1') as file:
        reader = csv.reader(file, delimiter=',')

        head = next(reader)
        code = head.index('NOCCODE')
        name = head.index('OperatorPublicName')

        filtered = []
        for row in reader:
            filtered.append((row[code], row[name]))

    print('Writing out the filtered CSV to a file')
    count = 0
    with open('filteredOps.csv', 'w') as file:
        writer = csv.writer(file, delimiter='\t')
        for row in filtered:
            writer.writerow(row)
            count += 1
    shutil.rmtree(os.path.abspath('./data/'))

    print('Imported {} operators in {} seconds'.format(count, round(time.time()-start,1)))
    start = time.time()

    c = conn.cursor()

    c.execute('''DELETE FROM operators''')
    conn.commit()
    print('Deleted all entries from operators table')

    with open('filteredOps.csv') as file:
        c.copy_from(file, 'operators', sep='\t')

    conn.commit()
    print('Copied {} entries to the stop database \n'.format(count))

    c.close()