import os, sys
import pathlib
from mysqlquerys import connect, mysql_rm


#self.tableHead = ['id', 'name', 'valid_from', 'valid_to', 'auto_ext', 'path']

class SQLTable:
    def __init__(self, ini_file):
        self.ini_file = ini_file
        self.conf = connect.Config(self.ini_file)
        self.dataBase = self.sql_rm.DataBase(self.conf.credentials)
        self.documents_table = mysql_rm.Table(self.conf.credentials, 'documente')
        # self.tableHead = ['id', 'name', 'valid_from', 'valid_to', 'auto_ext', 'path']
        self.standard = ['id', 'doc_id', 'record_time', 'name', 'valid_from', 'valid_to', 'auto_ext', 'file_doc', 'file_type', 'path']

    @property
    def sql_rm(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if self.conf.db_type == 'mysql':
            sql_rm = mysql_rm
        return sql_rm

    @property
    def tracked_databases(self):
        databases = self.documents_table.returnColumn('name')
        all_databases = self.dataBase.allAvailableDatabases
        tracked = list(set(databases) & set(all_databases))
        return tracked

    @property
    def databases_path(self):
        databases_path = {}
        for db in self.tracked_databases:
            pth = self.documents_table.returnCellsWhere('path', matches=[('name', db)])
            if pth:
                # print('**', pth)
                databases_path[db] = pth[0]
        return databases_path

    @property
    def databases_ids(self):
        databases_ids = {}
        for db in self.tracked_databases:
            pth = self.documents_table.returnCellsWhere('id', matches=[('name', db)])
            if pth:
                databases_ids[db] = pth[0]
        return databases_ids

    def upload_new_files_to_db(self, db_name):
        new_credentials = self.conf.credentials
        new_credentials['database'] = db_name
        dataBase = self.sql_rm.DataBase(new_credentials)
        for table in dataBase.allAvailableTablesInDatabase:
            self.upload_new_files_to_table(dataBase, table)

    def upload_new_files_to_table(self, database, sql_table):
        if isinstance(database, mysql_rm.DataBase):
            database_name = database.db_name
            pth = pathlib.Path(self.databases_path[database_name])
            pth_2_table = pth / sql_table
        elif isinstance(database, str):
            database_name = database
            pth = pathlib.Path(self.databases_path[database_name])
            pth_2_table = pth / sql_table

        if os.path.exists(pth_2_table):
            print('___BINGO', pth_2_table, self.get_max_dir_depth(pth_2_table))
            new_credentials = self.conf.credentials
            new_credentials['database'] = database_name
            sql = mysql_rm.Table(new_credentials, sql_table)
            # print(sql.columnsNames)
            # print(set(sql.columnsNames) ^ set(self.standard))
            dir_cols = [x for x in sql.columnsNames if x not in self.standard]
            print(dir_cols)
            for path in sorted(pth_2_table.rglob("*")):
                if path.is_file():
                    print('***********', path)
                    if path.suffix == '.rar':
                        continue
                    # pp = str(path)
                    # already_in_sql = sql.returnCellsWhere('id', [('pth', str(pp))])
                    already_in_sql = sql.returnCellsWhere('path', [('name', path.stem)])
                    # already_in_sql = sql.returnColumn('path')
                    if already_in_sql:
                        # print('already_in_sql', already_in_sql, type(already_in_sql))
                        for i in already_in_sql:
                            print('already_in_sql', i, type(i))
                    else:
                        # print('nu e in db')
                        cols = ['name', 'file_doc', 'file_type', 'path']
                        name = path.stem
                        file_doc = path
                        # print('path', type(path))
                        file_type = path.suffix
                        path_str = str(path)
                        vals = [name, file_doc, file_type, path_str]

                        # depth = len(path.parent.relative_to(pth_2_table).parts)
                        # print(path)
                        # print(path)
                        # print(path.parent.relative_to(pth_2_table).parts, depth)
                        for i, fold in enumerate(path.parent.relative_to(pth_2_table).parts):
                            # print(i, fold, dir_cols[i])
                            col = dir_cols[i]
                            cols.append(col)
                            vals.append(fold)
                        # print(cols, len(cols))
                        # print(vals, len(vals))
                        sql.addNewRowWithFile(cols, tuple(vals))
                        # sys.exit()

    def get_max_dir_depth(self, directory):
        depth = 0
        for path in sorted(directory.rglob("*")):
            if path.is_dir():
                # print(path.relative_to(directory).parts, len(path.relative_to(directory).parts))
                newdepth = len(path.relative_to(directory).parts)
                depth = max(depth, newdepth)
        return depth


def display_dir_tree(directory):
    print(f"+ {directory}")
    for path in sorted(directory.rglob("*")):
        depth = len(path.relative_to(directory).parts)
        spacer = "    " * depth
        print(f"{spacer}+ {path.name}")


def main():
    src_dir = r'D:\Documente\Radu\Versicherungen\Haftpflicht'
    src_dir = pathlib.Path(src_dir)
    # display_dir_tree(src_dir)
    # print(get_max_dir_depth(src_dir))
    ini_file = r"D:\Python\MySQL\myfolderstructure.ini"
    data_base_name = 'myfolderstructure'
    sql_db = SQLTable(ini_file)
    print(sql_db.tracked_databases)
    print(sql_db.databases_path)
    sql_db.upload_new_files_to_db(sql_db.tracked_databases[0])



if __name__ == '__main__':
    main()
