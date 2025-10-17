import os
import time
import csv
from datetime import date
from mysqlquerys import mysql_rm
import connect
from datetime import datetime


def insert_file_to_db():
    #https://pynative.com/python-mysql-blob-insert-retrieve-file-image-as-a-blob-in-mysql/
    ini_file = r"D:\Python\MySQL\test_db.ini"
    txt_file = r"D:\Documente\Munca\ALTEN\Arbeitszeugnis.pdf"
    with open(txt_file, 'rb') as file:
        binaryData = file.read()
    conf = connect.Config(ini_file)
    active_table = mysql_rm.Table(conf.credentials, 'testrrrr')
    query = "INSERT INTO testrrrr (aaa, ccc, biodata) VALUES (%s,%s,%s)"
    insert_blob_tuple = (111, 'aaa', binaryData)
    cursor = active_table.db.cursor()
    result = cursor.execute(query, insert_blob_tuple)
    active_table.db.commit()
    print("Image and file inserted successfully as a BLOB into python_employee table", result)
    cursor.close()


def get_blob():
    test_db = r"D:\Python\MySQL\test_db.ini"
    conf = connect.Config(test_db)
    active_table = mysql_rm.Table(conf.credentials, 'testrrrr')
    print(active_table.columnsProperties)

    cursor = active_table.db.cursor()
    # print(active_table.columnsNames)
    file_name = r'D:\Python\MySQL\test.pdf'
    id = 9
    sql_fetch_blob_query = "SELECT * from testrrrr where id = %s"
    cursor.execute(sql_fetch_blob_query, (id,))
    record = cursor.fetchall()
    for row in record:
        data = row[3]

        with open(file_name, 'wb') as file:
            file.write(data)


def filterRows_order_by():
    chelt_db = r"D:\Python\MySQL\cheltuieli_db.ini"
    conf = connect.Config(chelt_db)
    active_table = mysql_rm.Table(conf.credentials, 'alimentari')
    selectedStartDate = date(2021, 1, 1)
    selectedEndDate = date(2023, 12, 31)
    matches = [('data', (selectedStartDate, selectedEndDate)), ('type', 'benzina')]

    order_by = ('data', 'DESC')

    table = active_table.filterRows(matches, order_by)
    for i in table:
        print(i)


def return_cells_where():
    chelt_db = r"D:\Python\MySQL\cheltuieli_db.ini"
    ini_file = r"D:\Python\MySQL\cheltuieli_online\src\rappmysql\static\wdb.ini"
    test_db = r"D:\Python\MySQL\test_db.ini"

    conf = connect.Config(chelt_db)

    active_table = mysql_rm.Table(conf.credentials, 'hyundai_ioniq')
    print(active_table.columnsProperties)

    matches = [('type', 'electric')]
    ids = active_table.returnCellsWhere('id',matches)
    # # money = active_table.returnCellsWhere('id', matches)
    print(ids)
    for i in ids:
    #     # match = [('id', i)]
    #     # val = active_table.returnCellsWhere('type', match)
    #     # print(val[0])
    #     active_table.changeCellContent('type', 'electric', 'id', i)
        xx = ['id', (i, )]
        active_table.deleteRow(xx)
    cols = ['data', 'type', 'brutto', 'amount', 'ppu', 'comment',  'refuel', 'other', 'recharges']
    inpFile = r"D:\Documente\Masina\Hyundai Ioniq\Consum\rechnungen.csv"
    with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
        linereader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for i, row in enumerate(linereader):
            print(i, row)
            if i == 0:
                continue
            data, comment, amount,	brutto,	refuel,	other, recharges, ppu = row
            try:
                recharges = int(recharges)
            except:
                recharges = 0
            try:
                other = float(other)
            except:
                other = 0
            try:
                ppu = float(ppu)
            except:
                ppu = 0
            vals = (data, 'electric', brutto, amount,  ppu, comment, refuel, other, recharges)
            active_table.addNewRow(cols, vals)

    db = mysql_rm.DataBase(conf.credentials)
    db.export_database(None)


def convertDatumFormat4SQL(datum):
    # print(sys._getframe().f_code.co_name)
    # newDate = datetime.strptime(datum, '%d.%m.%y')
    for fmt in ('%Y-%m-%d','%Y_%m_%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y', '%d.%m.%y'):
        try:
            newDate = datetime.strptime(datum, fmt)
            return newDate.date()
        except ValueError:
            pass
    raise ValueError('no valid date format found')



def main():
    script_start_time = time.time()
    selectedStartDate = date(2023, 11, 20)
    selectedEndDate = date(2023, 11, 30)

    # chelt_db = r"D:\Python\MySQL\cheltuieli_db.ini"
    chelt_db = r"D:\Python\MySQL\masina.ini"
    ini_file = r"C:\_Development\Diverse\pypi\cfgmRN.ini"


    conf = connect.Config(ini_file)
    print(conf.credentials)
    print(conf.db_type)
    # print(type(conf.credentials))
    # active_table = mysql_rm.Table(conf.credentials, 'hyundai_ioniq')

    # dir = r'D:\Documente\Masina\Hyundai Ioniq\Consum\IoniqElectroLaden\SWM'
    # all = os.listdir(dir)
    # found = 0
    # for fl in all:
    #     print(fl)
    #     date_str = fl[:10]
    #     # print(date_str)
    #     date_d = convertDatumFormat4SQL(date_str)
    #     # print(date_d, type(date_d))
    #     # print(date_d)
    #     matches = [('type', 'electric'), ('data', date_d), ('comment', 'SWM')]
    #     ids = active_table.returnCellsWhere('id', matches)
    #     # print('....', ids)
    #     if len(ids) == 1:
    #         id_i = ids[0]
    #         inpFile = os.path.join(dir, fl)
    #         print(fl)
    #         v = active_table.convertToBinaryData(inpFile)
    #         active_table.changeCellContent('file', v, 'id', id_i)
    #         active_table.changeCellContent('file_name', fl, 'id', id_i)
    #         # print(fl, date_d, id_i)
    #         found += 1
    #     elif len(ids) == 0:
    #         print('NOT FOUND', fl, date_d)
    #     elif len(ids) > 1:
    #         print('MORE', fl, date_d)
    # print('total_chitante {} total importate {}'.format(len(all), found))


    # inpFile = r"D:\Documente\Masina\Hyundai Ioniq\Consum\IoniqElectroLaden\EnBW\2022-07-05 Rechnung_2022_06_DE_180010096839.pdf"
    # v = active_table.convertToBinaryData(inpFile)
    # active_table.changeCellContent('file', v, 'id', 613)


    # pth = r"D:\Python\MySQL\cheltuieli_online\src\rappmysql\static\sql\auto.sql"
    # active_db = mysql_rm.DataBase(conf.credentials)
    # active_db.createTableFromFile(pth)

    scrip_end_time = time.time()
    duration = scrip_end_time - script_start_time
    duration = time.strftime("%H:%M:%S", time.gmtime(duration))
    print('run time: {}'.format(duration))


if __name__ == '__main__':
    main()
