import os.path
import pathlib

import mysql.connector as mysql
import re
import codecs
import sys
import traceback
import numpy as np
import subprocess
from datetime import datetime
from rappmysql.mysqlquerys import connect
import rappmysql

compName = os.getenv('COMPUTERNAME')


class DataBase:
    def __init__(self, credentials):
        self.db = mysql.connect(**credentials)
        self.cursor = self.db.cursor()
        self.db_name = credentials['database']

    @property
    def is_connected(self):
        return self.db.is_connected()

    @property
    def dataBaseVersion(self):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.cursor.execute('SELECT version()')
        db_version = self.cursor.fetchone()
        return db_version

    @property
    def allAvailableTablesInDatabase(self):
        """ get all tables in schema"""
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        cur = self.db.cursor()
        command = "SHOW TABLES"
        cur.execute(command)
        rows = cur.fetchall()
        tables = []
        for row in rows:
            tabName = row[0]
            tables.append(tabName)
        cur.close()

        return sorted(tables)

    @property
    def allAvailableDatabases(self):
        """ get all tables in schema"""
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        cur = self.db.cursor()
        command = 'SHOW DATABASES'
        cur.execute(command)
        rows = cur.fetchall()
        tables = []
        for row in rows:
            tabName = row[0]
            tables.append(tabName)
        cur.close()

        return sorted(tables)

    def checkProcess(self):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        query = "SHOW PROCESSLIST"
        cur = self.db.cursor()
        cur.execute(query)
        records = cur.fetchall()
        return records

    def killProcess(self, processes):
        for process in processes:
            query = "KILL {}".format(process)
            self.cursor.execute(query)

    def killAllProcess(self, ):
        query = "SHOW PROCESSLIST"
        cur = self.db.cursor()
        cur.execute(query)
        records = cur.fetchall()
        for process in records:
            print(process)
            if process[-1] == 'SHOW PROCESSLIST':
                continue
            query = "KILL {}".format(process[0])
            print(query)
            self.cursor.execute(query)

    def run_sql_file(self, file):
        '''
        :param file: QFileDialog.getOpenFileName
        :return:
        '''
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        try:
            error = None
            command = ''
            f = open(file, errors="ignore", encoding="utf-8")
            for line in f.read().splitlines():
                command += line
                if ';' in line:
                    try:
                        print(command)
                        cur = self.db.cursor()
                        cur.execute(command)
                        command = ''
                    except mysql.Error as err:
                        print(20*'+')
                        print(command)
                        print(20 * '+')
                        print('ERROR mysql.Error: ', err.errno)
                        print('ERROR mysql.Error: ', err.msg)
                        error = (err.msg, command)
                        cur.close()
                        break
            f.close()
            self.db.commit()
        except Exception:
            print('ERR: ', traceback.format_exc())
            error = traceback.format_exc()
            cur.close()
        return error

    def createTableFromFile(self, file, newTableName):
        '''
        :param file: QFileDialog.getOpenFileName
        :return:
        '''
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        try:
            error = None
            command = ''
            f = open(file)
            for line in f.read().splitlines():
                command += line
                if ';' in line:
                    if re.search("^CREATE TABLE", command) or \
                            re.search("^ALTER TABLE", command) or \
                            re.search("^INSERT INTO", command):
                        match = re.findall(r"\`(.+?)\`", command)
                        tableName = match[0]
                        # newTableName = '{}'.format(tableName)
                        command = command.replace(tableName, newTableName)
                    cur = self.db.cursor()
                    cur.execute(command)
                    command = ''
            f.close()
        except mysql.Error as err:
            print(command, 'ERROR mysql.Error: ', err.msg)
            error = (err.msg, command)
            cur.close()
        except Exception:
            print('ERR: ', traceback.format_exc())
            error = traceback.format_exc()
            cur.close()

        return error

    def createTableList(self, fileList):
        '''
        :param fileList: QFileDialog.getOpenFileNames
        :return: Error if exists, else None
        '''
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        errList = []
        while fileList:
            for i, file in enumerate(fileList):
                error = self.createTableFromFile(file)
                if error:
                    if error[0] == 'Cannot add foreign key constraint' \
                            or re.search("^relation.*does not exist$", error[0]):
                        errList.append(error[1])
                        fileList.pop(i)
                        continue
                    elif 'already exists' in error[0]:
                        fileList.pop(i)
                    else:
                        print('ERR createTablesFromFiles: ', error)
                        fileList.pop(i)
                else:
                    fileList.pop(i)

        probList = []
        for com in errList:
            try:
                print('Retrying... {}'.format(com))
                cur = self.db.cursor()
                cur.execute(com)
                cur.close()
            except Exception:
                print('ERR: ', traceback.format_exc())
                error = (traceback.format_exc(), com)
                probList.append(error)

        if probList:
            print('remaining errs:')
            for i in errList:
                print(i)
        else:
            print('Successfully')

    def drop_table(self, tableName):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        query = "DROP TABLE IF EXISTS {};".format(tableName)
        cur = self.db.cursor()
        cur.execute(query)
        cur.close()

    def drop_table_list(self, tableList):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        # print(tableList)
        # return
        results = []
        while tableList:
            for i, tab in enumerate(tableList):
                print('######', tab, '#######')
                cur = self.db.cursor()
                # exists = self.checkIfTableExists(tab)
                if tab not in self.allAvailableTablesInDatabase:
                    print('table {} does not exist in database {}'.format(tab, self.db_name))
                    tableList.pop(i)
                    continue
                query = "SELECT table_name FROM information_schema.KEY_COLUMN_USAGE " \
                        "WHERE table_schema = %s AND referenced_table_name = %s "
                # print(query)
                # print(self.db_name, tab)
                cur = self.db.cursor()
                cur.execute(query, (self.db_name, tab))

                children = []
                for cursor in cur.fetchall():
                    if cursor[0]:
                        children.append(cursor)
                # print('children', children)
                cur.close()
                # return
                if not children:
                    res = self.drop_table(tab)
                    results.append(res)
                    tableList.pop(i)
                else:
                    # if children make sure all of them are included in list
                    for child in children:
                        if child[0] not in tableList:
                            print('if child not in tablelist:', tab, child, children)
                            err = self.drop_table(tab)
                            results.append(err)
                            tableList.pop(i)
                            break
                cur.close()
        return results

    def rename_table(self, tableName, newName):
        # #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        query = ('RENAME TABLE {} TO {}'.format(tableName, newName))
        cur = self.db.cursor()
        try:
            cur.execute(query)
            cur.close
        except mysql.connector.Error as err:
            print(err.msg)

    def deleteAllDataInTable(self, tableList):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        cur = self.db.cursor()
        for tab in tableList:
            query = ('DELETE FROM {}'.format(tab))
            cur.execute(query)
            self.db.commit()
        cur.close()

    def export_database(self, output_file):
        cmd = ['mysqldump', '-u', 'root', '-p', 'cheltuieli_desktop', '>', r"D:\Python\sql_tables\bbb.sql"]
        print('CMD', cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        out, err = p.communicate()
        if p.returncode != 0:
            print('returncode: ', p.returncode)
            print('Error: ', err)
        else:
            print('Done: {}'.format(cmd))

    def show_create_table(self, tableName):
        query = 'SHOW CREATE TABLE {}'.format(tableName)
        cursor = self.db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        records = records[0]

        cursor.close()
        filename = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\aa.sql"
        data = records[1]
        FILE = open(filename, "w")
        FILE.writelines(data)
        FILE.close()

    def show_create_table_2(self, tableName):
        print('################')
        query = 'SELECT * FROM {}'.format(tableName)
        cursor = self.db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        # print('++', query)
        data = ""
        for row in records:
            # print('ÄÄ', row)
            data += "INSERT INTO `" + str(tableName) + "` VALUES("
            first = True
            for field in row:
                if not first:
                    data += ', '
                data += '"' + str(field) + '"'
                first = False

            data += ");\n"
        data += "\n\n"

        cursor.close()
        filename = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\bb.sql"
        FILE = open(filename, "w")
        FILE.writelines(data)
        FILE.close()

    def export_tables_to_sql(self, tables, output_sql_file):
        data = ""
        cur = self.db.cursor()
        for table in tables:
            cur.execute("SHOW CREATE TABLE `" + str(table) + "`;")
            data += "\n" + str(cur.fetchone()[1]) + ";\n\n"
            cur.execute("SELECT * FROM `" + str(table) + "`;")
            for row in cur.fetchall():
                data += "INSERT INTO `" + str(table) + "` VALUES("
                first = True
                for field in row:
                    if not first:
                        data += ', '
                    data += '"' + str(field) + '"'
                    first = False

                data += ");\n"
            data += "\n\n"
        FILE = open(output_sql_file, "w")
        FILE.writelines(data)
        FILE.close()

    def backup_profile_with_files(self, tables, user_id,  output_dir=None, export_files=True):
        if not output_dir:
            tim = datetime.strftime(datetime.now(), '%Y_%m_%d__%H_%M_%S')
            dir = os.path.dirname(__file__)
            output_dir_name = '{}_{}'.format(tim, '{:09d}'.format(user_id))
            output_dir = os.path.join(dir, r'static\backup_profile', '{:09d}'.format(user_id), output_dir_name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print('created output_dir', output_dir)
        data = ""
        cur = self.db.cursor()
        for table in tables:
            query = "SHOW CREATE TABLE {}".format(table)
            cur.execute(query)
            show_create_table_query = cur.fetchone()[1]
            if re.search("^CREATE TABLE", show_create_table_query):
                show_create_table_query = show_create_table_query.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
            # new_create_table_query = []
            # tt = show_create_table_query.split('\n')
            # for r in tt:
            #     if 'file' in r:
            #         continue
            #     if re.search("AUTO_INCREMENT=", r):
            #         match = re.findall(r'AUTO_INCREMENT=(.+?)\ DEFAULT', r)
            #         start_row = match[0]
            #         r = r.replace(start_row, "1")
            #     new_create_table_query.append(r)
            # create_table_query = (('{}\n'*len(new_create_table_query)).format(*new_create_table_query))
            data += "\n {} ;\n\n".format(show_create_table_query)
            # print(data)

            query = 'DESC {}'.format(table)
            cur.execute(query)
            cols_names = cur.fetchall()
            table_has_files = False
            files_cols = []
            export_cols = []
            for col in cols_names:
                if 'file' in col[0]:
                    files_cols.append(col[0])
                    table_has_files = True
                    continue
                export_cols.append(col[0])
            export_cols_query = (('{}, ' * len(export_cols)).format(*export_cols))
            export_cols_query = export_cols_query[:-2]

            query = "SELECT {} FROM {} where {}={};".format(export_cols_query, table, tables[table], user_id)
            cur.execute(query)
            for row in cur.fetchall():
                # print('row****', row, type(row), len(row))
                data += "INSERT IGNORE INTO {} ({}) VALUES(".format(table, export_cols_query)
                first = True
                for field in row:
                    if not first:
                        data += ', '
                    # data += '"' + str(field) + '"'
                    # print(field, type(field))
                    if field is None:
                        data += 'NULL'
                    else:
                        # if table == 'chelt_plan':
                        if isinstance(field, str) and '"' in field:
                            # print(50*'#', '_{}_'.format(field), type(field))
                            field = field.replace('"', "'")
                            # print(50 * '#', '_{}_'.format(field), type(field))
                        data += '"{}"'.format(str(field))
                        # else:
                        #     data += '"{}"'.format(str(field))
                    first = False
                data += ");\n"
            data += "\n\n"
            ###########
            if table_has_files and export_files:
                # print('table', table)
                export_cols_query = (('{}, ' * len(files_cols)).format(*files_cols))
                export_cols_query = 'id, {}'.format(export_cols_query[:-2])
                # print('export_cols_query', export_cols_query)
                query = "SELECT {} FROM {} where {}={};".format(export_cols_query, table, tables[table], user_id)
                cur.execute(query)
                for row in cur.fetchall():
                    # print('ÄÄÄÄ', row)
                    row_id, row_file, row_file_name = row
                    # print('ÄÄÄÄ', row_id, row_file, row_file_name)
                    if not row_file:
                        continue
                    filename = '{}+{}+{}+{}'.format(user_id, table, row_id, row_file_name)
                    filename = os.path.join(output_dir, filename)
                    with open(filename, 'wb') as file:
                        file.write(row_file)

        tim = datetime.strftime(datetime.now(), '%Y_%m_%d__%H_%M_%S')
        output_file = '{}_{}.sql'.format(tim, 'user_name')
        # dir = os.path.dirname(__file__)
        output_sql_file = os.path.join(output_dir, output_file)

        FILE = open(output_sql_file, "w", encoding="utf-8")
        FILE.writelines(data)
        FILE.close()

    def return_sql_text_bkp(self, tables):
        data = ""
        cur = self.db.cursor()
        for table in tables:
            query = "SHOW CREATE TABLE {}".format(table)
            cur.execute(query)
            show_create_table_query = cur.fetchone()[1]
            if re.search("^CREATE TABLE", show_create_table_query):
                show_create_table_query = show_create_table_query.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
            data += "\n {} ;\n\n".format(show_create_table_query)
            # print(data)

            query = 'DESC {}'.format(table)
            cur.execute(query)
            cols_names = cur.fetchall()
            table_has_files = False
            files_cols = []
            export_cols = []
            for col in cols_names:
                if 'file' in col[0]:
                    files_cols.append(col[0])
                    table_has_files = True
                    continue
                export_cols.append(col[0])
            export_cols_query = (('{}, ' * len(export_cols)).format(*export_cols))
            export_cols_query = export_cols_query[:-2]
            query = "SELECT {} FROM {} WHERE".format(export_cols_query, table)
            for ccc, vvv in tables[table].items():
                # print(ccc, vvv)
                query += ' {} = {} AND'.format(ccc, vvv)
            query = query[:-4]
            cur.execute(query)
            for row in cur.fetchall():
                # print('row****', row, type(row), len(row))
                data += "INSERT IGNORE INTO {} ({}) VALUES(".format(table, export_cols_query)
                first = True
                for field in row:
                    if not first:
                        data += ', '
                    # data += '"' + str(field) + '"'
                    # print(field, type(field))
                    if field is None:
                        data += 'NULL'
                    else:
                        # if table == 'chelt_plan':
                        if isinstance(field, str) and '"' in field:
                            # print(50*'#', '_{}_'.format(field), type(field))
                            field = field.replace('"', "'")
                            # print(50 * '#', '_{}_'.format(field), type(field))
                        data += '"{}"'.format(str(field))
                        # else:
                        #     data += '"{}"'.format(str(field))
                    first = False
                data += ");\n"
            data += "\n\n"
        return data

    def return_sql_text(self, tables, export_files=False, export_all_users=False):
        data = ""
        cur = self.db.cursor()
        for table in tables:
            query = "SHOW CREATE TABLE {}".format(table)
            cur.execute(query)
            show_create_table_query = cur.fetchone()[1]
            if re.search("^CREATE TABLE", show_create_table_query):
                show_create_table_query = show_create_table_query.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")

            data += "\n {} ;\n\n".format(show_create_table_query)
            # print(data)

            query = 'DESC {}'.format(table)
            cur.execute(query)
            cols_names = cur.fetchall()
            table_has_files = False
            files_cols = []
            export_cols = []
            for col in cols_names:
                if 'file' in col[0]:
                    files_cols.append(col[0])
                    table_has_files = True
                    continue
                export_cols.append(col[0])
            export_cols_query = (('{}, ' * len(export_cols)).format(*export_cols))
            export_cols_query = export_cols_query[:-2]
            if export_all_users:
                query = "SELECT {} FROM {} ".format(export_cols_query, table)
            else:
                query = "SELECT {} FROM {} WHERE".format(export_cols_query, table)
                for ccc, vvv in tables[table].items():
                    query += ' {} = {} AND'.format(ccc, vvv)
                query = query[:-4]
            # print('*-query', query)
            cur.execute(query)
            for row in cur.fetchall():
                # print('row****', row, type(row), len(row))
                data += "INSERT IGNORE INTO {} ({}) VALUES(".format(table, export_cols_query)
                first = True
                for field in row:
                    if not first:
                        data += ', '
                    # data += '"' + str(field) + '"'
                    # print(field, type(field))
                    if field is None:
                        data += 'NULL'
                    else:
                        # if table == 'chelt_plan':
                        if isinstance(field, str) and '"' in field:
                            # print(50*'#', '_{}_'.format(field), type(field))
                            field = field.replace('"', "'")
                            # print(50 * '#', '_{}_'.format(field), type(field))
                        data += '"{}"'.format(str(field))
                        # else:
                        #     data += '"{}"'.format(str(field))
                    first = False
                data += ");\n"
            data += "\n\n"
            if table_has_files and export_files:
                export_cols_query = (('{}, ' * len(files_cols)).format(*files_cols))
                export_cols_query = 'id, {}'.format(export_cols_query[:-2])

                query = "SELECT {} FROM {} WHERE".format(export_cols_query, table)
                for ccc, vvv in tables[table].items():
                    query += ' {} = {} AND'.format(ccc, vvv)
                query = query[:-4]
                cur.execute(query)
                for row in cur.fetchall():
                    row_id, row_file, row_file_name = row
                    if not row_file:
                        continue
                    filename = '{}+{}'.format(row_id, row_file_name)
                    filename = os.path.join(export_files, filename)
                    with open(filename, 'wb') as file:
                        file.write(row_file)

        return data

    def createAliasTempTable(self, tableName, colDict, origTab):
        cur = self.db.cursor()
        selectQuery = ''
        for colName, alias in colDict.items():
            selectQuery += '{} {}, '.format(colName, alias)

        query = "CREATE TEMPORARY TABLE {} " \
                "SELECT {}" \
                " FROM {};".format(tableName, selectQuery[:-2], origTab)
        # print(query)
        cur.execute(query)
        query = ("DESC {}".format(tableName))
        cur.execute(query)
        tableHead = []
        for i in cur.fetchall():
            tableHead.append(i[0])

        query = ('SELECT * FROM {}'.format(tableName))
        cur.execute(query)
        table = cur.fetchall()

        cur.close()

        return tableHead, table

    def descAliasTempTable(self, tableName, colDict, origTab):
        cur = self.db.cursor()
        selectQuery = ''
        for colName, alias in colDict.items():
            selectQuery += '{} {}, '.format(colName, alias)

        query = "CREATE TEMPORARY TABLE {} " \
                "SELECT {}" \
                " FROM {};".format(tableName, selectQuery[:-2], origTab)
        # print(query)
        cur.execute(query)
        query = ("DESC {}".format(tableName))
        cur.execute(query)
        tableHead = []
        for i in cur.fetchall():
            tableHead.append(i[0])

        query = ('SELECT * FROM {}'.format(tableName))
        cur.execute(query)
        table = cur.fetchall()

        cur.close()

        return tableHead, table


class Table(DataBase):
    def __init__(self, credentials, tableName):
        super().__init__(credentials)
        self.tableName = tableName

    @property
    def noOfRows(self):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        query = 'SELECT COUNT(*) FROM {}'.format(self.tableName)
        cursor = self.db.cursor()
        cursor.execute(query)
        noOfRows = cursor.fetchone()[0]
        # rowNo = cursor.rowcount
        cursor.close()
        return noOfRows

    def lastRowId(self):
        query = ('SELECT id FROM {} ORDER BY id DESC LIMIT 1'.format(self.tableName))
        cur = self.db.cursor()
        cur.execute(query)
        lastId = cur.fetchonel()
        if lastId is None:
            return 0
        return lastId[0]

    @property
    def columnsNames(self):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        cursor = self.db.cursor()
        query = 'DESC {}'.format(self.tableName)
        cursor.execute(query)
        res = cursor.fetchall()
        cols = []
        for col in res:
            cols.append(col[0])
        cursor.close()
        return cols

    @property
    def columnsDetProperties(self):
        query = 'DESC {}'.format(self.tableName)
        colNames = ['Field', 'Type', 'Null', 'Key', 'Default', 'Extra']
        cursor = self.db.cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        cols = {}
        for col in res:
            colName, colType, null, key, default, extra = col
            if isinstance(colType, bytes):
                colType = str(colType.decode("utf-8"))
            cols[colName] = [colType, null, key, default, extra]
        cursor.close()
        return cols

    @property
    def columnsProperties(self):
        #print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        cursor = self.db.cursor()
        query = ("SELECT table_name, column_name, data_type FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{}'").format(self.tableName)
        cursor.execute(query)
        res = cursor.fetchall()
        cols = {}
        for col in res:
            table_name, col_name, data_type = col
            cols[col_name] = data_type
        cursor.close()
        return cols

    @property
    def children_tables(self):
        query = "SELECT table_name FROM information_schema.KEY_COLUMN_USAGE " \
                "WHERE table_schema = %s AND referenced_table_name = %s "
        # print(query)
        # print(self.db_name, self.tableName)
        cur = self.db.cursor()
        cur.execute(query, (self.db_name, self.tableName))
        # query = "SELECT table_name FROM information_schema.KEY_COLUMN_USAGE " \
        #         "WHERE table_schema = {} AND referenced_table_name = {} ".format(self.db_name, self.tableName)
        # print(query)
        # # print(self.db_name, self.tableName)
        # cur = self.db.cursor()
        # cur.execute(query)
        children = []
        for cursor in cur.fetchall():
            # print(cursor)
            if cursor[0]:
                children.append(cursor[0])
        return children

    def rename_column(self, tableName, old_col_name, new_col_name):
        # #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        query = ('ALTER TABLE {} RENAME COLUMN {} TO {}'.format(tableName, old_col_name, new_col_name))
        cur = self.db.cursor()
        try:
            cur.execute(query)
            cur.close
        except mysql.connector.Error as err:
            print(err.msg)

    def deleteRow(self, condition):
        colName, value = condition
        query = 'DELETE FROM {} WHERE {} = %s '.format(self.tableName, colName)
        print(query)
        cursor = self.db.cursor()
        cursor.execute(query, value)
        self.db.commit()
        cursor.close()

    def delete_multiple_rows(self, condition):
        colName, value = condition
        query = 'DELETE FROM {} WHERE {} = {} '.format(self.tableName, colName, value)
        print(query)
        cursor = self.db.cursor()
        cursor.execute(query, value)
        self.db.commit()
        cursor.close()

    def delete_multiple_rows_multiple_conditions(self, condition):
        colName, value = condition
        query = 'DELETE FROM {} WHERE {} = {} '.format(self.tableName, colName, value)
        print(query)
        cursor = self.db.cursor()
        cursor.execute(query, value)
        self.db.commit()
        cursor.close()

    def convertToBinaryData(self, filename):
        # Convert digital data to binary format
        with open(filename, 'rb') as file:
            binaryData = file.read()
        return binaryData

    # def convertToRightType(self, err_msg):
    #     if 'Incorrect decimal value:' in err_msg:

    def addNewRow(self, columns, values):
        # print(len(columns), len(values))
        strCols = (('{}, ' * len(columns)).format(*columns))
        strCols = '({})'.format(strCols[:-2])
        strVals = ('%s,'*len(columns))
        strVals = '({})'.format(strVals[:-1])

        query = "INSERT INTO {} {} VALUES {}".format(self.tableName, strCols, strVals)
        if isinstance(values, int):
            values = (values, )
        elif isinstance(values, str):
            values = (values,)
        elif isinstance(values, tuple):
            # print('values', values)
            new_vals = []
            for v in values:
                if isinstance(v, str):
                    if os.path.isfile(v):
                        v = self.convertToBinaryData(v)
                new_vals.append(v)
            values = tuple(new_vals)

        cursor = self.db.cursor()
        try:
            print(query)
            cursor.execute(query, values)
        except:
            print('nu merge:', traceback.format_exc())
            print()
            print('query: ', query)
            print('values: ', values)
            for i in range(len(columns)):
                print(columns[i], values[i], type(columns[i]), type(values[i]))
            raise RuntimeError
        # try:
        #     cursor.execute(query, values)
        # except mysql.errors.DatabaseError as err:
        #     print(err)
        #     print(err.msg)
        #     print('ÄÄÄÄÄÄÄÄÄÄÄ')
        #     self.convertToRightType(err.msg)
        self.db.commit()
        cursor.close()

        return cursor.lastrowid

    def addNewRowWithFile(self, columns, values):
        # print(len(columns), len(values))
        strCols = (('{}, ' * len(columns)).format(*columns))
        strCols = '({})'.format(strCols[:-2])
        strVals = ('%s,'*len(columns))
        strVals = '({})'.format(strVals[:-1])

        query = "INSERT INTO {} {} VALUES {}".format(self.tableName, strCols, strVals)
        #######
        print('***',query)
        # for i in range(len(columns)):
        #     print(columns[i], values[i])
        #######
        if isinstance(values, int):
            values = (values, )
        elif isinstance(values, str):
            values = (values,)
        elif isinstance(values, tuple):
            # print('values', values)
            new_vals = []
            for v in values:
                if isinstance(v, pathlib.WindowsPath):
                    print('aaaaa', v)
                    if v.is_file():
                        v = self.convertToBinaryData(v)
                new_vals.append(v)
            values = tuple(new_vals)
        # print('-->', values)
        try:
            cursor = self.db.cursor()
            cursor.execute(query, values)
            self.db.commit()
            cursor.close()
            print('executed')
            return cursor.lastrowid
        except mysql.Error as err:
            if err.errno == 2013 and err.msg == 'Lost connection to MySQL server during query':
                print('BINOGOOO')
                print('ERROR mysql.Error: ', err.errno)
                print('ERROR mysql.Error: ', err.msg)
                cursor.execute('set max_allowed_packet=67108864')
                self.db.commit()
                cursor.execute(query, values)
                self.db.commit()
                cursor.close()
                print('DONEEEEE')
            else:
                print('Alta eroare: ', err.errno, err.msg)

    def insertColumns(self, column_name, column_definition, afterCol):
        if afterCol == 'FIRST':
            query = 'ALTER TABLE {} ADD COLUMN {} {} FIRST'.format(self.tableName, column_name, column_definition)
        else:
            query = 'ALTER TABLE {} ADD COLUMN {} {} AFTER {}'.format(self.tableName, column_name, column_definition, afterCol)

        cursor = self.db.cursor()
        cursor.execute(query)
        self.db.commit()
        cursor.close()

    def returnAllRecordsFromTable(self):
        cur = self.db.cursor()
        query = ('SELECT * FROM {}'.format(self.tableName))
        cur.execute(query)
        records = cur.fetchall()
        return records

    def returnAllRecordsFromTableExceptBlob(self):
        cur = self.db.cursor()
        query = 'SELECT '
        for col_name, prop in self.columnsDetProperties.items():
            # print(col_name, prop)
            if prop[0] == 'longblob':
                continue
            query += '{}, '.format(col_name)
        query = query[:-2]
        query += ' FROM {}'.format(self.tableName)
        print(query)
        cur.execute(query)
        records = cur.fetchall()
        return records

    def returnLastRecords(self, column, noOfRows2Return):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        cur = self.db.cursor()
        query = ('SELECT * FROM {} ORDER BY {} DESC LIMIT %s'.format(self.tableName, column))
        cur.execute(query, (noOfRows2Return,))
        rows = cur.fetchall()
        cur.close()
        return rows

    def filterRows(self, matches, order_by=None):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        filterText = ''
        for match in matches:
            search_col, search_key = match
            if isinstance(search_key, tuple):
                min, max = search_key
                new = "{} >= '{}' AND {} <= '{}' AND ".format (search_col, min, search_col, max)
                filterText += new
            elif isinstance(search_key, list):
                new = "{} in {} AND ".format(search_col, tuple(search_key))
                filterText += new
            elif search_key == 'None' or search_key is None:
                new = "{} IS NULL AND ".format(search_col, search_key)
                filterText += new
            else:
                new = "{} = '{}' AND ".format(search_col, search_key)
                filterText += new

        query = 'SELECT '
        for col_name, prop in self.columnsDetProperties.items():
            # print(col_name, prop)
            if prop[0] == 'longblob':
                continue
            query += '{}, '.format(col_name)
        query = query[:-2]
        query += ' FROM {} WHERE {} '.format(self.tableName, filterText[:-4])

        # print(query)
        # query = "SELECT * FROM {} WHERE ".format(self.tableName) + filterText[:-4]
        if order_by:
            col, order = order_by
            txt = 'ORDER BY {} {}'.format(col, order)
            query += txt
        cur = self.db.cursor()
        cur.execute(query)
        records = cur.fetchall()
        cur.close()
        return records

    def returnRowsWhere(self, matches):
        has_longblob_col = False
        cols_without_longblob = ''
        for col_name, prop in self.columnsDetProperties.items():
            # print(col_name, prop)
            if prop[0] == 'longblob':
                has_longblob_col = True
            else:
                cols_without_longblob += '{}, '.format(col_name)
        cols_without_longblob = cols_without_longblob[:-2]

        # print('cols_without_longblob', cols_without_longblob)
        if isinstance(matches, tuple):
            searchCol, searchKey = matches
            if isinstance(searchKey, str) or isinstance(searchKey, int):
                query = "SELECT * FROM {} WHERE {} = '{}'".format(self.tableName, searchCol, searchKey)
            if isinstance(searchKey, tuple):
                query = "SELECT * FROM {} WHERE {} IN '{}'".format(self.tableName, searchCol, searchKey)
            if searchKey is None:
                query = "SELECT * FROM {} WHERE {} IS NULL".format(self.tableName, searchCol)
        elif isinstance(matches, list):
            text = ''
            for i in matches:
                searchCol, searchKey = i
                if searchKey is None:
                    new = '{} IS NULL AND '.format(searchCol)
                else:
                    new = '{} = "{}" AND '.format(searchCol, searchKey)
                text += new
            query = "SELECT * FROM {} WHERE ".format(self.tableName) + text[:-4]
        else:
            raise TypeError('{} must be tuple or list of tuples'.format(matches))

        if has_longblob_col:
            query = query.replace('*', cols_without_longblob)
        print('query', query)
        # return
        cursor = self.db.cursor()

        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        values = []
        for i in records:
            values.append(i)
        return values

    def returnRowsLike(self, column, keyWord):
        query = "SELECT * FROM {} WHERE {} LIKE '%{}%'".format(self.tableName,
                                                               column, keyWord)
        cur = self.db.cursor()
        cur.execute(query)
        records = cur.fetchall()
        return records

    def returnRowsYoungerThan(self, column, timeP):
        query = "SELECT * FROM {} WHERE {} > %s ORDER BY {} DESC".format(self.tableName, column, column)
        cur = self.db.cursor()
        cur.execute(query, (timeP, ))
        records = cur.fetchall()
        return records

    def returnRowsInInterval(self, startColumn, startTime, endColumn, endTime):
        # query = "SELECT * FROM {} WHERE {} > %s ORDER BY {} DESC".format(self.tableName, startColumn, startColumn)
        query = "SELECT * FROM {} WHERE {} > %s OR {} < %s".format(self.tableName, startColumn, endColumn)
        # print(query)
        cur = self.db.cursor()
        cur.execute(query, (startTime, endTime))
        records = cur.fetchall()
        return records

    def returnRowsWhereValueIsInIntervalAND(self, colWhere, keyWord, startColumn, valueInInterval, endColumn):
        # query = "SELECT * FROM {} WHERE {} > %s ORDER BY {} DESC".format(self.tableName, startColumn, startColumn)
        query = "SELECT * FROM {} WHERE {} = %s AND %s > {} AND {} > %s".format(self.tableName, colWhere, startColumn, endColumn)
        # print(query)
        cur = self.db.cursor()
        cur.execute(query, (keyWord, valueInInterval, valueInInterval))
        records = cur.fetchall()
        return records

    def returnCellWhereValueIsInIntervalAND(self, col2return,  colWhere, keyWord, startColumn, valueInInterval, endColumn):
        # query = "SELECT * FROM {} WHERE {} > %s ORDER BY {} DESC".format(self.tableName, startColumn, startColumn)
        query = "SELECT {} FROM {} WHERE {} = %s AND %s > {} AND ({} > %s OR {} IS NULL)".format(col2return, self.tableName, colWhere, startColumn, endColumn, endColumn)
        # print(query)
        cur = self.db.cursor()
        cur.execute(query, (keyWord, valueInInterval, valueInInterval))
        records = cur.fetchall()
        return records

    def returnRowsQuery(self, matches, order_by=None):
        filterText = ''
        for match in matches:
            search_col, sign, search_value = match
            if sign == 'LIKE':
                new = "{} {} '%{}%' AND ".format(search_col, sign, search_value)
                filterText += new
            elif search_value == None:
                new = "{} {} NULL AND ".format(search_col, sign, search_value)
                filterText += new
            else:
                new = "{} {} '{}' AND ".format(search_col, sign, search_value)
                filterText += new

        query = 'SELECT '
        for col_name, prop in self.columnsDetProperties.items():
            # print(col_name, prop)
            if prop[0] == 'longblob':
                continue
            query += '{}, '.format(col_name)
        query = query[:-2]
        query += ' FROM {} WHERE {} '.format(self.tableName, filterText[:-4])
        # query = 'SELECT * FROM {} WHERE {} '.format(self.tableName, filterText[:-4])
        if order_by:
            col, order = order_by
            txt = 'ORDER BY {} {}'.format(col, order)
            query += txt
        # print('__query__', query)
        cur = self.db.cursor()
        cur.execute(query)
        records = cur.fetchall()
        cur.close()
        return records

    def returnRowsOfYear(self, startColumn, startTime, endColumn, endTime):
        # query = "SELECT * FROM {} WHERE {} > %s ORDER BY {} DESC".format(self.tableName, startColumn, startColumn)
        query = "SELECT * FROM {} WHERE {} >= %s AND {} <= %s".format(self.tableName, startColumn, endColumn)
        # print(query)
        cur = self.db.cursor()
        cur.execute(query, (startTime, endTime))
        records = cur.fetchall()
        return records

    def returnRowsOutsideInterval(self, startColumn, startTime, endColumn, endTime):
        # query = "SELECT * FROM {} WHERE {} > %s ORDER BY {} DESC".format(self.tableName, startColumn, startColumn)
        query = "SELECT * FROM {} WHERE {} < %s AND {} > %s".format(self.tableName, startColumn, endColumn)
        # print(query)
        cur = self.db.cursor()
        cur.execute(query, (startTime, endTime))
        records = cur.fetchall()
        return records

    def get_column_type(self, column):
        colProps = self.columnsProperties[column]
        # print('µµµµµµµµµ', colProps)
        colType = colProps[0]
        return colType

    def modify2AutoIncrement(self, column, colType):
        query = 'ALTER TABLE {} MODIFY {} {} AUTO_INCREMENT;'.format(self.tableName, column, colType)
        print(query)
        cursor = self.db.cursor()
        cursor.execute(query)
        self.db.commit()
        cursor.close()

    def modifyType(self, column, colType):
        query = 'ALTER TABLE {} MODIFY {} {};'.format(self.tableName, column, colType)
        cursor = self.db.cursor()
        cursor.execute(query)
        self.db.commit()
        cursor.close()

    def changeCellContent(self, column2Modify, val2Moify, refColumn, refValue):
        cursor = self.db.cursor()
        try:
            if isinstance(refValue, tuple):
                query = "UPDATE {} SET {} = {} WHERE {} IN {}".format(self.tableName, column2Modify, val2Moify, refColumn, refValue)
                cursor.execute(query)
                self.db.commit()
                cursor.close()
                return
            else:
                query = "UPDATE {} SET {} = %s WHERE {} = %s".format(self.tableName, column2Modify, refColumn)
            print(query)
            print('val2Moify', val2Moify)

            if isinstance(val2Moify, str):
                if os.path.isfile(val2Moify):
                    print('aaaaa', val2Moify, type(val2Moify))
                    val2Moify = self.convertToBinaryData(val2Moify)
                    # print('aaaaa', val2Moify, type(val2Moify))
            vals = (val2Moify, int(refValue))
            # print(vals)
            cursor.execute(query, vals)
            self.db.commit()
            cursor.close()
        except mysql.Error as err:
            print('++', err)
            print('query', query)
            print('vals', vals)
            print('ERROR mysql.Error: ', err.msg)
            # error = err.msg
            # cur.close()

    def dropColumn(self, column2Del):
        query = "ALTER TABLE {} DROP COLUMN %s;".format(self.tableName)
        query = "ALTER TABLE {} DROP COLUMN {};".format(self.tableName, column2Del)
        print(query)
        cursor = self.db.cursor()
        # vals = (column2Del, )
        cursor.execute(query)
        self.db.commit()
        cursor.close()

    def executeQuery(self, query):
        print(sys._getframe().f_code.co_name)
        # print(file)
        cursor = self.db.cursor()
        if isinstance(query, str):
            commands = query.split(';')
        for command in commands:
            print('executing command: ', command)
            cursor.execute(command)

    def convertDatumFormat4SQL(self, datum):
        # print(sys._getframe().f_code.co_name)
        # newDate = datetime.strptime(datum, '%d.%m.%y')
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y', '%d.%m.%y'):
            try:
                newDate = datetime.strptime(datum, fmt)
                return newDate.date()
            except ValueError:
                pass
        raise ValueError('no valid date format found: {}'.format(datum))

    def convertDateTimeFormat4SQL(self, datum):
        # print(sys._getframe().f_code.co_name)
        # newDate = datetime.strptime(datum, '%d.%m.%y') 2024/09/21 11:10
        for fmt in ('%Y/%m/%d %H:%M', '%Y-%m-%d %H:%M'):
            try:
                newDate = datetime.strptime(datum, fmt)
                return newDate
            except ValueError:
                pass
        raise ValueError('no valid date format found: {}'.format(datum))

    def convertTimeFormat4SQL(self, time):
        # print(sys._getframe().f_code.co_name)
        # newDate = datetime.strptime(datum, '%d.%m.%y')
        for fmt in ('%H:%M', '%H:%M:%S'):
            try:
                newDate = datetime.strptime(time, fmt)
                return newDate.time()
            except ValueError:
                pass
        raise ValueError('no valid date format found')

    def returnColumn(self, col):
        query = 'SELECT {} FROM {}'.format(col, self.tableName)
        cursor = self.db.cursor()
        # vals = (column2Del, )
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        values = []
        for i in records:
            values.append(i[0])
        return values

    def returnColumns(self, cols):
        strTableHead = ''
        for col in cols:
            strTableHead += '{}, '.format(col)
        strTableHead = strTableHead[:-2]

        query = 'SELECT {} FROM {}'.format(strTableHead, self.tableName)
        cursor = self.db.cursor()
        # vals = (column2Del, )
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        values = []
        for i in records:
            values.append(i)
        return values

    def returnCellsWhere(self, col, matches):
        if isinstance(matches, tuple):
            searchCol, searchKey = matches
            if isinstance(searchKey, str) or isinstance(searchKey, int):
                query = "SELECT {} FROM {} WHERE {} = '{}'".format(col, self.tableName, searchCol, searchKey)
            if isinstance(searchKey, tuple):
                query = "SELECT {} FROM {} WHERE {} IN {}".format(col, self.tableName, searchCol, searchKey)
        elif isinstance(matches, list):
            text = ''
            for i in matches:
                searchCol, searchKey = i
                new = '{} = "{}" AND '.format(searchCol, searchKey)
                text += new
            query = "SELECT {} FROM {} WHERE ".format(col, self.tableName) + text[:-4]
        else:
            raise TypeError('{} must be tuple or list of tuples'.format(matches))

        cursor = self.db.cursor()
        # print('query', query)
        cursor.execute(query)
        records = cursor.fetchall()
        # print('*****records', records, type(records))
        cursor.close()
        values = []
        # colType = self.get_column_type(col)
        for i in records:
            # print('ßßßßßßß', colType)
            # print('ßßßßßßß', i[0])
            # if colType == 'longblob':
            #     values.append(i[0])
            #     # continue
            # # elif colType == 'json':
            # #     values.append(json.loads(i[0]))
            # else:
            values.append(i[0])
        return values

    def returnCellsWhereDiffrent(self, col, matches):
        if isinstance(matches, tuple):
            searchCol, searchKey = matches
            if isinstance(searchKey, str) or isinstance(searchKey, int):
                query = "SELECT {} FROM {} WHERE {} != '{}'".format(col, self.tableName, searchCol, searchKey)
        elif isinstance(matches, list):
            text = ''
            for i in matches:
                searchCol, searchKey = i
                new = '{} != "{}" AND '.format(searchCol, searchKey)
                text += new
            query = "SELECT {} FROM {} WHERE ".format(col, self.tableName) + text[:-4]
        else:
            raise TypeError('{} must be tuple or list of tuples'.format(matches))

        cursor = self.db.cursor()
        # print('query', query)
        cursor.execute(query)
        records = cursor.fetchall()
        # print(records)
        cursor.close()
        values = []
        colType = self.get_column_type(col)
        for i in records:
            if colType == 'json':
                values.append(json.loads(i[0]))
            else:
                values.append(i[0])
        return values

    def returnColsWhere(self, cols, matches):
        relCols = ''
        for col in cols:
            relCols += '{}, '.format(col)
        relCols = relCols[:-2]

        if isinstance(matches, tuple):
            searchCol, searchKey = matches
            if isinstance(searchKey, str) or isinstance(searchKey, int):
                query = "SELECT {} FROM {} WHERE {} = '{}'".format(relCols, self.tableName, searchCol, searchKey)
            if isinstance(searchKey, tuple):
                query = "SELECT {} FROM {} WHERE {} IN '{}'".format(relCols, self.tableName, searchCol, searchKey)
            if searchKey is None:
                query = "SELECT {} FROM {} WHERE {} IS NULL".format(relCols, self.tableName, searchCol)
        elif isinstance(matches, list):
            text = ''
            for i in matches:
                searchCol, searchKey = i
                if searchKey is None:
                    new = '{} IS NULL AND '.format(searchCol)
                else:
                    new = '{} = "{}" AND '.format(searchCol, searchKey)
                text += new
            query = "SELECT {} FROM {} WHERE ".format(relCols, self.tableName) + text[:-4]
        else:
            raise TypeError('{} must be tuple or list of tuples'.format(matches))

        cursor = self.db.cursor()
        # print('query', query)
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        values = []
        for i in records:
            values.append(i)
        return values

    def write_file(self, data, filename):
        # Convert binary data to proper format and write it on Hard Disk
        with open(filename, 'wb') as file:
            file.write(data)

    # def show_create_table_2(self, tableName):
    #     print('################')
    #     query = 'SELECT * FROM {}'.format(self.tableName)
    #     cursor = self.db.cursor()
    #     cursor.execute(query)
    #     records = cursor.fetchall()
    #     # print('++', query)
    #     data = ""
    #     for row in records:
    #         # print('ÄÄ', row)
    #         data += "INSERT INTO `" + str(self.tableName) + "` VALUES("
    #         first = True
    #         for field in row:
    #             if not first:
    #                 data += ', '
    #             data += '"' + str(field) + '"'
    #             first = False
    #
    #         data += ");\n"
    #     data += "\n\n"
    #
    #     values = []
    #     # for i in data:
    #     #     print(i)
    #     cursor.close()
    #     #     # values.append(i[0])
    #     # # return values
    #     # filename = str(os.getenv("HOME")) + "/backup_" + now.strftime("%Y-%m-%d_%H:%M") + ".sql"
    #     filename = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\bb.sql"
    #     # data = records[1]
    #     FILE = open(filename, "w")
    #     FILE.writelines(data)
    #     FILE.close()

    def compare_sql_file_to_sql_table(self, sql_file):
        f = open(sql_file)
        same = True
        diffrences = {}
        for line in f.read().splitlines():
            spl_row = line.split()
            if spl_row and '`' in spl_row[0]:
                sql_file_col = spl_row[0].strip('`')
                if sql_file_col in self.columnsDetProperties.keys():
                    col_type_file = spl_row[1]
                    col_type_sql = self.columnsDetProperties[sql_file_col][0]
                    if col_type_file != col_type_sql:
                        txt = 'Column {} has a different format in file than in sql table'.format(sql_file_col)
                        # print(txt)
                        same = False
                        diffrences[sql_file_col] = txt
                        # raise RuntimeError(txt)
                else:
                    print('sql_file_col', sql_file_col)
                    print('self.columnsDetProperties.keys()', self.columnsDetProperties.keys())
                    raise RuntimeError('Column {} missing in sql table file {}'.format(sql_file_col, sql_file))
        f.close()
        if not same:
            return diffrences


def convertDatumFormat4SQL(datum):
    # print(sys._getframe().f_code.co_name)
    # newDate = datetime.strptime(datum, '%d.%m.%y')
    for fmt in ('%Y%m%d','%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y', '%d.%m.%y'):
        try:
            newDate = datetime.strptime(datum, fmt)
            return newDate.date()
        except ValueError:
            pass
    raise ValueError('no valid date format found: {}'.format(datum))


def convertDateTimeFormat4SQL(datum):
    # print(sys._getframe().f_code.co_name)
    # newDate = datetime.strptime(datum, '%d.%m.%y') 2024/09/21 11:10
    for fmt in ('%Y/%m/%d %H:%M', '%Y-%m-%d %H:%M', '%Y%m%d_%H%M%S'):
        try:
            newDate = datetime.strptime(datum, fmt)
            return newDate
        except ValueError:
            pass
    raise ValueError('no valid date format found: {}'.format(datum))


if __name__ == '__main__':


    # if compName == 'DESKTOP-5HHINGF':
    #     ini_file = r"D:\Python\MySQL\cheltuieli.ini"
    # else:
    #     ini_file = r"C:\_Development\Diverse\pypi\cfgm.ini"
    #     # ini_file = r"C:\_Development\Diverse\pypi\cfgmRN.ini"

    ini_file = rappmysql.ini_chelt

    conf = connect.Config(ini_file)
    # print(conf.credentials)

    db = DataBase(conf.credentials)
    print(db.is_connected)

    # tables_dict = {'users': 'id',
    #                'all_cars': 'user_id',
    #                'masina': 'id_users'}
    # tables_dict = {'users': 'id',
    #                'banca': 'id_users',
    #                'income': 'id_users',
    #                'real_expenses_1': 'id_users',
    #                'chelt_plan': 'id_users',
    #                }

    # tables_dict = {'users': 'id',
    #                'banca': 'id_users',
    #                'chelt_plan': 'id_users',
    #                'knowntrans': 'id_users',
    #                'income': 'id_users',
    #                'deubnk': 'id_users',
    #                'n26': 'id_users',
    #                'sskm': 'id_users',
    #                'plan_vs_real': 'id_users',
    #                'imported_csv': 'id_users'
    #                }

    # output_dir = r'C:\_Development\Diverse\pypi\radu\masina\src\masina\static\backup_profile\000000001\000000001'
    # db.backup_profile_with_files(tables_dict, user_id=1, output_dir=output_dir, export_files=True)

    # db.drop_table_list(tab_list)

    matches = [('type', 'benzina'),
               ('id_users', 1),
               ('id_all_cars', 1)]

    ini_file = rappmysql.ini_masina

    conf = connect.Config(ini_file)
    credentials = conf.credentials
    alimentari = Table(credentials, 'masina')
    rows = alimentari.returnRowsWhere(matches)
    for ii in rows:
        print(ii)