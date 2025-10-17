import os.path
import mysql.connector as mysql
import re
import codecs
import sys
import traceback
import numpy as np
import subprocess
from datetime import datetime
from mysqlquerys import connect


class DataBase:
    def __init__(self, credentials):
        self.db = mysql.connect(**credentials)
        # self.db.set_session(autocommit=True)
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
                        # if 'REFERENCES' in command:
                        #     text = command.split('REFERENCES')[1]
                        #     match = re.findall(r"\`(.+?)\`", text)
                        #     referenceTable = match[0]
                        #     newRefName = "{} {}".format(self.schemaName, referenceTable)
                        #     refTab = '`{}`'.format(referenceTable)
                        #     newRef = '`{}`'.format(newRefName)
                        #     command = command.replace(refTab, newRef)
                    cur = self.db.cursor()
                    cur.execute(command)
                    command = ''
            f.close()
        except mysql.Error as err:
            print('ERROR mysql.Error: ', err.msg)
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
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        query = "DROP TABLE IF EXISTS {} CASCADE;".format(tableName)
        cur = self.db.cursor()
        cur.execute(query)
        cur.close()

    def drop_table_list(self, tableList):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        results = []
        while tableList:
            for i, tab in enumerate(tablelist):
                if self.connectionType == 'mysql':
                    exists = self.checkIfTableExists(tab)
                    if not exists:
                        print('table {} does not exist in database {}'.format(tab, self.dataBaseName))
                        tableList.pop(i)
                        continue
                    query = "SELECT table_name FROM information_schema.KEY COLUMN USAGE " \
                            "WHERE table_schema = %s AND referenced table_name = %s"
                    cur = self.db.cursor()
                    cur.execute(query, (self.dataBaseName, tab))
                    children = []
                    for cursor in cur.fetchall():
                        if cursor[0]:
                            children.append(cursor)
                    if not children:
                        res = self.drop_table(tab)
                        results.append(res)
                        tableList.pop(i)
                    else:
                        # if children make sure all of them are included in list
                        for child in children:
                            if child[0] not in tablelist:
                                print('if child not in tablelist:', tab, child, children)
                                err = self.drop_table(tab)
                                results.append(err)
                                tableList.pop(i)
                                break
                    cur.close()
                elif self.connectionType == 'postgresql':
                    res = self.drop_table(tab)
                    results.append(res)
                    tableList.pop(i)
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
        values = []
        # for i in records[1]:
        #     print(i)
        #     # values.append(i[0])
        # # return values
        # filename = str(os.getenv("HOME")) + "/backup_" + now.strftime("%Y-%m-%d_%H:%M") + ".sql"
        filename = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\aa.sql"
        data = records[1]
        FILE = open(filename, "w")
        FILE.writelines(data)
        FILE.close()

    # def show_create_table_2(self, tableName):
    #     print('################')
    #     query = 'SELECT * FROM {}'.format(tableName)
    #     cursor = self.db.cursor()
    #     cursor.execute(query)
    #     records = cursor.fetchall()
    #     # print('++', query)
    #     data = ""
    #     for row in records:
    #         # print('ÄÄ', row)
    #         data += "INSERT INTO `" + str(tableName) + "` VALUES("
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

    def backup_profile_with_id(self, tables, output_sql_file, user_id):
        data = ""
        cur = self.db.cursor()
        for table in tables:
            # print('::table', table)
            cur.execute("SHOW CREATE TABLE `" + str(table) + "`;")
            data += "\n" + str(cur.fetchone()[1]) + ";\n\n"

            cur.execute("SELECT * FROM `" + str(table) + "` WHERE {}={};".format(tables[table], user_id))
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

    def backup_profile_without_id(self, tables, output_sql_file, user_id):
        data = ""
        cur = self.db.cursor()
        for table in tables:
            print('::table', table)
            cur.execute("SHOW CREATE TABLE `" + str(table) + "`;")
            data += "\n" + str(cur.fetchone()[1]) + ";\n\n"

            cur.execute("SELECT * FROM `" + str(table) + "` where {}={};".format(tables[table], user_id))
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

        aa = data.split('\n')
        print(200*'+')
        for ii in aa:
            print(ii)
        print(200 * '+')
        # FILE = open(output_sql_file, "w")
        # FILE.writelines(data)
        # FILE.close()


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
        children = []
        for cursor in cur.fetchall():
            print(cursor)
            if cursor[0]:
                children.append(cursor[0])
        return children

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

    def addNewRow(self, columns, values):
        # print(len(columns), len(values))
        strCols = (('{}, ' * len(columns)).format(*columns))
        strCols = '({})'.format(strCols[:-2])
        strVals = ('%s,'*len(columns))
        strVals = '({})'.format(strVals[:-1])

        query = "INSERT INTO {} {} VALUES {}".format(self.tableName, strCols, strVals)
        #######
        print(query)
        for i in range(len(columns)):
            print(columns[i], values[i])
        #######
        if isinstance(values, int):
            values = (values, )
        elif isinstance(values, str):
            values = (values,)
        elif isinstance(values, tuple):
            print('values', values)
            new_vals = []
            for v in values:
                if isinstance(v, str):
                    if os.path.isfile(v):
                        v = self.convertToBinaryData(v)
                new_vals.append(v)
            values = tuple(new_vals)

        cursor = self.db.cursor()
        cursor.execute(query, values)
        self.db.commit()
        cursor.close()

        return cursor.lastrowid

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
                new = "{} > '{}' AND {} < '{}' AND ".format (search_col, min, search_col, max)
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

        cursor = self.db.cursor()
        # print('query', query)
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

    def returnRowsOfYear(self, startColumn, startTime, endColumn, endTime):
        # query = "SELECT * FROM {} WHERE {} > %s ORDER BY {} DESC".format(self.tableName, startColumn, startColumn)
        query = "SELECT * FROM {} WHERE {} > %s AND {} < %s".format(self.tableName, startColumn, endColumn)
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
        try:
            query = "UPDATE {} SET {} = %s WHERE {} = %s".format(self.tableName, column2Modify, refColumn)
            print(query)
            cursor = self.db.cursor()
            if isinstance(val2Moify, str):
                if os.path.isfile(val2Moify):
                    # print('aaaaa', val2Moify, type(val2Moify))
                    val2Moify = self.convertToBinaryData(val2Moify)
                    # print('aaaaa', val2Moify, type(val2Moify))
            vals = (val2Moify, refValue)
            # print(vals)
            cursor.execute(query, vals)
            self.db.commit()
            cursor.close()
        except mysql.Error as err:
            print('++', err)
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

    def importCSV(self, inpFile):
        with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
            linereader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for i, row in enumerate(linereader):
                if i == 0:
                    tableHead = row
                    continue
                if '' in row or 'None' in row:
                    new_strings = []
                    for string in row:
                        if string == '' or string == 'None':
                            new_strings.append(None)
                        else:
                            new_strings.append(string)
                    row = new_strings
                self.add_row(tableHead, row)

    def importSparkasseCSV(self, inpFile):
        with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
            linereader = csv.reader(csvfile, delimiter=';', quotechar='"')
            indxBuchungstag = self.columnsNames.index('Buchungstag')
            indxValutDatum = self.columnsNames.index('Valutadatum')
            indxBetrag = self.columnsNames.index('Betrag')
            for i, row in enumerate(linereader):
                # print(row)
                row.insert(0, i)
                if i == 0:
                    tableHead = row
                    continue
                if '' in row or 'None' in row:
                    new_strings = []
                    for string in row:
                        if string == '' or string == 'None':
                            new_strings.append(None)
                        else:
                            new_strings.append(string)
                    row = new_strings
                buchungstag = row[indxBuchungstag]
                valutDatum = row[indxValutDatum]
                betrag = row[indxBetrag]
                betrag = float(betrag.replace(',', '.'))
                buchungstag = self.convertDatumFormat4SQL(buchungstag)
                valutDatum = self.convertDatumFormat4SQL(valutDatum)

                row[indxBuchungstag] = buchungstag
                row[indxValutDatum] = valutDatum
                row[indxBetrag] = betrag
                self.add_row(self.columnsNames, row)

    def convertDatumFormat4SQL(self, datum):
        # print(sys._getframe().f_code.co_name)
        # newDate = datetime.strptime(datum, '%d.%m.%y')
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y', '%d.%m.%y'):
            try:
                newDate = datetime.strptime(datum, fmt)
                return newDate.date()
            except ValueError:
                pass
        raise ValueError('no valid date format found')

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

    def show_create_table_2(self, tableName):
        print('################')
        query = 'SELECT * FROM {}'.format(self.tableName)
        cursor = self.db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        # print('++', query)
        data = ""
        for row in records:
            # print('ÄÄ', row)
            data += "INSERT INTO `" + str(self.tableName) + "` VALUES("
            first = True
            for field in row:
                if not first:
                    data += ', '
                data += '"' + str(field) + '"'
                first = False

            data += ");\n"
        data += "\n\n"

        values = []
        # for i in data:
        #     print(i)
        cursor.close()
        #     # values.append(i[0])
        # # return values
        # filename = str(os.getenv("HOME")) + "/backup_" + now.strftime("%Y-%m-%d_%H:%M") + ".sql"
        filename = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\bb.sql"
        # data = records[1]
        FILE = open(filename, "w")
        FILE.writelines(data)
        FILE.close()

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
                    raise RuntimeError('Column {} missing in sql table'.format(sql_file_col))
        f.close()
        if not same:
            return diffrences

