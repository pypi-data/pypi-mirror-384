import csv
import os
import sys
import re
import numpy as np
from datetime import datetime
import dateutil.parser as dparser
from mysqlquerys import connect
from mysqlquerys import mysql_rm

np.set_printoptions(linewidth=250)

db_type = 'MySQL'
ini_file = r"D:\Python\MySQL\database.ini"
flightTable = connect.Table(ini_file, 'aeroclub', 'zbor_log')
costsTable = connect.Table(ini_file, 'myfolderstructure', 'aeroclub')


def write2flightTable(inpFile):
    with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
        linereader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for i, row in enumerate(linereader):
            if i == 0:
                tableHead = [c.strip('"') for c in row]
                # print(tableHead)
                tabHeadDict = {'Lfz.': 'plane',
                               'Datum': 'flight_date',
                               'Start': 'start',
                               'Landung': 'land',
                               'Zeit': 'flight_time',
                               'Startort': 'place_from',
                               'Landeort': 'place_to'
                               }
                continue
            cols = []
            vals = []

            for ir, v in enumerate(row):
                origColName = tableHead[ir]
                # print(origColName, list(tabHeadDict.keys()))
                if origColName in list(tabHeadDict.keys()):
                    # print('BINGO')
                    cols.append(tabHeadDict[origColName])
                    if tabHeadDict[origColName] == 'flight_date':
                        print('before', v)
                        v = flightTable.convertDatumFormat4SQL(v)
                        print('after', v)
                    elif (tabHeadDict[origColName] == 'Start') or (tabHeadDict[origColName] == 'Landung'):
                        v = flightTable.convertTimeFormat4SQL(v)
                    elif tabHeadDict[origColName] == 'Zeit':
                        v = int(v)
                    vals.append(v)

            print('cols', cols)
            print('vals', vals)
            cols.append('price_hour')
            vals.append(85)
            flightTable.add_row(cols, vals)


def getPrice4Time(fromTime, bis):
    match1 = ('flight_date', (fromTime, bis))
    match2 = ('plane', 'D-MENF')
    matches = [match1, match2]

    flights = flightTable.filterRows(matches)
    price = 0
    for row in flights:
        flightTime = row[flightTable.columnsNames.index('flight_time')]
        pricePerHour = row[flightTable.columnsNames.index('price_hour')]
        pricePerFlight = (int(flightTime) * float(pricePerHour))/60
        price += pricePerFlight
    price = round(price, 2)

    return price


def getQuartalDates(quartal, year):
    if quartal == 'Q1':
        quartal = (datetime(year, 1, 1), datetime(year, 3, 31))
    elif quartal == 'Q2':
        quartal = (datetime(year, 4, 1), datetime(year, 6, 30))
    elif quartal == 'Q3':
        quartal = (datetime(year, 7, 1), datetime(year, 9, 30))
    elif quartal == 'Q4':
        quartal = (datetime(year, 10, 1), datetime(year, 12, 31))
    return quartal


def getVideo(path):
    foundDirs = []
    dir = os.listdir(path)
    for d in dir:
        pth = os.path.join(path, d)
        if os.path.isdir(pth):
            try:
                # aa = dparser.parse(d, fuzzy=True)
                # print(aa)
                match = re.search(r'\d{4}.\d{2}.\d{2}', d)
                name = d[match.span()[1]:]
                date = datetime.strptime(match.group(), '%Y.%m.%d').date()
                tup = (date, name, pth)
                foundDirs.append(tup)
            except:
                print('****', d)
                continue

    for row in foundDirs:
        data, name, pth = row
        # print(flightTable.columnsNames.index('flight_date'))
        # print(flightTable.data[:, 3])
        flighttable = np.atleast_2d(flightTable.data)
        indx = np.where(flighttable[:, flightTable.columnsNames.index('flight_date')] == data)
        # print(flighttable[indx])
        for i in flighttable[indx]:
            id = i[0]
            flightTable.changeCellContent('name', str(name), 'id', id)
            flightTable.changeCellContent('path2log', str(pth), 'id', id)


# def write2costsTable(price):
#     costsTable


if __name__ == '__main__':
    # inpFile = r"D:\Documente\Aeroclub\Bad_Endorf\Export.csv"
    inpFile = r"D:\Documente\Radu\Aeroclub\Flight_Log\Export_VEREINSFLIEGER_11.10.2021_17.09.2024.csv"
    write2flightTable(inpFile)
    # quartals = ['Q1', 'Q2', 'Q3', 'Q4']
    # for year in range(2022, 2023):
    #     for q in quartals:
    #         interval = getQuartalDates(q, year)
    #         print(interval)
    # #         price = getPrice4Time(interval[0], interval[1])
    # #         print(year, q, price)
    # # pth = r"E:\Aviatie\Filmulete zbor"
    # # getVideo(pth)