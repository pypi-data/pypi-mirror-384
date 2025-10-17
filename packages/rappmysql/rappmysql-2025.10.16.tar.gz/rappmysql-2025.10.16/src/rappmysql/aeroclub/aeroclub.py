import csv
import os
import sys
import re
import zipfile
import numpy as np
from datetime import datetime, timedelta
import dateutil.parser as dparser
import pathlib
import shutil
import rappmysql
from rappmysql.mysqlquerys import connect
from rappmysql.mysqlquerys import mysql_rm

np.set_printoptions(linewidth=250)

app_aeroclub = {'docs': 'id_users', 'flight_logs': 'id_users', 'csv_logs': 'id_users'}
app_aeroclub_gui = ['aeroclub.ui']


def convert_timedelta(duration):
    days, seconds = duration.days, duration.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return days, hours, minutes, seconds


def put_files_in_dirs(src_dir):
    dirs = {}
    srcDir = pathlib.Path(src_dir)
    for media_file in srcDir.iterdir():
        if media_file.is_file():
            if re.search("^\d{8}_\d{6}", media_file.name):
                name = re.search("^\d{8}_\d{6}", media_file.name)
                name_datum = mysql_rm.convertDateTimeFormat4SQL(name.group()).date()
            elif re.search("IMG-\d{8}-", media_file.name):
                name = re.search("IMG-\d{8}-", media_file.name)
                name_datum = name.group().split('-')[1]
                name_datum = mysql_rm.convertDatumFormat4SQL(name_datum)
            if name_datum not in dirs.keys():
                dirs[name_datum] = [media_file]
            else:
                dirs[name_datum].append(media_file)

            dir_name = str(name_datum)

            newdir = media_file.parent / dir_name
            if not newdir.exists():
                os.makedirs(newdir)
            shutil.move(media_file, newdir)


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


class CheckAeroclubRequiredFiles:
    def __init__(self, ini_file):
        if isinstance(ini_file, dict):
            self.credentials = ini_file
        else:
            self.conf = connect.Config(ini_file)
            self.credentials = self.conf.credentials

        self.aeroclub_db = None
        path2GUI = pathlib.Path(__file__)
        self.path2GUI = path2GUI.resolve(path2GUI).parent / 'GUI'
        self.pth2SQLtables = os.path.join(os.path.dirname(__file__), 'static', 'sql')

        self.check_connec_to_aer_db()
        self.check_aer_sql_gui_files()
        self.check_tabels_in_aer_db()
        self.table_zbor_log = mysql_rm.Table(self.conf.credentials, 'flight_logs')
        self.table_docs = mysql_rm.Table(self.conf.credentials, 'docs')
        self.csv_logs = mysql_rm.Table(self.conf.credentials, 'csv_logs')

    def check_connec_to_aer_db(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(
            __name__, __class__, sys._getframe().f_code.co_name,sys._getframe().f_back.f_code.co_name))
        if not isinstance(self.credentials, dict):
            raise RuntimeError('Credentials not dict')
        self.aeroclub_db = mysql_rm.DataBase(self.credentials)
        if not self.aeroclub_db.is_connected:
            raise RuntimeError('Could not connect to database')
        print('Connected to database:', self.aeroclub_db.is_connected)

    def check_aer_sql_gui_files(self, ):
        for table in app_aeroclub.keys():
            sql_file = os.path.join(self.pth2SQLtables, '{}_template.sql'.format(table))
            print('##sql_table_template##', sql_file)
            if not os.path.exists(sql_file):
                raise FileNotFoundError('{}'.format(sql_file))

        for gui in app_aeroclub_gui:
            sql_file = os.path.join(self.path2GUI, gui)
            print('##gui_file##', sql_file)
            if not os.path.exists(sql_file):
                raise FileNotFoundError('{}'.format(sql_file))

    def check_tabels_in_aer_db(self):
        for table in app_aeroclub.keys():
            # print('##table##', table)
            sql_file = os.path.join(self.pth2SQLtables, '{}_template.sql'.format(table))
            if table not in self.aeroclub_db.allAvailableTablesInDatabase:
                print('Table {} not in database...creating it'.format(table))
                self.aeroclub_db.createTableFromFile(sql_file, table)
            else:
                # exec("sqltable = mysql_rm.Table(self.credentials, '{}')".format(table))
                varName = 'table_{}'.format(table)
                # print("{} = mysql_rm.Table(self.credentials, '{}')".format(varName, table))
                # print('ÄÄ', varName)
                loc = locals()
                # print(loc)
                exec("{} = mysql_rm.Table(self.credentials, '{}')".format(varName, table), globals(), loc)
                varName = loc[varName]
                same = varName.compare_sql_file_to_sql_table(sql_file)
                if same is not True:
                    print(same)


