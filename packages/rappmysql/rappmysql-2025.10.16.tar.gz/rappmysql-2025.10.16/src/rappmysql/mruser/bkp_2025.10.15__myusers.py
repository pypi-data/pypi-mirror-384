import csv
import os.path
import traceback
import numpy as np
import datetime as dt
from datetime import datetime, timedelta
import time
import sys
import json
import shutil
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import zipfile
import pathlib
import rappmysql
from rappmysql.mysqlquerys import connect, mysql_rm
from rappmysql.aeroclub.aeroclub import AeroclubApp
from rappmysql.masina.auto import AutoApp
from rappmysql.cheltuieli.chelt_plan import CheltApp
import rappmysql.mruser as mruser

compName = os.getenv('COMPUTERNAME')

np.set_printoptions(linewidth=250)

app_tables_users = {'users': 'id', 'user_apps': 'id_users'}
app_users_gui = ['login_window.ui']


def calculate_last_day_of_month(mnth, year):
    if mnth < 12:
        # lastDayOfMonth = datetime(datetime.now().year, mnth + 1, 1) - timedelta(days=1)
        lastDayOfMonth = datetime(year, mnth + 1, 1) - timedelta(days=1)
        lastDayOfMonth = lastDayOfMonth.day
    elif mnth == 12:
        lastDayOfMonth = 31
    return lastDayOfMonth


def calculate_today_plus_x_days(x_days):
    result = datetime(datetime.now().year, datetime.now().month, datetime.now().day) + timedelta(days=int(x_days))
    return result


def default_interval():
    # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    print('Caller : ', sys._getframe().f_back.f_code.co_name)
    startDate = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
    if datetime.now().month != 12:
        mnth = datetime.now().month + 1
        lastDayOfMonth = datetime(datetime.now().year, mnth, 1) - timedelta(days=1)
    else:
        lastDayOfMonth = datetime(datetime.now().year + 1, 1, 1) - timedelta(days=1)

    return startDate, lastDayOfMonth


def get_monthly_interval(month: str, year):
    # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    mnth = datetime.strptime(month, "%B").month
    startDate = datetime(year, mnth, 1)

    if mnth != 12:
        lastDayOfMonth = datetime(year, mnth + 1, 1) - timedelta(days=1)
    else:
        lastDayOfMonth = datetime(year + 1, 1, 1) - timedelta(days=1)

    return startDate.date(), lastDayOfMonth.date()


def convert_to_display_table(tableHead, table, displayTableHead):
    newTableData = np.empty([table.shape[0], len(displayTableHead)], dtype=object)
    for i, col in enumerate(displayTableHead):
        indxCol = tableHead.index(col)
        newTableData[:, i] = table[:, indxCol]
    return displayTableHead, newTableData


