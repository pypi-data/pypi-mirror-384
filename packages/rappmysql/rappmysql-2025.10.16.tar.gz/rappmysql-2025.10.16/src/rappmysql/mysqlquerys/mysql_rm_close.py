import os.path
import pathlib
import json
import mysql.connector as mysql
from mysql.connector import pooling
import re
import codecs
import sys
import traceback
import numpy as np
import subprocess
from datetime import datetime
from contextlib import contextmanager
import warnings
from rappmysql.mysqlquerys import connect
import rappmysql

compName = os.getenv('COMPUTERNAME')


import os
import re
import sys
import traceback
import subprocess
from datetime import datetime
from mysql.connector import pooling
import mysql.connector as mysql


class DataBase:
    def __init__(self, credentials):
        self.db_name = credentials['database']
        self.pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=3,
            pool_reset_session=True,
            **credentials
        )

    def get_connection(self):
        """Get a connection from the pool"""
        return self.pool.get_connection()

    @property
    def is_connected(self):
        db = self.get_connection()
        try:
            return db.is_connected()
        finally:
            db.close()

    @property
    def dataBaseVersion(self):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute('SELECT version()')
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @property
    def allAvailableTablesInDatabase(self):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SHOW TABLES")
            tables = [row[0] for row in cur.fetchall()]
            return sorted(tables)
        finally:
            cur.close()
            conn.close()

    @property
    def allAvailableDatabases(self):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SHOW DATABASES")
            databases = [row[0] for row in cur.fetchall()]
            return sorted(databases)
        finally:
            cur.close()
            conn.close()

    def checkProcess(self):
        query = "SHOW PROCESSLIST"
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query)
            records = cur.fetchall()
        finally:
            cur.close()
            conn.close()
        return records

    def killProcess(self, processes):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            for process in processes:
                query = f"KILL {process}"
                cur.execute(query)
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def killAllProcess(self):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            query = "SHOW PROCESSLIST"
            cur.execute(query)
            records = cur.fetchall()
            for process in records:
                if process[-1] == 'SHOW PROCESSLIST':
                    continue
                kill_query = f"KILL {process[0]}"
                cur.execute(kill_query)
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def run_sql_file(self, file):
        error = None
        command = ''
        try:
            with open(file, errors="ignore", encoding="utf-8") as f:
                for line in f.read().splitlines():
                    command += line
                    if ';' in line:
                        conn = self.get_connection()
                        cur = conn.cursor()
                        try:
                            cur.execute(command)
                            conn.commit()
                            command = ''
                        except mysql.Error as err:
                            error = (err.msg, command)
                            break
                        finally:
                            cur.close()
                            conn.close()
        except Exception:
            error = traceback.format_exc()
        return error

    def createTableFromFile(self, file, newTableName):
        error = None
        command = ''
        try:
            with open(file) as f:
                for line in f.read().splitlines():
                    command += line
                    if ';' in line:
                        if re.search("^CREATE TABLE", command) or \
                                re.search("^ALTER TABLE", command) or \
                                re.search("^INSERT INTO", command):
                            match = re.findall(r"\`(.+?)\`", command)
                            if match:
                                tableName = match[0]
                                command = command.replace(tableName, newTableName)
                        conn = self.get_connection()
                        cur = conn.cursor()
                        try:
                            cur.execute(command)
                            conn.commit()
                            command = ''
                        except mysql.Error as err:
                            error = (err.msg, command)
                            break
                        finally:
                            cur.close()
                            conn.close()
        except Exception:
            error = traceback.format_exc()
        return error

    def createTableList(self, fileList):
        errList = []
        # copy fileList to avoid mutation during iteration
        files_to_process = fileList[:]

        while files_to_process:
            for i, file in enumerate(files_to_process):
                error = self.createTableFromFile(file, newTableName="")  # You may need to adjust this param
                if error:
                    if error[0] == 'Cannot add foreign key constraint' or \
                            re.search("^relation.*does not exist$", error[0]):
                        errList.append(error[1])
                        files_to_process.pop(i)
                        break
                    elif 'already exists' in error[0]:
                        files_to_process.pop(i)
                        break
                    else:
                        files_to_process.pop(i)
                        break
                else:
                    files_to_process.pop(i)
                    break

        probList = []
        for com in errList:
            conn = self.get_connection()
            cur = conn.cursor()
            try:
                cur.execute(com)
                conn.commit()
            except Exception:
                error = (traceback.format_exc(), com)
                probList.append(error)
            finally:
                cur.close()
                conn.close()

        if probList:
            for i in errList:
                print(i)
        else:
            print('Successfully')

    def drop_table(self, tableName):
        query = "DROP TABLE IF EXISTS {};".format(tableName)
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query)
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def drop_table_list(self, tableList):
        results = []
        while tableList:
            for i, tab in enumerate(tableList):
                if tab not in self.allAvailableTablesInDatabase:
                    tableList.pop(i)
                    break
                conn = self.get_connection()
                cur = conn.cursor()
                try:
                    query = "SELECT table_name FROM information_schema.KEY_COLUMN_USAGE " \
                            "WHERE table_schema = %s AND referenced_table_name = %s "
                    cur.execute(query, (self.db_name, tab))
                    children = [row for row in cur.fetchall() if row[0]]

                    if not children:
                        cur.close()
                        conn.close()
                        self.drop_table(tab)
                        results.append(True)
                        tableList.pop(i)
                        break
                    else:
                        for child in children:
                            if child[0] not in tableList:
                                cur.close()
                                conn.close()
                                self.drop_table(tab)
                                results.append(True)
                                tableList.pop(i)
                                break
                        else:
                            # If none of the children triggered a drop, just close here and continue
                            cur.close()
                            conn.close()
                except:
                    cur.close()
                    conn.close()
                    raise
        return results

    def rename_table(self, tableName, newName):
        query = 'RENAME TABLE {} TO {}'.format(tableName, newName)
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query)
            conn.commit()
        except mysql.connector.Error as err:
            print(err.msg)
        finally:
            cur.close()
            conn.close()

    def deleteAllDataInTable(self, tableList):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            for tab in tableList:
                query = 'DELETE FROM {}'.format(tab)
                cur.execute(query)
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def export_database(self, output_file):
        cmd = ['mysqldump', '-u', 'root', '-p', 'cheltuieli_desktop', '>', output_file]
        try:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True)
            out, err = p.communicate()
            if p.returncode != 0:
                print('returncode: ', p.returncode)
                print('Error: ', err)
            else:
                print('Done: {}'.format(cmd))
        except Exception:
            print('Failed to export database.')

    def show_create_table(self, tableName):
        query = 'SHOW CREATE TABLE {}'.format(tableName)
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            records = cursor.fetchall()
            data = records[0][1]
            filename = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\aa.sql"
            with open(filename, "w") as FILE:
                FILE.writelines(data)
        finally:
            cursor.close()
            conn.close()

    def show_create_table_2(self, tableName):
        query = 'SELECT * FROM {}'.format(tableName)
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            records = cursor.fetchall()
            data = ""
            for row in records:
                data += "INSERT INTO `" + str(tableName) + "` VALUES("
                data += ', '.join('"' + str(field) + '"' for field in row)
                data += ");\n"
            data += "\n\n"
            filename = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\bb.sql"
            with open(filename, "w") as FILE:
                FILE.writelines(data)
        finally:
            cursor.close()
            conn.close()

    def export_tables_to_sql(self, tables, output_sql_file):
        data = ""
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            for table in tables:
                cur.execute("SHOW CREATE TABLE `{}`;".format(table))
                data += "\n" + str(cur.fetchone()[1]) + ";\n\n"
                cur.execute("SELECT * FROM `{}`;".format(table))
                for row in cur.fetchall():
                    row_data = ', '.join('"{}"'.format(str(field)) for field in row)
                    data += f"INSERT INTO `{table}` VALUES({row_data});\n"
                data += "\n\n"
            with open(output_sql_file, "w") as FILE:
                FILE.writelines(data)
        finally:
            cur.close()
            conn.close()

    def backup_profile_with_files(self, tables, user_id, output_dir=None, export_files=True):
        if not output_dir:
            tim = datetime.strftime(datetime.now(), '%Y_%m_%d__%H_%M_%S')
            dir = os.path.dirname(__file__)
            output_dir_name = '{}_{}'.format(tim, '{:09d}'.format(user_id))
            output_dir = os.path.join(dir, 'static', 'backup_profile', '{:09d}'.format(user_id), output_dir_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        data = ""
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            for table in tables:
                cur.execute(f"SHOW CREATE TABLE {table}")
                create_sql = cur.fetchone()[1].replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
                data += "\n{};\n\n".format(create_sql)

                cur.execute(f"DESC {table}")
                cols = cur.fetchall()
                file_cols = [col[0] for col in cols if 'file' in col[0]]
                export_cols = [col[0] for col in cols if col[0] not in file_cols]

                export_cols_query = ', '.join(export_cols)
                query = f"SELECT {export_cols_query} FROM {table} WHERE {tables[table]} = {user_id};"
                cur.execute(query)
                for row in cur.fetchall():
                    values = ', '.join(
                        'NULL' if val is None else '"{}"'.format(str(val).replace('"', "'")) for val in row)
                    data += f"INSERT IGNORE INTO {table} ({export_cols_query}) VALUES({values});\n"
                data += "\n\n"

                if file_cols and export_files:
                    file_export_query = ', '.join(file_cols)
                    query = f"SELECT id, {file_export_query} FROM {table} WHERE {tables[table]} = {user_id};"
                    cur.execute(query)
                    for row in cur.fetchall():
                        row_id, file_blob, file_name = row
                        if not file_blob:
                            continue
                        file_path = os.path.join(output_dir, f"{user_id}+{table}+{row_id}+{file_name}")
                        with open(file_path, 'wb') as f:
                            f.write(file_blob)

            output_file = f"{datetime.strftime(datetime.now(), '%Y_%m_%d__%H_%M_%S')}_user_name.sql"
            with open(os.path.join(output_dir, output_file), "w", encoding="utf-8") as FILE:
                FILE.writelines(data)
        finally:
            cur.close()
            conn.close()

    def return_sql_text_bkp(self, tables):
        data = ""
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            for table in tables:
                cur.execute(f"SHOW CREATE TABLE {table}")
                create_sql = cur.fetchone()[1].replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
                data += "\n{};\n\n".format(create_sql)

                cur.execute(f"DESC {table}")
                cols = cur.fetchall()
                export_cols = [col[0] for col in cols if 'file' not in col[0]]
                export_cols_query = ', '.join(export_cols)

                where_clause = ' AND '.join(f"{k} = {v}" for k, v in tables[table].items())
                cur.execute(f"SELECT {export_cols_query} FROM {table} WHERE {where_clause};")
                for row in cur.fetchall():
                    values = ', '.join(
                        'NULL' if val is None else '"{}"'.format(str(val).replace('"', "'")) for val in row)
                    data += f"INSERT IGNORE INTO {table} ({export_cols_query}) VALUES({values});\n"
                data += "\n\n"
        finally:
            cur.close()
            conn.close()
        return data

    def return_sql_text(self, tables, export_files=False, export_all_users=False):
        data = ""
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            for table in tables:
                cur.execute(f"SHOW CREATE TABLE {table}")
                create_sql = cur.fetchone()[1].replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
                data += "\n{};\n\n".format(create_sql)

                cur.execute(f"DESC {table}")
                cols = cur.fetchall()
                file_cols = [col[0] for col in cols if 'file' in col[0]]
                export_cols = [col[0] for col in cols if col[0] not in file_cols]
                export_cols_query = ', '.join(export_cols)

                if export_all_users:
                    query = f"SELECT {export_cols_query} FROM {table}"
                else:
                    where_clause = ' AND '.join(f"{k} = {v}" for k, v in tables[table].items())
                    query = f"SELECT {export_cols_query} FROM {table} WHERE {where_clause};"
                cur.execute(query)
                for row in cur.fetchall():
                    values = ', '.join(
                        'NULL' if val is None else '"{}"'.format(str(val).replace('"', "'")) for val in row)
                    data += f"INSERT IGNORE INTO {table} ({export_cols_query}) VALUES({values});\n"
                data += "\n\n"

                if file_cols and export_files:
                    file_export_query = ', '.join(file_cols)
                    query = f"SELECT id, {file_export_query} FROM {table} WHERE {where_clause};"
                    cur.execute(query)
                    for row in cur.fetchall():
                        row_id, file_blob, file_name = row
                        if not file_blob:
                            continue
                        filename = os.path.join(export_files, f"{row_id}+{file_name}")
                        with open(filename, 'wb') as f:
                            f.write(file_blob)
        finally:
            cur.close()
            conn.close()
        return data

    def createAliasTempTable(self, tableName, colDict, origTab):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            select_query = ', '.join(f'{col} {alias}' for col, alias in colDict.items())
            cur.execute(f"CREATE TEMPORARY TABLE {tableName} SELECT {select_query} FROM {origTab}")
            cur.execute(f"DESC {tableName}")
            tableHead = [i[0] for i in cur.fetchall()]
            cur.execute(f"SELECT * FROM {tableName}")
            table = cur.fetchall()
        finally:
            cur.close()
            conn.close()
        return tableHead, table

    def descAliasTempTable(self, tableName, colDict, origTab):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            select_query = ', '.join(f'{col} {alias}' for col, alias in colDict.items())
            cur.execute(f"CREATE TEMPORARY TABLE {tableName} SELECT {select_query} FROM {origTab}")
            cur.execute(f"DESC {tableName}")
            tableHead = [i[0] for i in cur.fetchall()]
            cur.execute(f"SELECT * FROM {tableName}")
            table = cur.fetchall()
        finally:
            cur.close()
            conn.close()
        return tableHead, table

    # def close(self):
    #     """Close the database connection."""
    #     if self.cursor:
    #         self.cursor.close()
    #     if self.conn:
    #         self.conn.close()


class Table(DataBase):
    def __init__(self, credentials, tableName):
        super().__init__(credentials)
        self.tableName = tableName

    @property
    def noOfRows(self):
        query = 'SELECT COUNT(*) FROM {}'.format(self.tableName)
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            noOfRows = cursor.fetchone()[0]
        finally:
            cursor.close()
            conn.close()
        return noOfRows

    def lastRowId(self):
        query = 'SELECT id FROM {} ORDER BY id DESC LIMIT 1'.format(self.tableName)
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query)
            lastId = cur.fetchone()
            if lastId is None:
                return 0
            return lastId[0]
        finally:
            cur.close()
            conn.close()

    @property
    def columnsNames(self):
        query = 'DESC {}'.format(self.tableName)
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            res = cursor.fetchall()
            cols = [col[0] for col in res]
        finally:
            cursor.close()
            conn.close()
        return cols

    @property
    def columnsDetProperties(self):
        query = 'DESC {}'.format(self.tableName)
        colNames = ['Field', 'Type', 'Null', 'Key', 'Default', 'Extra']
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            res = cursor.fetchall()
            cols = {}
            for col in res:
                colName, colType, null, key, default, extra = col
                if isinstance(colType, bytes):
                    colType = colType.decode("utf-8")
                cols[colName] = [colType, null, key, default, extra]
        finally:
            cursor.close()
            conn.close()
        return cols

    @property
    def columnsProperties(self):
        query = (
            "SELECT table_name, column_name, data_type FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{}'").format(
            self.tableName)
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            res = cursor.fetchall()
            cols = {col_name: data_type for _, col_name, data_type in res}
        finally:
            cursor.close()
            conn.close()
        return cols

    @property
    def children_tables(self):
        query = "SELECT table_name FROM information_schema.KEY_COLUMN_USAGE WHERE table_schema = %s AND referenced_table_name = %s"
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query, (self.db_name, self.tableName))
            children = [row[0] for row in cur.fetchall() if row[0]]
        finally:
            cur.close()
            conn.close()
        return children

    def rename_column(self, tableName, old_col_name, new_col_name):
        query = 'ALTER TABLE {} RENAME COLUMN {} TO {}'.format(tableName, old_col_name, new_col_name)
        db = self.get_connection()
        cur = db.cursor()
        try:
            cur.execute(query)
        except mysql.connector.Error as err:
            print(err.msg)
        finally:
            cur.close()
            db.close()

    def deleteRow(self, condition):
        colName, value = condition
        query = 'DELETE FROM {} WHERE {} = %s'.format(self.tableName, colName)
        db = self.get_connection()
        cursor = db.cursor()
        try:
            cursor.execute(query, (value,))
            db.commit()
        finally:
            cursor.close()
            db.close()

    def delete_multiple_rows(self, condition):
        colName, value = condition
        query = 'DELETE FROM {} WHERE {} = %s'.format(self.tableName, colName)
        db = self.get_connection()
        cursor = db.cursor()
        try:
            cursor.execute(query, (value,))
            db.commit()
        finally:
            cursor.close()
            db.close()

    def delete_multiple_rows_multiple_conditions(self, condition):
        colName, value = condition
        query = 'DELETE FROM {} WHERE {} = %s'.format(self.tableName, colName)
        db = self.get_connection()
        cursor = db.cursor()
        try:
            cursor.execute(query, (value,))
            db.commit()
        finally:
            cursor.close()
            db.close()

    def convertToBinaryData(self, filename):
        with open(filename, 'rb') as file:
            binaryData = file.read()
        return binaryData

    def addNewRow(self, columns, values):
        strCols = ', '.join(columns)
        strVals = ', '.join(['%s'] * len(columns))
        query = "INSERT INTO {} ({}) VALUES ({})".format(self.tableName, strCols, strVals)

        if isinstance(values, (int, str)):
            values = (values,)
        elif isinstance(values, tuple):
            new_vals = []
            for v in values:
                if isinstance(v, str) and os.path.isfile(v):
                    v = self.convertToBinaryData(v)
                new_vals.append(v)
            values = tuple(new_vals)

        db = self.get_connection()
        cursor = db.cursor()
        try:
            cursor.execute(query, values)
            db.commit()
        except Exception as e:
            print('Insert error:', e)
            print('Query:', query)
            print('Values:', values)
            raise
        finally:
            cursor.close()
            db.close()
        return cursor.lastrowid

    def addNewRowWithFile(self, columns, values):
        strCols = ', '.join(columns)
        strVals = ', '.join(['%s'] * len(columns))
        query = "INSERT INTO {} ({}) VALUES ({})".format(self.tableName, strCols, strVals)
        print('Executing:', query)

        if isinstance(values, (int, str)):
            values = (values,)
        elif isinstance(values, tuple):
            new_vals = []
            for v in values:
                if isinstance(v, pathlib.Path):
                    if v.is_file():
                        v = self.convertToBinaryData(str(v))
                new_vals.append(v)
            values = tuple(new_vals)

        db = self.get_connection()
        cursor = db.cursor()
        try:
            cursor.execute(query, values)
            db.commit()
            print('Executed successfully')
        except mysql.connector.Error as err:
            if err.errno == 2013 and 'Lost connection' in err.msg:
                print('Handling lost connection error...')
                cursor.execute('SET max_allowed_packet=67108864')
                db.commit()
                cursor.execute(query, values)
                db.commit()
                print('Re-executed successfully')
            else:
                print('MySQL Error:', err.errno, err.msg)
                raise
        finally:
            cursor.close()
            db.close()
        return cursor.lastrowid

    def insertColumns(self, column_name, column_definition, afterCol):
        if afterCol == 'FIRST':
            query = 'ALTER TABLE {} ADD COLUMN {} {} FIRST'.format(self.tableName, column_name, column_definition)
        else:
            query = 'ALTER TABLE {} ADD COLUMN {} {} AFTER {}'.format(self.tableName, column_name, column_definition,
                                                                      afterCol)
        db = self.get_connection()
        cursor = db.cursor()
        try:
            cursor.execute(query)
            db.commit()
        finally:
            cursor.close()
            db.close()

    def returnAllRecordsFromTable(self):
        db = self.get_connection()
        cur = db.cursor()
        try:
            query = 'SELECT * FROM {}'.format(self.tableName)
            cur.execute(query)
            records = cur.fetchall()
        finally:
            cur.close()
            db.close()
        return records

    def returnAllRecordsFromTableExceptBlob(self):
        db = self.get_connection()
        cur = db.cursor()
        try:
            query = 'SELECT '
            for col_name, prop in self.columnsDetProperties.items():
                if prop[0] == 'longblob':
                    continue
                query += f'{col_name}, '
            query = query.rstrip(', ')
            query += ' FROM {}'.format(self.tableName)
            print('Executing:', query)
            cur.execute(query)
            records = cur.fetchall()
        finally:
            cur.close()
            db.close()
        return records

    def returnLastRecords(self, column, noOfRows2Return):
        db = self.get_connection()
        cur = db.cursor()
        try:
            query = 'SELECT * FROM {} ORDER BY {} DESC LIMIT %s'.format(self.tableName, column)
            cur.execute(query, (noOfRows2Return,))
            rows = cur.fetchall()
        finally:
            cur.close()
            db.close()
        return rows

    def filterRows(self, matches, order_by=None):
        filterText = ''
        for match in matches:
            search_col, search_key = match
            if isinstance(search_key, tuple):
                min, max = search_key
                new = "{} >= '{}' AND {} <= '{}' AND ".format(search_col, min, search_col, max)
                filterText += new
            elif isinstance(search_key, list):
                new = "{} in {} AND ".format(search_col, tuple(search_key))
                filterText += new
            elif search_key == 'None' or search_key is None:
                new = "{} IS NULL AND ".format(search_col)
                filterText += new
            else:
                new = "{} = '{}' AND ".format(search_col, search_key)
                filterText += new

        query = 'SELECT '
        for col_name, prop in self.columnsDetProperties.items():
            if prop[0] == 'longblob':
                continue
            query += '{}, '.format(col_name)
        query = query[:-2]
        query += ' FROM {} WHERE {} '.format(self.tableName, filterText[:-4])

        if order_by:
            col, order = order_by
            query += 'ORDER BY {} {}'.format(col, order)

        db = self.get_connection()
        cur = db.cursor()
        cur.execute(query)
        records = cur.fetchall()
        cur.close()
        db.close()
        return records

    def returnRowsWhere(self, matches):
        has_longblob_col = False
        cols_without_longblob = ''
        for col_name, prop in self.columnsDetProperties.items():
            if prop[0] == 'longblob':
                has_longblob_col = True
            else:
                cols_without_longblob += '{}, '.format(col_name)
        cols_without_longblob = cols_without_longblob[:-2]

        if isinstance(matches, tuple):
            searchCol, searchKey = matches
            if isinstance(searchKey, (str, int)):
                query = "SELECT * FROM {} WHERE {} = '{}'".format(self.tableName, searchCol, searchKey)
            elif isinstance(searchKey, tuple):
                query = "SELECT * FROM {} WHERE {} IN '{}'".format(self.tableName, searchCol, searchKey)
            elif searchKey is None:
                query = "SELECT * FROM {} WHERE {} IS NULL".format(self.tableName, searchCol)
        elif isinstance(matches, list):
            text = ''
            for i in matches:
                searchCol, searchKey = i
                if searchKey is None:
                    text += '{} IS NULL AND '.format(searchCol)
                else:
                    text += '{} = "{}" AND '.format(searchCol, searchKey)
            query = "SELECT * FROM {} WHERE ".format(self.tableName) + text[:-4]
        else:
            raise TypeError('{} must be tuple or list of tuples'.format(matches))

        if has_longblob_col:
            query = query.replace('*', cols_without_longblob)

        db = self.get_connection()
        cursor = db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        db.close()
        return list(records)

    def returnRowsLike(self, column, keyWord):
        query = "SELECT * FROM {} WHERE {} LIKE '%{}%'".format(self.tableName, column, keyWord)
        db = self.get_connection()
        cur = db.cursor()
        cur.execute(query)
        records = cur.fetchall()
        cur.close()
        db.close()
        return records

    def returnRowsYoungerThan(self, column, timeP):
        query = "SELECT * FROM {} WHERE {} > %s ORDER BY {} DESC".format(self.tableName, column, column)
        db = self.get_connection()
        cur = db.cursor()
        cur.execute(query, (timeP,))
        records = cur.fetchall()
        cur.close()
        db.close()
        return records

    def returnRowsInInterval(self, startColumn, startTime, endColumn, endTime):
        query = "SELECT * FROM {} WHERE {} > %s OR {} < %s".format(self.tableName, startColumn, endColumn)
        db = self.get_connection()
        cur = db.cursor()
        cur.execute(query, (startTime, endTime))
        records = cur.fetchall()
        cur.close()
        db.close()
        return records

    def returnRowsWhereValueIsInIntervalAND(self, colWhere, keyWord, startColumn, valueInInterval, endColumn):
        query = "SELECT * FROM {} WHERE {} = %s AND %s > {} AND {} > %s".format(self.tableName, colWhere, startColumn,
                                                                                endColumn)
        db = self.get_connection()
        cur = db.cursor()
        cur.execute(query, (keyWord, valueInInterval, valueInInterval))
        records = cur.fetchall()
        cur.close()
        db.close()
        return records

    def returnCellWhereValueIsInIntervalAND(self, col2return, colWhere, keyWord, startColumn, valueInInterval,
                                            endColumn):
        query = ("SELECT {} FROM {} WHERE {} = %s AND %s > {} AND ({} > %s OR {} IS NULL)"
                 .format(col2return, self.tableName, colWhere, startColumn, endColumn, endColumn))
        db = self.get_connection()
        cur = db.cursor()
        cur.execute(query, (keyWord, valueInInterval, valueInInterval))
        records = cur.fetchall()
        cur.close()
        db.close()
        return records

    def returnRowsQuery(self, matches, order_by=None):
        filterText = ''
        for match in matches:
            search_col, sign, search_value = match
            if sign == 'LIKE':
                filterText += "{} {} '%{}%' AND ".format(search_col, sign, search_value)
            elif sign == '==' and search_value is None:
                filterText += "{} IS NULL AND ".format(search_col)
            elif sign == '!=' and search_value is None:
                filterText += "{} IS NOT NULL AND ".format(search_col)
            else:
                filterText += "{} {} '{}' AND ".format(search_col, sign, search_value)

        query = 'SELECT '
        for col_name, prop in self.columnsDetProperties.items():
            if prop[0] == 'longblob':
                continue
            query += '{}, '.format(col_name)
        query = query[:-2]
        query += ' FROM {} WHERE {} '.format(self.tableName, filterText[:-4])
        if order_by:
            col, order = order_by
            query += 'ORDER BY {} {}'.format(col, order)

        # print('__query__', query)
        db = self.get_connection()
        cur = db.cursor()
        cur.execute(query)
        records = cur.fetchall()
        cur.close()
        db.close()
        return records

    def return_from_table(self, matches, colname=None, with_files=False, order_by=None):
        filterText = ''
        for match in matches:
            search_col, sign, search_value = match
            if sign == 'LIKE':
                filterText += "{} {} '%{}%' AND ".format(search_col, sign, search_value)
            elif sign == '==' and search_value is None:
                filterText += "{} IS NULL AND ".format(search_col)
            elif sign == '!=' and search_value is None:
                filterText += "{} IS NOT NULL AND ".format(search_col)
            else:
                filterText += "{} {} '{}' AND ".format(search_col, sign, search_value)

        if colname:
            query = 'SELECT {} '.format(colname)
        else:
            if with_files:
                query = 'SELECT * '
            else:
                query = 'SELECT '
                for col_name, prop in self.columnsDetProperties.items():
                    if prop[0] == 'longblob':
                        continue
                    query += '{}, '.format(col_name)
                query = query[:-2]

        query += ' FROM {} WHERE {} '.format(self.tableName, filterText[:-4])
        if order_by:
            col, order = order_by
            query += 'ORDER BY {} {}'.format(col, order)

        print('__query__', query)
        db = self.get_connection()
        cur = db.cursor()
        cur.execute(query)
        records = cur.fetchall()
        cur.close()
        db.close()
        return records

    def returnRowsOfYear(self, startColumn, startTime, endColumn, endTime):
        query = "SELECT * FROM {} WHERE {} >= %s AND {} <= %s".format(self.tableName, startColumn, endColumn)
        db = self.get_connection()
        cur = db.cursor()
        cur.execute(query, (startTime, endTime))
        records = cur.fetchall()
        cur.close()
        db.close()
        return records

    def returnRowsOutsideInterval(self, startColumn, startTime, endColumn, endTime):
        query = "SELECT * FROM {} WHERE {} < %s AND {} > %s".format(self.tableName, startColumn, endColumn)
        db = self.get_connection()
        cur = db.cursor()
        cur.execute(query, (startTime, endTime))
        records = cur.fetchall()
        cur.close()
        db.close()
        return records

    def get_column_type(self, column):
        colProps = self.columnsProperties[column]
        colType = colProps[0]
        return colType

    def modify2AutoIncrement(self, column, colType):
        query = 'ALTER TABLE {} MODIFY {} {} AUTO_INCREMENT;'.format(self.tableName, column, colType)
        print(query)
        db = self.get_connection()
        cursor = db.cursor()
        cursor.execute(query)
        db.commit()
        cursor.close()
        db.close()

    def modifyType(self, column, colType):
        query = 'ALTER TABLE {} MODIFY {} {};'.format(self.tableName, column, colType)
        db = self.get_connection()
        cursor = db.cursor()
        cursor.execute(query)
        db.commit()
        cursor.close()
        db.close()

    def changeCellContent(self, column2Modify, val2Moify, refColumn, refValue):
        db = self.get_connection()
        cursor = db.cursor()
        try:
            if isinstance(refValue, tuple):
                query = "UPDATE {} SET {} = {} WHERE {} IN {}".format(self.tableName, column2Modify, val2Moify,
                                                                      refColumn, refValue)
                cursor.execute(query)
                db.commit()
                cursor.close()
                db.close()
                return
            else:
                query = "UPDATE {} SET {} = %s WHERE {} = %s".format(self.tableName, column2Modify, refColumn)
            print(query)
            print('val2Moify', val2Moify)

            if isinstance(val2Moify, str):
                if os.path.isfile(val2Moify):
                    print('aaaaa', val2Moify, type(val2Moify))
                    val2Moify = self.convertToBinaryData(val2Moify)
            vals = (val2Moify, int(refValue))
            cursor.execute(query, vals)
            db.commit()
            cursor.close()
            db.close()
        except mysql.Error as err:
            print('++', err)
            print('query', query)
            print('vals', vals)
            print('ERROR mysql.Error: ', err.msg)
            cursor.close()
            db.close()

    def dropColumn(self, column2Del):
        query = "ALTER TABLE {} DROP COLUMN {};".format(self.tableName, column2Del)
        print(query)
        db = self.get_connection()
        cursor = db.cursor()
        cursor.execute(query)
        db.commit()
        cursor.close()
        db.close()

    def executeQuery(self, query):
        print(sys._getframe().f_code.co_name)
        db = self.get_connection()
        cursor = db.cursor()
        if isinstance(query, str):
            commands = query.split(';')
        for command in commands:
            print('executing command: ', command)
            cursor.execute(command)
        cursor.close()
        db.close()

    def convertDatumFormat4SQL(self, datum):
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y', '%d.%m.%y'):
            try:
                newDate = datetime.strptime(datum, fmt)
                return newDate.date()
            except ValueError:
                pass
        raise ValueError('no valid date format found: {}'.format(datum))

    def convertDateTimeFormat4SQL(self, datum):
        for fmt in ('%Y/%m/%d %H:%M', '%Y-%m-%d %H:%M'):
            try:
                newDate = datetime.strptime(datum, fmt)
                return newDate
            except ValueError:
                pass
        raise ValueError('no valid date format found: {}'.format(datum))

    def convertTimeFormat4SQL(self, time):
        for fmt in ('%H:%M', '%H:%M:%S'):
            try:
                newDate = datetime.strptime(time, fmt)
                return newDate.time()
            except ValueError:
                pass
        raise ValueError('no valid date format found')

    def returnColumn(self, col):
        query = 'SELECT {} FROM {}'.format(col, self.tableName)
        db = self.get_connection()
        cursor = db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        db.close()
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
        db = self.get_connection()
        cursor = db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        db.close()
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

        db = self.get_connection()
        cursor = db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        db.close()
        values = []
        for i in records:
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

        db = self.get_connection()
        cursor = db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        db.close()
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

        db = self.get_connection()
        cursor = db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        db.close()
        values = []
        for i in records:
            values.append(i)
        return values

    def write_file(self, data, filename):
        with open(filename, 'wb') as file:
            file.write(data)

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
                        same = False
                        diffrences[sql_file_col] = txt
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