class AeroclubApp:
    def __init__(self, ini_file, user_id):
        # super().__init__(ini_file)
        self.id = user_id
        if isinstance(ini_file, dict):
            self.credentials = ini_file
        else:
            self.conf = connect.Config(ini_file)
            self.credentials = self.conf.credentials

        self.aeroclub_db = None
        self.aeroclub_db = mysql_rm.DataBase(self.credentials)
        self.table_zbor_log = mysql_rm.Table(self.conf.credentials, 'flight_logs')
        self.table_docs = mysql_rm.Table(self.conf.credentials, 'docs')
        self.csv_logs = mysql_rm.Table(self.conf.credentials, 'csv_logs')

    def zip_profile_files(self, src_dir, output_file):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        relroot = os.path.abspath(os.path.join(src_dir, os.pardir))
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zip:
            for root, dirs, files in os.walk(src_dir):
                # add directory (needed for empty dirs)
                zip.write(root, os.path.relpath(root, relroot))
                for file in files:
                    filename = os.path.join(root, file)
                    if os.path.isfile(filename):  # regular files only
                        arcname = os.path.join(os.path.relpath(root, relroot), file)
                        zip.write(filename, arcname)
        return output_file

    def export_aeroclub_profile(self, output_dir=None, export_files=False):
        # chelt_plan_ident = {'id_users': self.id}
        # yearly_plan_ident = {'id_users': self.id}
        # tables = {'chelt_plan': chelt_plan_ident,
        #           'yearly_plan': yearly_plan_ident}
        # print(tables)
        tables = {}
        for tab in app_aeroclub:
            tables[tab] = {'id_users': self.id}

        # print(25*'+')
        # print(print(tables))
        # return
        tim = datetime.strftime(datetime.now(), '%Y_%m_%d__%H_%M_%S')
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(__file__), 'static', 'backup_profile',
                                      '{:09d}'.format(self.id),
                                      '{}_{:09d}'.format(tim, self.id))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if export_files:
            sql_query = self.aeroclub_db.return_sql_text(tables, export_files=output_dir)
        else:
            sql_query = self.aeroclub_db.return_sql_text(tables)

        output_sql_file = os.path.join(output_dir, '{}_{:09d}.sql'.format(tim, self.id))
        FILE = open(output_sql_file, "w", encoding="utf-8")
        FILE.writelines(sql_query)
        FILE.close()
        #####
        output_zip = os.path.join(os.path.dirname(output_dir), '{}.zip'.format(output_dir))
        zip_file = self.zip_profile_files(output_dir, output_zip)
        if os.path.exists(zip_file):
            shutil.rmtree(output_dir)
        print('finished backup', output_zip)
        return output_sql_file

    def import_aeroclub_profile(self, zip_file, import_files=False):
        output_dir, file = os.path.split(zip_file)
        src_dir = self.unzip_profile_files(zip_file, output_dir)
        src_dir = os.path.join(src_dir, file[:-4])
        if not os.path.exists(src_dir):
            raise RuntimeError('Missing Folder {}'.format(src_dir))

        sql_files = [x for x in os.listdir(src_dir) if x.endswith('.sql')]
        sql_file = os.path.join(src_dir, sql_files[0])
        # print(sql_file)
        # return
        self.aeroclub_db.run_sql_file(sql_file)
        if import_files:
            attachments = [x for x in os.listdir(src_dir) if
                           (x.endswith('.jpg') or
                            x.endswith('.pdf') or
                            x.endswith('.csv') or
                            x.endswith('.CSV')
                            )]
            tab = []
            for file_name in attachments:
                try:
                    # print(file_name)
                    table_id, orig_name = file_name.split('+')
                    fil = os.path.join(src_dir, file_name)
                    self.alimentari.changeCellContent('file', fil, 'id', table_id)
                    self.alimentari.changeCellContent('file_name', str(orig_name), 'id', table_id)
                    # print(user_id, table_name, table_id, orig_name)
                except:
                    print('could not import {}, name not ok'.format(file_name))
                tup = (table_id, orig_name, file_name)
                tab.append(tup)
            # tab = np.atleast_2d(tab)
            # all_sql_tables = list(np.unique(tab[:, 1]))
            # for table_name in all_sql_tables:
            #     # print('table_name', table_name)
            #     sql_table = mysql_rm.Table(self.credentials, table_name)
            #     table = tab[tab[:, 1] == table_name]
            #     for row in table:
            #         user_id, table_name, table_id, orig_name, fl_name = row
            #         # print('&', user_id, table_name, table_id, orig_name, fl_name)
            #         fil = os.path.join(src_dir, fl_name)
            #         sql_table.changeCellContent('file', fil, 'id', table_id)
            #         sql_table.changeCellContent('file_name', str(orig_name), 'id', table_id)
        if os.path.exists(src_dir):
            shutil.rmtree(src_dir)

    def erase_autoapp_traces(self):
        # for i in self.chelt_db.checkProcess():
        #     print(i)
        self.aeroclub_db.killAllProcess()
        self.aeroclub_db.drop_table_list(list(app_aeroclub.keys()))