class CheckUsersRequiredFiles:
    def __init__(self, ini_file):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        if isinstance(ini_file, dict):
            self.credentials = ini_file
        else:
            self.conf = connect.Config(ini_file)
            self.credentials = self.conf.credentials

        self.users_db = None
        path2GUI = pathlib.Path(__file__)
        self.path2GUI = path2GUI.resolve(path2GUI).parent / 'GUI'
        self.pth2SQLtables = os.path.join(os.path.dirname(__file__), 'static', 'sql')

        # self.check_connec_to_users_db()
        # self.check_users_sql_gui_files()
        # self.check_tabels_in_users_db()
        # self.connect_to_all_databases()

    def check_connec_to_users_db(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        if not isinstance(self.credentials, dict):
            raise RuntimeError('Credentials not dict')
        self.users_db = mysql_rm.DataBase(self.credentials)
        if not self.users_db.is_connected:
            raise RuntimeError('Could not connect to database')
        print('Connected to users_db:', self.users_db.is_connected)

    def check_users_sql_gui_files(self, ):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        for table in app_tables_users.keys():
            sql_file = os.path.join(self.pth2SQLtables, '{}_template.sql'.format(table))
            # print('##sql_table_template##', sql_file)
            if not os.path.exists(sql_file):
                raise FileNotFoundError('{}'.format(sql_file))

        for gui in app_users_gui:
            sql_file = os.path.join(self.path2GUI, gui)
            # print('##gui_file##', sql_file)
            if not os.path.exists(sql_file):
                raise FileNotFoundError('{}'.format(sql_file))

    def check_tabels_in_users_db(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        for table in app_tables_users.keys():
            # print('##table##', table)
            sql_file = os.path.join(self.pth2SQLtables, '{}_template.sql'.format(table))
            if table not in self.users_db.allAvailableTablesInDatabase:
                print('Table {} not in database...creating it'.format(table))
                self.users_db.createTableFromFile(sql_file, table)
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

    def connect_to_all_databases(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        conf = connect.Config(rappmysql.ini_masina)
        credentials_masina = conf.credentials
        self.auto_db = mysql_rm.DataBase(credentials_masina)
        if not self.auto_db.is_connected:
            raise RuntimeError('Could not connect to database')
        print('Connected to database auto_db:', self.auto_db.db_name)

        conf = connect.Config(rappmysql.ini_chelt)
        credentials_chelt = conf.credentials
        self.chelt_db = mysql_rm.DataBase(credentials_chelt)
        if not self.chelt_db.is_connected:
            raise RuntimeError('Could not connect to database')
        print('Connected to database chelt_db:', self.chelt_db.db_name)

        conf = connect.Config(rappmysql.ini_aeroclub)
        credentials_aeroclub = conf.credentials
        self.aeroclub_db = mysql_rm.DataBase(credentials_aeroclub)
        if not self.aeroclub_db.is_connected:
            raise RuntimeError('Could not connect to database')
        print('Connected to database aeroclub_db:', self.aeroclub_db.db_name)


class Users(UserMixin):
    def __init__(self, user_name, ini_users):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        super(UserMixin).__init__()
        # CheckUsersRequiredFiles.__init__(self, ini_users)
        self.user_name = user_name
        self.auto_app = None
        self.chelt_app = None
        self.aeroclub_app = None
        if isinstance(ini_users, dict):
            self.credentials = ini_users
        else:
            self.conf = connect.Config(ini_users)
            self.credentials = self.conf.credentials
        self.users_table = mysql_rm.Table(self.credentials, 'users')
        self.user_apps_table = mysql_rm.Table(self.credentials, 'user_apps')

    def init_app(self, app_name, ini_file):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        if app_name == 'cheltuieli':
            self.chelt_app = CheltApp(ini_file, self.id)
        elif app_name == 'auto':
            self.auto_app = AutoApp(ini_file, self.id)
        elif app_name == 'aeroclub':
            self.aeroclub_app = AeroclubApp(ini_file, self.id)

    def add_user(self, register_details):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        cols = []
        vals = []
        for k, v in register_details.items():
            cols.append(k)
            vals.append(v)
        user_id = self.users_table.addNewRow(cols, tuple(vals))
        return user_id

    def add_application(self, app_name):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        cols = ['id_users', 'app_name']  # , 'app_credentials'
        vals = [self.id, app_name]  # , str(new_credentials)
        id_app_row = self.user_apps_table.addNewRow(cols, tuple(vals))
        return id_app_row

    def run_sql_query(self, file):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        self.users_db.run_sql_file(file)

    @property
    def all_users(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        all_users = self.users_table.returnColumn('username')
        return all_users

    @property
    def all_possible_applications(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        all_possible_applications = self.user_apps_table.returnColumn('app_name')
        all_possible_applications = list(set(all_possible_applications))
        all_possible_applications = ['cheltuieli', 'masina', 'aeroclub']
        # all_possible_applications = rappmysql.subpackages
        return all_possible_applications

    @property
    def unused_applications(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        unused_applications = set(self.applications) ^ set(self.all_possible_applications)
        # unused_applications = ['cheltuieli', 'masina']
        return list(unused_applications)

    @property
    def id(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        matches = ('username', self.user_name)
        user_id = self.users_table.returnCellsWhere('id', matches)[0]
        return user_id

    @property
    def valid_user(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        all_users = self.users_table.returnColumn('username')
        if self.user_name in all_users:
            return True
        else:
            return False

    @property
    def admin(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        if self.valid_user:
            matches = ('id', self.id)
            user_type = self.users_table.returnCellsWhere('user_type', matches)[0]
            if user_type == 'admin':
                return True
            else:
                return False

    @property
    def applications(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        matches = ('id_users', self.id)
        user_apps = self.user_apps_table.returnCellsWhere('app_name', matches)
        return list(user_apps)

    @property
    def hashed_password(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        matches = ('username', self.user_name)
        hashed_password = self.users_table.returnCellsWhere('password', matches)[0]
        return hashed_password

    def verify_password(self, password):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        return check_password_hash(self.hashed_password, password)

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

    def unzip_profile_files(self, src_file, output_dir):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        with zipfile.ZipFile(src_file, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        return output_dir

    def erase_all_traces(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        self.chelt_db.drop_table_list(list(rappmysql.cheltuieli.chelt_plan.app_real_expenses.keys()))
        self.chelt_db.drop_table_list(list(rappmysql.cheltuieli.chelt_plan.app_chelt_tables.keys()))
        self.auto_db.drop_table_list(list(rappmysql.masina.auto.app_masina_tables.keys()))
        self.aeroclub_db.drop_table_list(list(rappmysql.aeroclub.aeroclub.app_aeroclub.keys()))
        self.users_db.drop_table_list(list(app_tables_users.keys()))

    def backup(self, export_files=False, complete_database=False):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        user_tables = {}
        for tab in app_tables_users:
            if tab == 'users':
                user_tables[tab] = {'id': self.id}
                continue
            user_tables[tab] = {'id_users': self.id}
        aeroclub_tables = {}
        for tab in rappmysql.aeroclub.aeroclub.app_aeroclub:
            aeroclub_tables[tab] = {'id_users': self.id}
        masina_tables = {}
        for tab in rappmysql.masina.auto.app_masina_tables:
            masina_tables[tab] = {'id_users': self.id}
        cheltuieli_tables = {}
        for tab in rappmysql.cheltuieli.chelt_plan.app_chelt_tables:
            cheltuieli_tables[tab] = {'id_users': self.id}
        for tab in rappmysql.cheltuieli.chelt_plan.app_real_expenses:
            cheltuieli_tables[tab] = {'id_users': self.id}
        tim = datetime.strftime(datetime.now(), '%Y_%m_%d__%H_%M_%S')
        if complete_database:
            output_dir = os.path.join(os.path.dirname(__file__), 'static', 'db_backup', '{}'.format(tim))
        else:
            output_dir = os.path.join(os.path.dirname(__file__), 'static', 'backup_complete_profile',
                                      '{:09d}'.format(self.id),
                                      '{}_{:09d}'.format(tim, self.id))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        complete_sql = ''
        if export_files:
            users_sql_query = self.users_db.return_sql_text(user_tables, export_files=output_dir, export_all_users=complete_database)
            complete_sql += users_sql_query
            masina_sql_query = self.auto_db.return_sql_text(masina_tables, export_files=output_dir, export_all_users=complete_database)
            complete_sql += masina_sql_query
            chelt_sql_query = self.chelt_db.return_sql_text(cheltuieli_tables, export_files=output_dir, export_all_users=complete_database)
            complete_sql += chelt_sql_query
            aeroclub_sql_query = self.aeroclub_db.return_sql_text(aeroclub_tables, export_files=output_dir, export_all_users=complete_database)
            complete_sql += aeroclub_sql_query
        else:
            users_sql_query = self.users_db.return_sql_text(user_tables, export_all_users=complete_database)
            complete_sql += users_sql_query
            masina_sql_query = self.auto_db.return_sql_text(masina_tables, export_all_users=complete_database)
            complete_sql += masina_sql_query
            chelt_sql_query = self.chelt_db.return_sql_text(cheltuieli_tables, export_all_users=complete_database)
            complete_sql += chelt_sql_query
            aeroclub_sql_query = self.aeroclub_db.return_sql_text(aeroclub_tables, export_all_users=complete_database)
            complete_sql += aeroclub_sql_query

        output_sql_file = os.path.join(output_dir, '{}_{:09d}.sql'.format(tim, self.id))
        FILE = open(output_sql_file, "w", encoding="utf-8")
        FILE.writelines(complete_sql)
        FILE.close()
        #####
        output_zip = os.path.join(os.path.dirname(output_dir), '{}.zip'.format(output_dir))
        zip_file = self.zip_profile_files(output_dir, output_zip)
        if os.path.exists(zip_file):
            shutil.rmtree(output_dir)
        print('finished backup')
        return output_sql_file

    def backup_users_tables(self, export_files=False):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        user_tables = {}
        for tab in app_tables_users:
            if tab == 'users':
                user_tables[tab] = {'id': self.id}
                continue
            user_tables[tab] = {'id_users': self.id}

        tim = datetime.strftime(datetime.now(), '%Y_%m_%d__%H_%M_%S')
        output_dir = os.path.join(os.path.dirname(__file__), 'static', 'backup_profile',
                                  '{:09d}'.format(self.id),
                                  '{}_{:09d}'.format(tim, self.id))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if export_files:
            sql_query = self.users_db.return_sql_text(user_tables, export_files=output_dir)
        else:
            sql_query = self.users_db.return_sql_text(user_tables)

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

    def import_zip(self, zip_file, import_files=False):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        output_dir, file = os.path.split(zip_file)
        src_dir = self.unzip_profile_files(zip_file, output_dir)
        src_dir = os.path.join(src_dir, file[:-4])
        if not os.path.exists(src_dir):
            raise RuntimeError('Missing Folder {}'.format(src_dir))

        sql_files = [x for x in os.listdir(src_dir) if x.endswith('.sql')]
        sql_file = os.path.join(src_dir, sql_files[0])
        self.users_db.run_sql_file(sql_file)
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


def main():
    script_start_time = time.time()
    selectedStartDate = datetime(2025, 1, 1, 0, 0, 0)
    selectedEndDate = datetime(2025, 1, 31, 0, 0, 0)

    # if compName == 'DESKTOP-5HHINGF':
    #     ini_file = r"D:\Python\MySQL\cheltuieli.ini"
    # else:
    #     ini_file = r"C:\_Development\Diverse\pypi\cfgm.ini"
    #     # ini_file = r"C:\_Development\Diverse\pypi\cfgmRN.ini"

    user = Users(None, rappmysql.ini_users)
    zp = r"C:\_Development\Diverse\pypi\rappmysql\src\rappmysql\mruser\static\db_backup\2025_06_26__11_58_11.zip"
    # user.import_zip(zp)
    user.erase_all_traces()
    # print('****', user.admin)
    # print('****', user.masini)
    # print('****', user.cheltuieli)
    # print('****', user.all_possible_applications)
    # print('****', user.unused_applications)
    # print('****', user.applications)
    # user.init_app('cheltuieli')

    # user.init_app('aeroclub')
    # user.backup(complete_database=True)
    # user.export_aeroclub_profile(export_files=True)
    # print('****', user.has_cheltuieli_real)
    # print('****', user.export_profile())
    # print('****', user.export_chelt_plan_sql())
    # print(user.delete_auto('aaaa_aaaa'))
    # if not user.masini:
    #     print('GGG')
    # else:
    #     for aa in user.masini:
    #         print(aa)
    # output_sql = r'C:\_Development\Diverse\pypi\radu\masina\src\masina\static\backup_profile\000000001\hyundai_ioniq.sql'
    # all_cars_ident = {'user_id': 1, 'id': 1}
    # masina_ident = {'id_users': 1, 'id_all_cars': 1}
    # tables = {'all_cars': all_cars_ident,
    #           'masina': masina_ident}

    # dire = r'C:\_Development\Diverse\pypi\radu\masina\src\masina\static\backup_profile\000000001\000000001'
    # sql_query = user.auto_db.return_sql_text(tables, export_files=dire)
    # print(sql_query)
    # user.export_car_sql(2, export_files=True)
    # profile = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\static\backup_profile\000000001\000000002\2025_06_05__16_22_12_000000002.zip"
    # user.import_profile_with_files(profile, import_files=True)

    scrip_end_time = time.time()
    duration = scrip_end_time - script_start_time
    duration = time.strftime("%H:%M:%S", time.gmtime(duration))
    print('run time: {}'.format(duration))


if __name__ == '__main__':
    main()