if __name__ == '__main__':

    # iniFile = r"D:\Python\MySQL\database.ini"
    # iniFile = r"D:\Python\MySQL\web_db.ini"
    # iniFile = r"D:\Python\MySQL\mysqlquerys\src\mysqlquerys\local.ini"
    # iniFile = r"C:\_Development\Diverse\pypi\cfgmRN.ini"
    iniFile = r"C:\_Development\Diverse\pypi\cfgm.ini"

    conf = connect.Config(iniFile)
    # print(conf.credentials)

    db = DataBase(conf.credentials)
    print(db.is_connected)
    # tables = ['users', 'all_cars', 'hyundai_ioniq', 'bmw_318i']
    # sql = r'C:\_Development\Diverse\pypi\radu\masina\src\masina\ee.sql'
    # tables_dict = {'users': 'id',
    #       'all_cars': 'user_id',
    #       'hyundai_ioniq': 'id_users',
    #       'bmw_318i': 'id_users',
    #       }
    # print(db.backup_profile_with_id(tables_dict, sql, user_id=1))
    # print(table.returnAllRecordsFromTable())
    testrrrr = Table(conf.credentials, 'users')
    # print(testrrrr.children_tables)
    # print(testrrrr.columnsDetProperties)
    sql_file = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\static\sql\users_template.sql"
    testrrrr.compare_sql_file_to_sql_table(sql_file)