class AeroclubSQL:
    def __init__(self, ini_file):
        if isinstance(ini_file, dict):
            self.credentials = ini_file
        else:
            self.conf = connect.Config(ini_file)
            self.credentials = self.conf.credentials

        self.aeroclub_db = mysql_rm.DataBase(self.credentials)
        self.table_zbor_log = mysql_rm.Table(self.conf.credentials, 'flight_logs')
        self.table_docs = mysql_rm.Table(self.conf.credentials, 'docs')
        self.csv_logs = mysql_rm.Table(self.conf.credentials, 'csv_logs')

    @property
    def sql_rm(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if self.conf.db_type == 'mysql':
            sql_rm = mysql_rm
        return sql_rm

    def csv_table_head_conversion(self, csv_table_head):
        # print('csv_table_head', csv_table_head)
        table_head_conversion = {}
        table_head_conversion['vereinsflieger_csv_1'] = {'Lfz.': 'plane',
                                                         'Datum': 'flight_date',
                                                         'Pilot': 'pilot',
                                                         'Start': 'start',
                                                         'Landung': 'land',
                                                         'Zeit': 'flight_time',
                                                         'Startort': 'place_from',
                                                         'Landeort': 'place_to',
                                                         'Landungen': 'landings'
                                                         }
        table_head_conversion['vereinsflieger_csv_2'] = {'Lfz.': 'plane',
                                                         'Datum': 'flight_date',
                                                         'Pilot': 'pilot',
                                                         'Start': 'start',
                                                         'Landung': 'land',
                                                         'Flugzeit': 'flight_time',
                                                         'Startort': 'place_from',
                                                         'Landeort': 'place_to',
                                                         'Landungen': 'landings'
                                                         }
        table_head_conversion['fly_is_fun_csv'] = {'Inmatr. Avion': 'plane',
                                                   # 'AerodromDecolare': 'place_from',
                                                   'DataDecolare': 'flight_date',
                                                   'Decolare': 'start',
                                                   'Aterizare': 'land',
                                                   'Timp': 'flight_time',
                                                   'AerodromDecolare': 'place_from',
                                                   'AerodromAterizare': 'place_to',
                                                   'Nr. Aterizari': 'landings'
                                                   }
        table_head_conversion['fly_demon_csv'] = {'Aircraft': 'plane',
                                                  'Pilot': 'pilot',
                                                  'Landing Time': 'land',
                                                  'Flight Length': 'flight_time'
                                                  }
        for csv_from, csv_conv_dict in table_head_conversion.items():
            asta_e = True
            for col in list(csv_conv_dict.keys()):
                if col not in csv_table_head:
                    # if csv_from == 'fly_is_fun_csv':
                    #     # print(col)
                    asta_e = False
            if asta_e:
                return csv_from, csv_conv_dict

    def get_csv_provider(self, inpFile):
        tableHead = None
        with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
            linereader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for i, row in enumerate(linereader):
                if i == 0:
                    tableHead = [c.strip('"') for c in row]
                    # print(tableHead, len(tableHead))
        if len(tableHead) > 1:
            csv_from, tabHeadDict = self.csv_table_head_conversion(tableHead)
        else:
            with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
                linereader = csv.reader(csvfile, delimiter=';', quotechar='"')
                # print('+++', linereader[0])
                for i, row in enumerate(linereader):
                    if i == 0:
                        tableHead = [c.strip('"') for c in row]
                        # print(tableHead, len(tableHead))
            csv_from, tabHeadDict = self.csv_table_head_conversion(tableHead)
        return csv_from, tabHeadDict

    def import_flydemon_csv(self, inpFile):
        cols = []
        vals = []
        with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
            linereader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for i, row in enumerate(linereader):
                if i == 0:
                    tableHead = [c.strip('"') for c in row]
                    csv_from, tabHeadDict = self.csv_table_head_conversion(tableHead)
                    continue
                sql_table_head = list(tabHeadDict.keys())
                cols = []
                row_vals = []
                for ir, v in enumerate(row):
                    csvColName = tableHead[ir]
                    if csvColName in sql_table_head:
                        sqlColName = tabHeadDict[csvColName]
                        if sqlColName not in cols:
                            cols.append(sqlColName)
                        if sqlColName == 'flight_date':
                            v = self.table_zbor_log.convertDatumFormat4SQL(v)
                        elif (sqlColName == 'Start') or (sqlColName == 'Landung'):
                            v = self.table_zbor_log.convertTimeFormat4SQL(v)
                        row_vals.append(v)
                    else:
                        if csvColName == 'Log Name':
                            place_from, place_to = v.split('-')
                            if 'place_from' not in cols:
                                cols.append('place_from')
                            if 'place_to' not in cols:
                                cols.append('place_to')
                            row_vals.append(place_from)
                            row_vals.append(place_to)
                        elif csvColName == 'Takeoff Time':
                            v = self.table_zbor_log.convertDateTimeFormat4SQL(v)
                            flight_date = v.date()
                            start = v.time()
                            if 'flight_date' not in cols:
                                cols.append('flight_date')
                            if 'start' not in cols:
                                cols.append('start')
                            row_vals.append(flight_date)
                            row_vals.append(start)
                        else:
                            continue
                vals.append(tuple(row_vals))
        return cols, vals

    def import_fly_is_fun_csv(self, inpFile):
        cols = []
        vals = []
        with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
            linereader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for i, row in enumerate(linereader):
                if i == 0:
                    tableHead = [c.strip('"') for c in row]
                    csv_from, tabHeadDict = self.csv_table_head_conversion(tableHead)
                    continue
                sql_table_head = list(tabHeadDict.keys())

                row_vals = []
                for ir, v in enumerate(row):
                    csvColName = tableHead[ir]
                    if csvColName in sql_table_head:
                        sqlColName = tabHeadDict[csvColName]
                        if sqlColName not in cols:
                            cols.append(sqlColName)
                        if sqlColName == 'flight_date':
                            v = self.table_zbor_log.convertDatumFormat4SQL(v)
                        elif (sqlColName == 'start') or (sqlColName == 'land') or (sqlColName == 'flight_time'):
                            v = self.table_zbor_log.convertTimeFormat4SQL(v)
                        row_vals.append(v)
                    else:
                        # print(csvColName)
                        if csvColName == 'Log Name':
                            place_from, place_to = v.split('-')
                            # print(place_from, place_to)
                            if 'place_from' not in cols:
                                cols.append('place_from')
                            if 'place_to' not in cols:
                                cols.append('place_to')
                            row_vals.append(place_from)
                            row_vals.append(place_to)
                        elif csvColName == 'Takeoff Time':
                            v = self.table_zbor_log.convertDateTimeFormat4SQL(v)
                            flight_date = v.date()
                            start = v.time()
                            if 'flight_date' not in cols:
                                cols.append('flight_date')
                            if 'start' not in cols:
                                cols.append('start')
                            row_vals.append(flight_date)
                            row_vals.append(start)
                        else:
                            continue
                row_vals.append(inpFile)
                vals.append(tuple(row_vals))
        cols.append('path_to_log')
        return cols, vals

    def import_vereinsflieger_in_sql(self, inpFile):
        cols = []
        vals = []
        with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
            linereader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for i, row in enumerate(linereader):
                print(i, row, type(row), len(row))
                if i == 0:
                    tableHead = [c.strip('"') for c in row]
                    csv_from, tabHeadDict = self.csv_table_head_conversion(tableHead)
                    continue
                elif len(row) == 1 and 'Zeitspanne' in row[0]:
                    continue
                sql_table_head = list(tabHeadDict.keys())

                row_vals = []
                for ir, v in enumerate(row):
                    csvColName = tableHead[ir]
                    if csvColName in sql_table_head:
                        sqlColName = tabHeadDict[csvColName]
                        if sqlColName not in cols:
                            cols.append(sqlColName)
                        if sqlColName == 'flight_date':
                            v = self.table_zbor_log.convertDatumFormat4SQL(v)
                        elif (sqlColName == 'Start') or (sqlColName == 'Landung'):
                            v = self.table_zbor_log.convertTimeFormat4SQL(v)
                        elif sqlColName == 'flight_time':
                            v = timedelta(minutes=int(v))
                        row_vals.append(v)
                # row_vals.append(os.path.split(inpFile[1]))
                # print('..-.', inpFile)
                vals.append(tuple(row_vals))
        # cols.append('path_to_log')
        return cols, vals

    def get_price_per_time(self, avion, flight_times):
        take_off, landing = flight_times
        pph = self.table_docs.returnCellWhereValueIsInIntervalAND('pph', 'name', avion, 'valid_from', take_off,
                                                                  'valid_to')
        # print('****', pph)
        try:
            pph = float(pph[0][0])
        except:
            return None
        ppm = pph / 60
        flight_time = landing - take_off
        flight_mins = flight_time.seconds / 60
        price = flight_mins * ppm
        return round(price, 2)

    def fill_in_pph(self):
        for zbor in self.table_zbor_log.returnAllRecordsFromTable():
            id = zbor[self.table_zbor_log.columnsNames.index('id')]
            plane = zbor[self.table_zbor_log.columnsNames.index('plane')]
            flight_date = zbor[self.table_zbor_log.columnsNames.index('flight_date')]
            start = zbor[self.table_zbor_log.columnsNames.index('start')]
            land = zbor[self.table_zbor_log.columnsNames.index('land')]
            days, hours, minutes, seconds = convert_timedelta(start)
            start = datetime(flight_date.year, flight_date.month, flight_date.day, hours, minutes, seconds)
            days, hours, minutes, seconds = convert_timedelta(land)
            land = datetime(flight_date.year, flight_date.month, flight_date.day, hours, minutes, seconds)
            price = self.get_price_per_time(plane, (start, land))
            self.table_zbor_log.changeCellContent('price_hour', price, 'id', id)

    def getVideo(self, path):
        foundDirs = []
        dir = os.listdir(path)
        for d in dir:
            pth = os.path.join(path, d)
            if os.path.isdir(pth):
                try:
                    match = re.search(r'\d{4}.\d{2}.\d{2}', d)
                    name = d[match.span()[1]:]
                    date = datetime.strptime(match.group(), '%Y.%m.%d').date()
                    tup = (date, name, pth)
                    foundDirs.append(tup)
                except:
                    try:
                        match = re.search(r'\d{4}-\d{2}-\d{2}', d)
                        name = d[match.span()[1]:]
                        date = datetime.strptime(match.group(), '%Y-%m-%d').date()
                        tup = (date, name, pth)
                        foundDirs.append(tup)
                    except:
                        print('**--**', d)
                        continue

        for row in foundDirs:
            data, name, pth = row

            matches = [('flight_date', data)]
            row_id = self.table_zbor_log.returnCellsWhere('id', matches)
            if not row_id:
                print('*=', data, name, pth)
                continue
            for id in row_id:
                self.table_zbor_log.changeCellContent('name', str(name), 'id', id)
                self.table_zbor_log.changeCellContent('path2video', str(pth), 'id', id)

    def already_in_mysql(self, plane, flight_date, start):
        match1 = ('flight_date', flight_date)
        match2 = ('start', start)
        match3 = ('plane', plane)
        matches = [match1, match2, match3]
        res = self.table_zbor_log.filterRows(matches)
        return res

    def import_csv(self, csv_file):
        csv_from, tabHeadDict = self.get_csv_provider(csv_file)

        if 'vereinsflieger' in csv_from:
            cols, vals = self.import_vereinsflieger_in_sql(csv_file)
        elif 'demon' in csv_from:
            cols, vals = self.import_flydemon_csv(csv_file)
        elif 'is_fun' in csv_from:
            cols, vals = self.import_fly_is_fun_csv(csv_file)
        # cols.sort()
        print(cols, len(cols))

        # print(vals, len(vals))
        imported = 0
        not_imported = 0
        total = 0
        imported_flight_dates = []
        for row in vals:
            total += 1
            # row.append(csv_file)
            plane, flight_date, start = row[cols.index('plane')], row[cols.index('flight_date')], row[cols.index('start')]
            imported_flight_dates.append(flight_date)
            already_in_sql = self.already_in_mysql(plane, flight_date, start)
            if already_in_sql:
                print('&&&', row)
                not_imported += 1
            else:
                print('*', row)
                self.table_zbor_log.addNewRow(cols, row)
                imported += 1
        print('total {}, imported {}, not_imported {}'.format(total, imported, not_imported))
        # self.fill_in_pph()
        start = min(imported_flight_dates)
        end = max(imported_flight_dates)
        self.add_row_to_imported_csv(csv_file, start, end, total, imported)

    def add_row_to_imported_csv(self, inpFile, start, end, total_rows, imported_rows):
        cols = ['file_name', 'start', 'end', 'file', 'total_rows', 'imported_rows']
        path, file_name = os.path.split(inpFile)
        vals = [file_name, start, end, inpFile, total_rows, imported_rows]
        self.csv_logs.addNewRow(cols, tuple(vals))

    def import_all_csv_in_dir(self, src_dir):
        srcDir = pathlib.Path(src_dir)
        for csv_file in srcDir.glob('*.csv'):  # rglob
            self.import_csv(csv_file)

    def get_not_paid_flights(self):
        payments = {}
        match1 = ('paid', 0)
        res = self.table_zbor_log.returnRowsWhere(match1)
        total = 0
        for row in res:
            plane = row[self.table_zbor_log.columnsNames.index('plane')]
            price = row[self.table_zbor_log.columnsNames.index('price_hour')]
            total += price
            if plane not in payments.keys():
                payments[plane] = price
            else:
                payments[plane] += price
        payments['total'] = total
        return payments

    @property
    def default_interval(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        startDate = datetime(datetime.now().year, 1, 1)
        endDate = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
        return startDate, endDate

    @property
    def all_airplanes_registrations(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        col_plane = list(set(self.table_zbor_log.returnColumn('plane')))
        return col_plane

    def get_monthly_interval(self, month: str, year):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        mnth = datetime.strptime(month, "%B").month
        startDate = datetime(year, mnth, 1)

        if mnth != 12:
            lastDayOfMonth = datetime(year, mnth + 1, 1) - timedelta(days=1)
        else:
            lastDayOfMonth = datetime(year + 1, 1, 1) - timedelta(days=1)

        return startDate, lastDayOfMonth

    def get_flights_for_interval_type(self, selectedStartDate, selectedEndDate, airplane):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        matches = [('flight_date', (selectedStartDate, selectedEndDate)),
                   ]
        if airplane:
            matches.append(('plane', airplane))
        print(matches)
        table = self.table_zbor_log.filterRows(matches, order_by=('flight_date', 'DESC'))

        if table:
            table_head = []
            for col_name, prop in self.table_zbor_log.columnsDetProperties.items():
                # print(col_name, prop)
                if prop[0] == 'longblob':
                    continue
                table_head.append(col_name)
            arr = np.atleast_2d(table)
            arr = np.insert(arr, 0, np.array(table_head), axis=0)
        else:
            arr = np.atleast_2d(np.array(self.table_zbor_log.columnsNames))
        return arr

    @property
    def total_unpaid_flights(self):
        not_paid_dict =self.get_not_paid_flights()
        return not_paid_dict['total']

    @property
    def flight_time_this_year(self):
        selectedStartDate, selectedEndDate = self.default_interval
        arr = self.get_flights_for_interval_type(selectedStartDate, selectedEndDate, airplane=None)
        col = arr[1:, self.table_zbor_log.columnsNames.index('flight_time')]
        return sum(col, timedelta())

    @property
    def total_flight_time(self):
        col = self.table_zbor_log.returnColumn('flight_time')
        total = sum(col, timedelta())
        # print(total)
        totsec = total.total_seconds()
        h = totsec // 3600
        m = (totsec % 3600) // 60
        sec = (totsec % 3600) % 60  # just for reference
        return"%d:%d" % (h, m)


def main():
    src_dir = r"D:\Aeroclub\Zbor"
    src_dir = r"E:\Aviatie\Filmulete zbor"
    # put_files_in_dirs(src_dir)

    ins = AeroclubSQL(rappmysql.ini_aeroclub)
    ins.fill_in_pph()
    # print(ins.get_not_paid_flights())
    # print(ins.total_unpaid_flights)
    # print(ins.flight_time_this_year)
    # print(ins.total_flight_time)
    return

    # ins.getVideo(src_dir)
    # return
    # # inpDir = r"D:\Documente\Radu\Aeroclub\Flight_Log"
    # # ins.import_all_csv_in_dir(inpDir)

    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\fly_is_fun_bis_2014.csv"
    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\fly_is_fun_11.07.2015 bis 25.09.2017.csv"
    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\Export_VEREINSFLIEGER_30.09.2017_10.10.2021.csv"
    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\Export_VEREINSFLIEGER_11.10.2021_17.09.2024.csv"
    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\Export_VEREINSFLIEGER_21.09.2024_07.10.2024.csv"
    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\Export_VEREINSFLIEGER_May_2025.csv"
    ins.import_csv(csv)

    # start = datetime(2024, 5, 11, 7, 58, 0)
    # end = datetime(2024, 5, 11, 8, 22, 0)
    # pph = ins.get_price_per_time("D-MENF", (start, end))
    # # start = datetime(2024, 9, 8, 12, 39, 0)
    # # end = datetime(2024, 9, 8, 13, 6, 0)
    # # pph = ins.get_price_per_time("D-MOEO", (start, end))
    # print(pph)


if __name__ == '__main__':
    # inpFile = r"D:\Documente\Aeroclub\Bad_Endorf\Export.csv"

    # write2flightTable(inpFile)
    # quartals = ['Q1', 'Q2', 'Q3', 'Q4']
    # for year in range(2022, 2023):
    #     for q in quartals:
    #         interval = getQuartalDates(q, year)
    #         print(interval)
    # #         price = getPrice4Time(interval[0], interval[1])
    # #         print(year, q, price)
    # # pth = r"E:\Aviatie\Filmulete zbor"
    # # getVideo(pth)
    main()
