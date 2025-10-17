import numpy as np
import shutil
import rappmysql
from rappmysql.mysqlquerys import connect
from rappmysql.mysqlquerys import mysql_rm
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import traceback
import sys, os
import time
import pathlib
import zipfile

np.set_printoptions(linewidth=250)
compName = os.getenv('COMPUTERNAME')
# try:
#     compName = os.getenv('COMPUTERNAME')
#     if compName == 'DESKTOP-5HHINGF':
#         ini_users = r"D:\Python\MySQL\users.ini"
#         ini_chelt = r"D:\Python\MySQL\cheltuieli.ini"
#         ini_masina = r"D:\Python\MySQL\masina.ini"
#         report_dir = r"D:\Python\MySQL\onlineanywhere\static"
#     else:
#         ini_users = r"C:\_Development\Diverse\pypi\cfgm.ini"
#         ini_chelt = r"C:\_Development\Diverse\pypi\cfgm.ini"
#         ini_masina = r"C:\_Development\Diverse\pypi\cfgm.ini"
#         # ini_file = r"C:\_Development\Diverse\pypi\cfgmRN.ini"
#         report_dir = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\static"
# except:
#     ini_users = '/home/radum/mysite/static/wdb.ini'

app_masina_tables = {'all_cars': 'id_users', 'masina': 'id_users'}
app_masina_gui = ['masina.ui', 'add_auto.ui']


class CheckAutoRequiredFiles:
    def __init__(self, ini_file):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        if isinstance(ini_file, dict):
            self.credentials = ini_file
        else:
            self.conf = connect.Config(ini_file)
            self.credentials = self.conf.credentials
        self.auto_db = None
        path2GUI = pathlib.Path(__file__)
        self.path2GUI = path2GUI.resolve(path2GUI).parent / 'GUI'
        self.pth2SQLtables = os.path.join(os.path.dirname(__file__), 'static', 'sql')
        # self.all_cars_table = mysql_rm.Table(self.credentials, 'all_cars')
        # self.alimentari = mysql_rm.Table(self.credentials, 'masina')
        self.check_requirements()

    def check_requirements(self):
        self.check_connection_to_database()
        self.check_sql_gui_files_existance()
        self.check_tabels_in_database()

    def check_connection_to_database(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(
            __name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        if not isinstance(self.credentials, dict):
            raise RuntimeError('Credentials not dict')
        self.auto_db = mysql_rm.DataBase(self.credentials)
        if not self.auto_db.is_connected:
            raise RuntimeError('Could not connect to database')
        print('Connected to auto_db:', self.auto_db.is_connected)

    def check_sql_gui_files_existance(self, ):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        for table in app_masina_tables.keys():
            sql_file = os.path.join(self.pth2SQLtables, '{}_template.sql'.format(table))
            print('##sql_table_template##', sql_file)
            if not os.path.exists(sql_file):
                raise FileNotFoundError('{}'.format(sql_file))

        for gui in app_masina_gui:
            sql_file = os.path.join(self.path2GUI, gui)
            print('##gui_file##', sql_file)
            if not os.path.exists(sql_file):
                raise FileNotFoundError('{}'.format(sql_file))

    def check_tabels_in_database(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        for table in app_masina_tables.keys():
            # print('##table##', table)
            sql_file = os.path.join(self.pth2SQLtables, '{}_template.sql'.format(table))
            if table not in self.auto_db.allAvailableTablesInDatabase:
                print('Table {} not in database...creating it'.format(table))
                self.auto_db.createTableFromFile(sql_file, table)
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


class AutoApp:
    def __init__(self, ini_masina, user_id):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        # super().__init__(ini_masina)
        self.id = user_id
        if isinstance(ini_masina, dict):
            self.credentials = ini_masina
        else:
            self.conf = connect.Config(ini_masina)
            self.credentials = self.conf.credentials
        self.auto_db = mysql_rm.DataBase(self.credentials)
        self.all_cars_table = mysql_rm.Table(self.credentials, 'all_cars')
        self.alimentari = mysql_rm.Table(self.credentials, 'masina')

    @property
    def masini(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        masini = {}
        matches = ('id_users', self.id)
        cars_rows = self.all_cars_table.returnRowsWhere(matches)
        if cars_rows:
            for row in cars_rows:
                print('***row', row)
                indx_id = self.all_cars_table.columnsNames.index('id')
                indx_brand = self.all_cars_table.columnsNames.index('brand')
                indx_model = self.all_cars_table.columnsNames.index('model')
                table_name = '{}_{}'.format(row[indx_brand], row[indx_model])
                masini[row[indx_id]] = table_name
        return masini

    @property
    def electric_providers(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        matches = [('type', 'electric')]
        col = self.alimentari.returnCellsWhere('eProvider', matches)
        electric_providers = list(set(col))
        # electric_providers = ['eCharge', 'MyHyundai', 'EnBW', 'SWM_Plus', 'SWM']
        return electric_providers

    def add_car(self, brand, model, car_type):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        brand = brand.lower()
        model = model.lower()
        car_type = car_type.lower()
        cols = ('id_users', 'brand', 'model', 'cartype')
        vals = (self.id, brand, model, car_type)
        matches = [('id_users', self.id), ('brand', brand), ('model', model), ('cartype', car_type)]
        existing_row = self.all_cars_table.returnRowsWhere(matches)
        # print('existing_row', existing_row)
        if existing_row:
            print('car already existing at id {}'.format(existing_row[0][0]))
            return
        else:
            self.all_cars_table.addNewRow(cols, vals)
            # new_auto_table = '{}_{}'.format(brand, model)
            # new_auto_table = new_auto_table.lower()
            # if new_auto_table in self.auto_db.allAvailableTablesInDatabase:
            #     print('table {} existing in database'.format(new_auto_table))
            # else:
            #     pth_auto_template = os.path.join(os.path.dirname(__file__), 'static', 'sql', 'auto_template.sql')
            #     self.auto_db.createTableFromFile(pth_auto_template, new_auto_table)

    def export_car_sql(self, car_id, export_files=False):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        all_cars_ident = {'id_users': self.id, 'id': car_id}
        masina_ident = {'id_users': self.id, 'id_all_cars': car_id}
        tables = {'all_cars': all_cars_ident,
                  'masina': masina_ident}

        tim = datetime.strftime(datetime.now(), '%Y_%m_%d__%H_%M_%S')
        output_dir = os.path.join(os.path.dirname(__file__), 'static', 'backup_profile',
                                  '{:09d}'.format(self.id),
                                  '{:09d}'.format(car_id),
                                  '{}_{:09d}'.format(tim, car_id))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if export_files:
            sql_query = self.auto_db.return_sql_text(tables, export_files=output_dir)
        else:
            sql_query = self.auto_db.return_sql_text(tables)

        output_sql_file = os.path.join(output_dir, '{}_{:09d}.sql'.format(tim, self.id))
        FILE = open(output_sql_file, "w", encoding="utf-8")
        FILE.writelines(sql_query)
        FILE.close()
        #####
        output_zip = os.path.join(os.path.dirname(output_dir), '{}.zip'.format(output_dir))
        zip_file = self.zip_profile_files(output_dir, output_zip)
        if os.path.exists(zip_file):
            shutil.rmtree(output_dir)
        print('finished backup')

        return output_sql_file

    def import_car_with_files(self, zip_file, import_files=False):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        output_dir, file = os.path.split(zip_file)
        src_dir = self.unzip_profile_files(zip_file, output_dir)
        src_dir = os.path.join(src_dir, file[:-4])
        if not os.path.exists(src_dir):
            raise RuntimeError('Missing Folder {}'.format(src_dir))

        sql_files = [x for x in os.listdir(src_dir) if x.endswith('.sql')]
        sql_file = os.path.join(src_dir, sql_files[0])
        # print(sql_file)
        # return
        self.auto_db.run_sql_file(sql_file)
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
                    # print(id_users, table_name, table_id, orig_name)
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
            #         id_users, table_name, table_id, orig_name, fl_name = row
            #         # print('&', id_users, table_name, table_id, orig_name, fl_name)
            #         fil = os.path.join(src_dir, fl_name)
            #         sql_table.changeCellContent('file', fil, 'id', table_id)
            #         sql_table.changeCellContent('file_name', str(orig_name), 'id', table_id)
        if os.path.exists(src_dir):
            shutil.rmtree(src_dir)

    def get_id_all_cars(self, table_name):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        brand, model = table_name.split('_')
        matches = [('id_users', self.id),
                   ('brand', brand),
                   ('model', model),
                   ]
        # print(matches)
        id_all_cars = self.all_cars_table.returnCellsWhere('id', matches)[0]
        return id_all_cars

    def delete_auto(self, table_name):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        brand, model = table_name.split('_')
        matches = [('id_users', self.id), ('brand', brand), ('model', model)]
        id_car = self.all_cars_table.returnCellsWhere('id', matches)
        # print('id_car', id_car)
        condition = ['id', id_car[0]]
        self.all_cars_table.delete_multiple_rows(condition)

    def erase_autoapp_traces(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        # for i in self.chelt_db.checkProcess():
        #     print(i)
        self.auto_db.killAllProcess()
        self.auto_db.drop_table_list(list(app_masina_tables.keys()))

    def unzip_profile_files(self, src_file, output_dir):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        with zipfile.ZipFile(src_file, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        return output_dir

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


class Masina:
    def __init__(self, ini_file, id_users, id_car):
        '''
        :param ini_file:type=QFileDialog.getOpenFileName name=filename file_type=(*.ini;*.txt)
        '''
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        # super().__init__(ini_file)
        self.id_users = id_users
        self.id_car = id_car
        if isinstance(ini_file, dict):
            self.credentials = ini_file
        else:
            self.conf = connect.Config(ini_file)
            self.credentials = self.conf.credentials
        self.auto_db = mysql_rm.DataBase(self.credentials)
        self.all_cars_table = mysql_rm.Table(self.credentials, 'all_cars')
        self.alimentari = mysql_rm.Table(self.credentials, 'masina')

        # if isinstance(ini_file, dict):
        #     credentials = ini_file
        # else:
        #     self.conf = connect.Config(ini_file)
        #     credentials = self.conf.credentials
        # self.checkup_list(credentials)
        # self.alimentari = mysql_rm.Table(self.credentials, 'masina')
        self.types_of_costs = ["electric", "benzina", "intretinere", "asigurare", 'impozit', 'TüV', 'carwash', 'other']
        self.no_of_records = self.get_no_of_records()
        self.total_money = self.get_total_money()
        self.tot_benzina = self.get_tot_benzina()
        self.tot_electric = self.get_tot_electric()
        self.monthly_benzina = self.get_monthly_benzina()
        self.monthly_electric = self.get_monthly_electric()
        self.monthly = self.get_monthly()
        self.db_start_date = self.get_db_start_date()
        self.db_last_record_date = self.get_db_last_record_date()
        self.table_alimentari = self.get_table_alimentari()
        self.dict_totals = self.get_dict_totals()
        self.table_totals = self.get_table_totals()
        self.last_records = self.get_last_records()

    # @property
    def get_no_of_records(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        return self.alimentari.noOfRows

    @property
    def default_interval(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        startDate = datetime(datetime.now().year - 1, datetime.now().month, datetime.now().day)
        endDate = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
        return startDate, endDate

    # @property
    def get_total_money(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        col = self.alimentari.returnColumn('brutto')
        return round(sum(col), 2)

    # @property
    def get_tot_benzina(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        matches = [('type', 'benzina'),
                   ('id_users', self.id_users),
                   ('id_all_cars', self.id_car)]
        col = self.alimentari.returnCellsWhere('brutto', matches)
        return round(sum(col), 2)

    # @property
    def get_tot_electric(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        matches = [('type', 'electric'),
                   ('id_users', self.id_users),
                   ('id_all_cars', self.id_car)]
        col = self.alimentari.returnCellsWhere('brutto', matches)
        return round(sum(col), 2)

    # @property
    def get_monthly(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        try:
            return round((self.monthly_benzina + self.monthly_electric), 2)
        except:
            return None

    # @property
    def get_monthly_benzina(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        try:
            matches = [('type', 'benzina'),
                       ('id_users', self.id_users),
                       ('id_all_cars', self.id_car)]
            rows = self.alimentari.returnRowsWhere(matches)
            rows = np.atleast_2d(rows)
            money = rows[:, self.alimentari.columnsNames.index('brutto')]
            start_date = min(rows[:, self.alimentari.columnsNames.index('data')])
            finish_date = max(rows[:, self.alimentari.columnsNames.index('data')])

            total_money = round(sum(money), 2)

            # print(start_date)
            # print(finish_date)
            # print(total_money)
            days = (finish_date - start_date).days
            # print(days)
            average_day_per_month = 365 / 12
            monthly = (average_day_per_month * total_money) / days
            return round(monthly, 2)
            # return round(5.5555, 2)
        except:
            return None

    # @property
    def get_monthly_electric(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        try:
            matches = [('type', 'electric'),
                       ('id_users', self.id_users),
                       ('id_all_cars', self.id_car)]
            rows = self.alimentari.returnRowsWhere(matches)
            # print(rows)
            # print(type(rows))
            if rows:
                rows = np.atleast_2d(rows)
                money = rows[:, self.alimentari.columnsNames.index('brutto')]
                start_date = min(rows[:, self.alimentari.columnsNames.index('data')])
                finish_date = max(rows[:, self.alimentari.columnsNames.index('data')])
                # print('*****', money, start_date, finish_date)
                total_money = round(sum(money), 2)
                days = (finish_date - start_date).days
                average_day_per_month = 365 / 12
                monthly = (average_day_per_month * total_money) / days
                return round(monthly, 2)
        except:
            return None

    # @property
    def get_db_start_date(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        matches = [('id_users', self.id_users),
                   ('id_all_cars', self.id_car)]
        all_dates = self.alimentari.returnCellsWhere('data', matches)
        # print('**all_dates', all_dates, type(all_dates))
        if all_dates:
            start_date = min(all_dates)
        else:
            start_date = None
        return start_date

    # @property
    def get_db_last_record_date(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        try:
            # all_dates = self.alimentari.returnColumn('data')
            matches = [('id_users', self.id_users),
                       ('id_all_cars', self.id_car)]
            all_dates = self.alimentari.returnCellsWhere('data', matches)
            finish_date = max(all_dates)
            return finish_date
        except:
            return None

    # @property
    def get_table_alimentari(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        arr = [('', 'Alimentari[€]', 'Benzina[€]', 'Electric[€]')]
        if self.no_of_records > 0:
            total_alim = round(self.tot_benzina + self.tot_electric, 2)
            arr.append(('Monthly', self.monthly, self.monthly_benzina, self.monthly_electric))
            arr.append(('Total', total_alim, self.tot_benzina, self.tot_electric))
        else:
            arr.append(('Monthly', None, None, None))
            arr.append(('Total', None, None, None))

        arr = np.atleast_2d(arr)
        return arr

    def dict_last_months(self, delta_mths=12):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        if not self.db_start_date:
            return None
        table_dict = {}
        try:
            for mnth in reversed(range(delta_mths+1)):
                dd = {}
                start_date = date.today() - relativedelta(months=+mnth)
                mnth_as_str = start_date.strftime("%B")
                startTime, endTime = self.get_monthly_interval(mnth_as_str, start_date.year)
                interval = '{}.{}'.format(mnth_as_str[:3], start_date.year)
                # print(startTime, endTime)
                tot = 0
                for t in self.types_of_costs:
                    matches = [('id_users', '=', self.id_users),
                               ('id_all_cars', '=', self.id_car),
                               ('type', '=', t),
                               ('data', '>=', startTime),
                               ('data', '<=', endTime)
                               ]
                    payments4Interval = self.alimentari.returnRowsQuery(matches)
                    if payments4Interval:
                        payments4Interval = np.atleast_2d(payments4Interval)
                        col = payments4Interval[:, self.alimentari.columnsNames.index('brutto')]
                        value = sum(col)
                        value = round(value, 2)
                        dd[t] = value
                        tot += value
                dd['total/row'] = round(tot, 2)
                table_dict[interval] = dd
            return table_dict
        except:
            return str(traceback.format_exc())

    # @property
    def get_dict_totals(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        if not self.db_start_date:
            return None
        table_dict = {}
        try:
            for year in reversed(range(self.db_start_date.year, self.db_last_record_date.year + 1)):
                dd = {}
                startTime = datetime(year, 1, 1)
                endTime = datetime(year, 12, 31)
                tot = 0
                for t in self.types_of_costs:
                    # print('t', t)
                    matches = [('id_users', '=', self.id_users),
                               ('id_all_cars', '=', self.id_car),
                               ('type', '=', t),
                               ('data', '>=', startTime),
                               ('data', '<=', endTime)
                               ]
                    payments4Interval = self.alimentari.returnRowsQuery(matches)
                    if payments4Interval:
                        payments4Interval = np.atleast_2d(payments4Interval)
                        col = payments4Interval[:, self.alimentari.columnsNames.index('brutto')]
                        value = sum(col)
                        value = round(value, 2)
                        dd[t] = value
                        tot += value
                dd['total/row'] = round(tot, 2)
                table_dict[year] = dd
            return table_dict
        except:
            return str(traceback.format_exc())

    # @property
    def get_table_totals(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        try:
            table_head = self.types_of_costs.copy()
            table_totals = []
            for year, expenses in self.dict_totals.items():
                row = [year]
                total_per_year = 0
                for col in table_head:
                    if col in expenses.keys():
                        row.append(expenses[col])
                        total_per_year += expenses[col]
                    else:
                        row.append(0)
                row.append(round(total_per_year, 2))
                table_totals.append(tuple(row))
            table_head.insert(0, 'year')
            table_head.append('tot/year')
            table_totals.insert(0, tuple(table_head))
            table_totals = np.atleast_2d(table_totals)
            return table_totals
        except:
            return None

    # @property
    def get_last_records(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        # print(len(tuple(self.alimentari.columnsNames)))
        table_head = self.alimentari.columnsNames.copy()
        table_head.remove('file')
        last_records = [tuple(table_head)]
        for typ in self.types_of_costs:
            matches = [('id_users', self.id_users),
                       ('id_all_cars', self.id_car),
                       ('type', typ)]
            table = self.alimentari.filterRows(matches, order_by=('data', 'DESC'))
            if table:
                last_records.append(tuple(table[0]))
        last_records = np.atleast_2d(last_records)
        return last_records

    def delete_row(self, row_id):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        condition = ('id', row_id)
        self.alimentari.delete_multiple_rows(condition)

    def get_monthly_interval(self, month: str, year):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        mnth = datetime.strptime(month, "%B").month
        startDate = datetime(year, mnth, 1)

        if mnth != 12:
            lastDayOfMonth = datetime(year, mnth + 1, 1) - timedelta(days=1)
        else:
            lastDayOfMonth = datetime(year + 1, 1, 1) - timedelta(days=1)

        return startDate, lastDayOfMonth

    def get_all_alimentari(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        cols = []
        for k, v in self.alimentari.columnsDetProperties.items():
            if v[0] == 'longblob':
                continue
            cols.append(k)
        alimentari = self.alimentari.returnColumns(cols)
        # alimentari = self.alimentari.returnAllRecordsFromTable()
        alimentari = np.atleast_2d(alimentari)
        alimentari = np.insert(alimentari, 0, cols, axis=0)
        return alimentari

    def get_alimentari_for_interval_type(self, selectedStartDate, selectedEndDate, alim_type):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        matches = [('data', (selectedStartDate, selectedEndDate)),
                   ('id_users', self.id_users),
                   ('id_all_cars', self.id_car)]
        if alim_type:
            matches.append(('type', alim_type))
        print(matches)
        table = self.alimentari.filterRows(matches, order_by=('data', 'DESC'))

        if table:
            table_head = []
            for col_name, prop in self.alimentari.columnsDetProperties.items():
                # print(col_name, prop)
                if prop[0] == 'longblob':
                    continue
                table_head.append(col_name)
            arr = np.atleast_2d(table)
            arr = np.insert(arr, 0, np.array(table_head), axis=0)
        else:
            arr = np.atleast_2d(np.array(self.alimentari.columnsNames))
        return arr

    def upload_file(self, file_name, id):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        self.alimentari.changeCellContent('file', file_name, 'id', id)
        pth, file_name = os.path.split(file_name)
        self.alimentari.changeCellContent('file_name', file_name, 'id', id)

    def insert_new_alim(self, current_id_users, id_all_cars, data, alim_type, brutto, amount, refuel, other, recharges,
                        km, comment, file, provider):
        '''
        :param data:type=dateTime name=date
        :param alim_type:type=comboBox name=alim_type items=[electric,benzina,TüV,intretinere]
        :param brutto:type=text name=brutto
        :param amount:type=text name=amount
        :param refuel:type=text name=refuel
        :param other:type=text name=other
        :param recharges:type=text name=recharges
        :param km:type=text name=km
        :param comment:type=text name=comment
        :param file:type=QFileDialog.getOpenFileName name=file
        '''
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        if file:
            _, file_name = os.path.split(file)
            cols = ['id_users', 'id_all_cars', 'data', 'type', 'brutto', 'amount', 'refuel', 'other', 'recharges',
                    'ppu', 'km', 'comment', 'file', 'file_name', 'eProvider']
        else:
            cols = ['id_users', 'id_all_cars', 'data', 'type', 'brutto', 'amount', 'refuel', 'other', 'recharges',
                    'ppu', 'km', 'comment', 'eProvider']
        try:
            if isinstance(brutto, str) and ',' in brutto:
                brutto = brutto.replace(',', '.')
            brutto = float(brutto)
        except:
            brutto = None
        try:
            if isinstance(amount, str) and ',' in amount:
                amount = amount.replace(',', '.')
            elif amount == '':
                amount = 1
            amount = float(amount)
        except:
            amount = None
        try:
            if isinstance(refuel, str) and ',' in refuel:
                refuel = refuel.replace(',', '.')
            refuel = float(refuel)
        except:
            refuel = None
        try:
            if isinstance(other, str) and ',' in other:
                other = other.replace(',', '.')
            other = float(other)
        except:
            other = None
        try:
            if isinstance(recharges, str) and ',' in recharges:
                recharges = recharges.replace(',', '.')
            recharges = float(recharges)
        except:
            recharges = None
        try:
            km = int(km)
        except:
            km = None

        ppu = round(float(brutto) / float(amount), 3)
        if file:
            vals = [current_id_users, id_all_cars, data, alim_type, brutto, amount, refuel, other, recharges, ppu, km,
                    comment, file, file_name, provider]
        else:
            vals = [current_id_users, id_all_cars, data, alim_type, brutto, amount, refuel, other, recharges, ppu, km,
                    comment, provider]

        self.alimentari.addNewRow(cols, tuple(vals))

    def create_sql_table(self, table_name):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        masina_sql = os.path.join(os.path.dirname(__file__), 'static', 'sql',
                                  'auto_template.sql')

        # masina_sql = r'static\sql\auto.sql'
        mysql_rm.DataBase(self.conf.credentials).createTableFromFile(masina_sql, table_name)

    def last_records_for_plot(self, delta_mths=12):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        plot_lr = {}
        start_date = date.today() - relativedelta(months=+delta_mths)
        # print('start_date', start_date)
        last_rec_tab_head = list(self.last_records[0])
        # print(last_rec_tab_head)
        for lr in self.last_records[1:]:
            # print(lr)
            ali_date = lr[last_rec_tab_head.index('data')]
            recharge_type = lr[last_rec_tab_head.index('type')]
            brutto = lr[last_rec_tab_head.index('brutto')]
            if ali_date > start_date:
                # print('BINGOOOOO')
                total_interval = date.today() - start_date
                interval_since_lr = date.today() - ali_date
                # print(total_interval, interval_since_lr)
                # print(recharge_type, interval_since_lr/total_interval)
                label = '{}_{}_{}'.format(recharge_type, ali_date, brutto)
                plot_lr[label] = interval_since_lr/total_interval
        return plot_lr


def main():
    script_start_time = time.time()
    selectedStartDate = datetime(2024, 7, 15, 0, 0, 0)
    selectedEndDate = datetime(2025, 7, 15, 0, 0, 0)

    # auto_app = AutoApp(rappmysql.ini_masina, 1)
    # print(auto_app.masini)
    app_masina = Masina(rappmysql.ini_masina, 1, 14)
    # alimentari = app_masina.get_alimentari_for_interval_type(selectedStartDate, selectedEndDate, None)
    # for i in alimentari:
    #     print(i)
    # print(len(alimentari))
    # print(app_masina.tot_benzina)
    # print(app_masina.tot_electric)
    print(app_masina.monthly_benzina)
    # print(app_masina.monthly_electric)
    # print(app_masina.dict_totals)
    # print(app_masina.bkp_table_totals)
    # print(app_masina.monthly)
    # dict_last_months = app_masina.dict_last_months()
    # for interval, values in dict_last_months.items():
    #     print(interval)
    #     print(values)
    #     print(type(values))
    # app_masina.last_records_for_plot()
    # print()
    # print(app_masina.table_totals)
    # print('app_masina.last_records')
    # print(app_masina.last_records)

    scrip_end_time = time.time()
    duration = scrip_end_time - script_start_time
    duration = time.strftime("%H:%M:%S", time.gmtime(duration))
    print('run time: {}'.format(duration))


if __name__ == '__main__':
    main()
