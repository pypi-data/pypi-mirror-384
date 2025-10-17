import decimal
import os.path
import traceback
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import *
import numpy as np
from datetime import datetime, timedelta
import datetime as dt
from dateutil.relativedelta import *
import sys
import os
from mysqlquerys import connect
from mysqlquerys import mysql_rm
np.set_printoptions(linewidth=250)
__version__ = 'V1'


class CheltPlanificate:
    def __init__(self, ini_file):
        # self.dataBase = connect.DataBase(db_type, data_base_name)
        self.ini_file = ini_file
        self.conf = connect.Config(self.ini_file)
        self.dataBase = self.sql_rm.DataBase(self.conf.credentials)
        # print(50*'Ö')
        # print(self.dataBase.allAvailableDatabases)
        # print(50*'Ö')

    @property
    def sql_rm(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if self.conf.db_type == 'mysql':
            sql_rm = mysql_rm
        return sql_rm

    def get_all_sql_vals(self, tableHead):
        # print(sys._getframe().f_code.co_name, tableHead)
        table_documente = mysql_rm.Table(self.conf.credentials, 'documente')
        all_docs_databases = table_documente.returnColumn('Name')
        all_chelt = []
        for db in all_docs_databases:
            print('ÄÄ', db, self.conf.credentials)
            new_conf = self.conf.credentials
            new_conf['database'] = db
            if db in self.dataBase.allAvailableDatabases:
                database = self.sql_rm.DataBase(new_conf)
                print('**', database.allAvailableTablesInDatabase)
        # sys.exit()



                # for table in self.dataBase.tables:
                # for table in self.dataBase.allAvailableTablesInDatabase:
                for table in database.allAvailableTablesInDatabase:
                    # self.dataBase.active_table = table
                    print('table', table)
                    # active_table = mysql_rm.Table(self.conf.credentials, table)
                    active_table = mysql_rm.Table(new_conf, table)
                    check = all(item in list(active_table.columnsProperties.keys()) for item in tableHead)
                    if check:
                        vals = active_table.returnColumns(tableHead)
                        for row in vals:
                            row = list(row)
                            row.insert(0, table)
                            all_chelt.append(row)

                newTableHead = ['table']
                for col in tableHead:
                    newTableHead.append(col)

        return newTableHead, all_chelt

    def excludeNone(self, tableHead, table):
        if None in table[:, tableHead.index('valid_to')]:
            newTable = table[table[:, tableHead.index('valid_to')] != np.array(None)]
        return tableHead, newTable

    def get_days_to_expire(self, tableHead, table):
        print(sys._getframe().f_code.co_name, tableHead)

        newTableHead = []
        for col in tableHead:
            newTableHead.append(col)
        newTableHead.append('days2Expire')

        newCol = np.empty((table.shape[0], 1), dtype=object)
        newCol.fill('')
        table = np.append(table, newCol, 1)
        for row in table:
            expDate = row[tableHead.index('valid_to')]
            today = dt.date.today()
            if expDate is not None:
                time2exp = (expDate - today).days
                row[-1] = time2exp
        return newTableHead, table

    def hideExpired(self, tableHead, table):
        print(sys._getframe().f_code.co_name, tableHead)
        newTable = table[table[:, tableHead.index('days2Expire')] > 0]
        return tableHead, newTable

    def relevantOnly(self, tableHead, table, days):
        print(sys._getframe().f_code.co_name, tableHead)
        colIndx = tableHead.index('path')
        indxPath = [x for x, item in enumerate(table[:, colIndx]) if (item == '' or item is None)]
        colIndx = tableHead.index('days2Expire')
        indxExp = [x for x, item in enumerate(table[:, colIndx]) if item != '' and 0<item<days]
        indx = [*indxPath, *indxExp]
        indx = list(set(indx))
        newTable = table[indx]
        return tableHead, newTable


class MyApp(QMainWindow):
    def __init__(self):
        super(MyApp, self).__init__()
        path2src, pyFileName = os.path.split(__file__)
        uiFileName = 'check_expiration.ui'
        path2GUI = os.path.join(path2src, 'GUI', uiFileName)
        Ui_MainWindow, QtBaseClass = uic.loadUiType(path2GUI)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        title = '{}_{}'.format(pyFileName, __version__)
        self.setWindowTitle(title)
        self.expDays = int(self.ui.SB_expDays.text())

        self.ini_file = r"D:\Python\MySQL\myfolderstructure.ini"
        self.data_base_name = 'myfolderstructure'

        self.cheltPlan = CheltPlanificate(self.ini_file)
        self.tableHead = ['id', 'name', 'valid_from', 'valid_to', 'auto_ext', 'path']
        self.newRows = []
        self.pathUpdates = []

        self.ui.planTable.horizontalHeader().sectionClicked.connect(self.sortPlan)
        self.ui.planTable.horizontalHeader().sectionDoubleClicked.connect(self.setFilter)
        self.ui.PB_update.clicked.connect(self.updateSQL)
        self.ui.PB_ResetFilter.clicked.connect(self.reset_Filter)
        self.prepareTablePlan()

        self.ui.CB_hideExpired.stateChanged.connect(self.prepareTablePlan)
        self.ui.CB_relOnly.stateChanged.connect(self.prepareTablePlan)
        self.ui.CB_excludeNone.stateChanged.connect(self.prepareTablePlan)
        self.ui.planTable.cellDoubleClicked.connect(self.updatePath)
        self.ui.planTable.cellChanged.connect(self.onCellChanged)

    def prepareTablePlan(self):
        print(sys._getframe().f_code.co_name)
        tableHead, table = self.cheltPlan.get_all_sql_vals(self.tableHead)
        table = np.atleast_2d(table)
        if self.ui.CB_excludeNone.isChecked():
            tableHead, table = self.cheltPlan.excludeNone(tableHead, table)
        tableHead, table = self.cheltPlan.get_days_to_expire(tableHead, table)
        if self.ui.CB_hideExpired.isChecked():
            tableHead, table = self.cheltPlan.excludeNone(tableHead, table)
            tableHead, table = self.cheltPlan.hideExpired(tableHead, table)
        elif self.ui.CB_relOnly.isChecked():
            tableHead, table = self.cheltPlan.relevantOnly(tableHead, table, self.expDays)

        self.populateExpensesPlan(tableHead, table)
        self.colorCells(tableHead)

    def populateExpensesPlan(self, tableHead, table):
        print(sys._getframe().f_code.co_name)
        self.ui.planTable.clear()
        self.ui.planTable.setColumnCount(len(tableHead))
        self.ui.planTable.setHorizontalHeaderLabels(tableHead)
        self.ui.planTable.setRowCount(table.shape[0])
        txt = 'No. of rows: {}'.format(table.shape[0])
        self.ui.label.setText(txt)
        for row in range(table.shape[0]):
            for col in range(table.shape[1]):
                if isinstance(table[row, col], int) or isinstance(table[row, col], float):
                    item = QTableWidgetItem()
                    item.setData(QtCore.Qt.DisplayRole, table[row, col])
                    self.ui.planTable.setItem(row, col, item)
                elif tableHead[col] == 'path' and str(table[row, col]) != '':
                    pth = table[row, col]
                    # print(20*'-', pth)
                    if pth:
                        pth = pth.strip('"')
                        if os.path.exists(pth):
                            url = bytearray(QUrl.fromLocalFile(pth).toEncoded()).decode()
                            print(20*'U', url)
                            print(20*'P', pth)
                            item = QLabel()
                            text = "<a href={}>{}</a>".format(url, pth)
                            item.setText(text)
                            item.setOpenExternalLinks(True)
                            self.ui.planTable.setCellWidget(row, col, item)
                        else:
                            item = QTableWidgetItem(str(table[row, col]))
                            self.ui.planTable.setItem(row, col, item)
                    else:
                        item = QTableWidgetItem(str(table[row, col]))
                        self.ui.planTable.setItem(row, col, item)
                elif tableHead[col] == 'path' and str(table[row, col]) == '':
                    item = QTableWidgetItem(str(table[row, col]))
                    self.ui.planTable.setItem(row, col, item)
                else:
                    item = QTableWidgetItem(str(table[row, col]))
                    self.ui.planTable.setItem(row, col, item)

    def updateSQL(self):
        # self.readTable()
        self.newRows = np.atleast_2d(self.newRows)
        self.newRows = np.unique(self.newRows, axis=0)
        print(self.newRows)
        print(self.newRows.shape)

        if self.newRows.shape[1] > 0:
            for row in self.newRows:
                tableName, id = row
                table = connect.Table(self.ini_file, self.data_base_name, tableName)
                matches = ('id', id)
                row = table.returnRowsWhere(matches)[0]

                cols = []
                vals = []
                for i, col in enumerate(table.columnsNames):
                    if col == 'id' or col == 'path':
                        continue
                    cols.append(col)
                    vals.append(row[i])

                newRowId = table.add_row(cols, vals)
                valid_to = row[table.columnsNames.index('valid_to')]
                freq = row[table.columnsNames.index('freq')]
                newValid_to = valid_to + relativedelta(months=freq)
                newValid_from = valid_to + relativedelta(days=1)
                table.changeCellContent('valid_to', newValid_to, 'id', newRowId)
                table.changeCellContent('valid_from', newValid_from, 'id', newRowId)
                table.changeCellContent('auto_ext', 1, 'id', newRowId)
                table.changeCellContent('auto_ext', 0, 'id', id)
        for row in self.pathUpdates:
            tableName, id, path = row
            table = connect.Table(self.ini_file, self.data_base_name, tableName)
            # matches = ('id', id)
            # row = table.returnRowsWhere(matches)[0]
            # newRowId = table.add_row(table.columnsNames[1:], row[1:])
            # valid_to = row[table.columnsNames.index('valid_to')]
            # freq = row[table.columnsNames.index('freq')]
            # newValid_to = valid_to + relativedelta(months=freq)
            # newValid_from = valid_to + relativedelta(days=1)
            # table.changeCellContent('valid_to', newValid_to, 'id', newRowId)
            # table.changeCellContent('valid_from', newValid_from, 'id', newRowId)
            table.changeCellContent('path', path, 'id', id)
        self.prepareTablePlan()

    def readTable(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        rows = self.ui.planTable.rowCount()
        cols = self.ui.planTable.columnCount()
        tableHead = []
        tableData = np.empty((rows, cols), dtype=object)
        for column in range(cols):
            colName = self.ui.planTable.horizontalHeaderItem(column).text()
            tableHead.append(colName)
            for row in range(rows):
                cell = self.ui.planTable.item(row, column)
                if colName == 'path':
                    print('+++++', colName, type(cell))
                    widget = self.ui.planTable.cellWidget(row, column)
                    print('----', widget)
                    if widget is not None:
                        pth = widget.text()
                        print('&&&&&', pth)
                        print('&&&&&', type(pth))
                        newPTH = os.path.abspath(os.path.expanduser(pth))
                        newPTH = newPTH.strip()
                        print('gggggg', newPTH)

                if cell is None:
                    tableData[row, column] = None
                else:
                    tableData[row, column] = cell.text()
                    # if colName == 'path':
                    #     print('+++++', colName, type(cell))
                    #     widget = self.ui.planTable.cellWidget(row, column)
                    #     if widget:
                    #         print('BINGO')
                    #         print(widget.text())

        return tableHead, tableData

    def colorCells(self, tableHead):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        rows = self.ui.planTable.rowCount()
        cols = self.ui.planTable.columnCount()
        if 'newRow' not in tableHead:
            tableHead.append('newRow')
            self.ui.planTable.insertColumn(cols)
        cols = self.ui.planTable.columnCount()
        self.ui.planTable.setHorizontalHeaderLabels(tableHead)
        for row in range(rows):
            for column in range(cols):
                cell = self.ui.planTable.item(row, column)
                headerName = self.ui.planTable.horizontalHeaderItem(column).text()
                if headerName == 'days2Expire':
                    if cell.text():
                        days2Expire = int(cell.text())
                        if self.expDays > days2Expire > 0:
                            self.ui.planTable.item(row, column).setBackground(QtGui.QColor('red'))
                elif headerName == 'path':
                    widget = self.ui.planTable.cellWidget(row, column)
                    if widget is None:
                        self.ui.planTable.item(row, column).setBackground(QtGui.QColor('red'))
                elif headerName == 'newRow':
                    cell = QTableWidgetItem()
                    cell.setFlags(QtCore.Qt.ItemIsUserCheckable |QtCore.Qt.ItemIsEnabled)
                    cell.setCheckState(QtCore.Qt.Unchecked)
                    # cell.stateChanged.connect(self.clickBoxStateChanged(col))
                    self.ui.planTable.setItem(row, column, cell)

    def onCellChanged(self, row, column):
        item = self.ui.planTable.item(row, column)
        if item.checkState() == 2:
        # if self.ui.planTable.cellWidget(row, column).isChecked():
            cellTable = self.ui.planTable.item(row, 0)
            cellID = self.ui.planTable.item(row, 1)
            tup = (cellTable.text(), cellID.text())
            self.newRows.append(tup)

    def updatePath(self, row, col):
        print(sys._getframe().f_code.co_name)
        headerName = self.ui.planTable.horizontalHeaderItem(col).text()
        if headerName == 'path':
            inpFile, _ = QFileDialog.getOpenFileName(None, 'Select file', '', '')
            if inpFile:
                if os.path.exists(inpFile):
                    item = QTableWidgetItem(str(inpFile))
                    self.ui.planTable.setItem(row, col, item)
                    self.ui.planTable.item(row, col).setBackground(QtGui.QColor('green'))
                    cols = self.ui.planTable.columnCount()
                    for col in range(cols):
                        headerName = self.ui.planTable.horizontalHeaderItem(col).text()
                        if headerName == 'table':
                            table = self.ui.planTable.item(row, col).text()
                        elif headerName == 'id':
                            id = self.ui.planTable.item(row, col).text()
                    tup = (table, id, inpFile)
                    self.pathUpdates.append(tup)

    def sortPlan(self, logical_index):
        print(sys._getframe().f_code.co_name)
        header = self.ui.planTable.horizontalHeader()
        order = Qt.DescendingOrder
        if not header.isSortIndicatorShown():
            header.setSortIndicatorShown(True)
        elif header.sortIndicatorSection() == logical_index:
            order = header.sortIndicatorOrder()
        header.setSortIndicator(logical_index, order)
        self.ui.planTable.sortItems(logical_index, order)

    def setFilter(self, logical_index):
        print(sys._getframe().f_code.co_name)
        # colName = self.ui.planTable.columnsNames[logical_index]
        colName = self.ui.planTable.horizontalHeaderItem(logical_index).text()
        header = self.ui.planTable.horizontalHeader()

        geom = QtCore.QRect(header.sectionViewportPosition(logical_index), 0, header.sectionSize(logical_index),
                            header.height())
        item = QLineEdit(header)
        item.setGeometry(geom)
        item.show()
        item.setFocus()
        item.editingFinished.connect(lambda: (self.applyFilter(colName, item.text()),
                                              item.clear(),
                                              item.hide(),
                                              item.deleteLater()))

    def applyFilter(self, colName, filter):
        print(sys._getframe().f_code.co_name)
        if filter == '':
            return

        tableHead, tableData = self.readTable()

        filterText = self.ui.lineEditFilterList.text()
        if not filterText:
            if isinstance(filter, str):
                filterText += '{}="{}"'.format(colName, filter)
            elif isinstance(filter, tuple):
                filterText += '{} < {} < {}'.format(filter[0], colName, filter[1])
            elif isinstance(filter, list):
                filterText += '{} in {}"'.format(str(filter), colName)
        else:
            if isinstance(filter, str):
                filterText += '; {}="{}"'.format(colName, filter)
            elif isinstance(filter, tuple):
                filterText += '; {} < {} < {}'.format(filter[0], colName, filter[1])
            elif isinstance(filter, list):
                filterText += '; {} in {}"'.format(str(filter), colName)

        self.ui.lineEditFilterList.setText(filterText)

        newTableData = tableData[np.where(tableData[:, tableHead.index(colName)] == filter)]
        self.populateExpensesPlan(tableHead, newTableData)
        self.colorCells(tableHead)

    def reset_Filter(self):
        self.ui.lineEditFilterList.setText('')
        self.prepareTablePlan()


class FilterWindow(QDialog):
    def __init__(self, colType, colName):
        super(FilterWindow, self).__init__()
        path2src, pyFileName = os.path.split(__file__)
        uiFileName = 'filterWindow.ui'
        path2GUI = os.path.join(path2src, 'GUI', uiFileName)
        Ui_MainWindow, QtBaseClass = uic.loadUiType(path2GUI)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.colName = colName
        self.ui.GB_DateInterval.setVisible(False)
        self.ui.GB_IntInterval.setVisible(False)
        self.ui.checkBoxDateInterval.stateChanged.connect(self.openDateInterval)
        self.ui.checkBoxIntInterval.stateChanged.connect(self.openIntInterval)

        self.rejected.connect(self.byebye)

        if colType == 'int':
            self.ui.GB_IntInterval.setVisible(True)
            self.ui.lineEdit_max.setEnabled(False)
        if colType == 'date':
            self.ui.GB_DateInterval.setVisible(True)
            self.ui.dateEditTo.setEnabled(False)

    def openIntInterval(self):
        if self.ui.checkBoxIntInterval.isChecked():
            self.ui.lineEdit_max.setEnabled(True)
            self.ui.label_int.setText('< {} <'.format(self.colName))
        else:
            self.ui.lineEdit_max.setEnabled(False)
            self.ui.label_int.setText('= {}'.format(self.colName))

    def openDateInterval(self):
        if self.ui.checkBoxDateInterval.isChecked():
            self.ui.dateEditTo.setEnabled(True)
            self.ui.label_date.setText('< {} <'.format(self.colName))
        else:
            self.ui.dateEditTo.setEnabled(False)
            self.ui.label_date.setText('= {}'.format(self.colName))

    def byebye(self):
        self.close()

    def intInterval(self):
        if self.ui.checkBoxIntInterval.isChecked():
            tup = (self.ui.lineEdit_min.text(), self.ui.lineEdit_max.text())
            return tup
        else:
            return self.ui.lineEdit_min.text()

    def dateInterval(self):
        if self.ui.checkBoxDateInterval.isChecked():
            tup = (self.ui.dateEditFrom.date(), self.ui.dateEditTo.date())
            return tup
        else:
            return self.ui.dateEditFrom.date()

    @staticmethod
    def getIntInterval(colName):
        dialog = FilterWindow('int', colName)
        result = dialog.exec_()
        filt = dialog.intInterval()
        if result == QDialog.Accepted:
            return filt
        else:
            return None

    @staticmethod
    def getDateInterval(colName):
        dialog = FilterWindow('date', colName)
        result = dialog.exec_()
        filt = dialog.dateInterval()
        if result == QDialog.Accepted:
            return filt
        else:
            return None


class InsertNewRow(QDialog):
    def __init__(self, cols):
        super(InsertNewRow, self).__init__()
        self.cols = cols
        path2src, pyFileName = os.path.split(__file__)
        uiFileName = 'addNewRow.ui'
        path2GUI = os.path.join(path2src, 'GUI', uiFileName)
        Ui_MainWindow, QtBaseClass = uic.loadUiType(path2GUI)
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)
        self.fillInTable()

    def fillInTable(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.gui.tableWidget.setRowCount(len(self.cols))
        for row, colName in enumerate(self.cols):
            cell = QLineEdit()
            cell.setText(str(colName))
            cell.setEnabled(False)
            self.gui.tableWidget.setCellWidget(row, 0, cell)

            colType, null, key, default, extra = self.cols[colName][:5]
            cell = QLineEdit()
            cell.setText(str(colType))
            cell.setEnabled(False)
            self.gui.tableWidget.setCellWidget(row, 1, cell)
            # self.gui.tableWidget.setItem(row, 1, QTableWidgetItem(colType))
            cell = QLineEdit()
            cell.setText(str(null))
            cell.setEnabled(False)
            self.gui.tableWidget.setCellWidget(row, 2, cell)
            # self.gui.tableWidget.setItem(row, 2, QTableWidgetItem(null))
            cell = QLineEdit()
            cell.setText(str(key))
            cell.setEnabled(False)
            self.gui.tableWidget.setCellWidget(row, 3, cell)
            # self.gui.tableWidget.setItem(row, 3, QTableWidgetItem(key))
            cell = QLineEdit()
            cell.setText(str(default))
            cell.setEnabled(False)
            self.gui.tableWidget.setCellWidget(row, 4, cell)
            # self.gui.tableWidget.setItem(row, 4, QTableWidgetItem(default))

            cellAutoIncr = QTableWidgetItem()
            cellAutoIncr.setFlags(QtCore.Qt.ItemIsEnabled)#QtCore.Qt.ItemIsUserCheckable |

            if 'auto_increment' in extra:
                autoIncremVal = self.cols[colName][-1]
                cell = QLineEdit()
                cell.setText(str(autoIncremVal))
                cell.setEnabled(False)
                cellAutoIncr.setCheckState(QtCore.Qt.Checked)
                self.gui.tableWidget.setCellWidget(row, 6, cell)
            else:
                cellAutoIncr.setCheckState(QtCore.Qt.Unchecked)
                self.gui.tableWidget.setItem(row, 6, QTableWidgetItem(extra))
            self.gui.tableWidget.setItem(row, 5, cellAutoIncr)

            if 'timestamp' in colType:
                cell = QDateEdit()
                cell.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
                cell.setDateTime(QDateTime(datetime.now().year,
                                           datetime.now().month,
                                           datetime.now().day,
                                           datetime.now().hour,
                                           datetime.now().minute,
                                           datetime.now().second))
                cell.setEnabled(False)
                self.gui.tableWidget.setCellWidget(row, 6, cell)

            if 'date' in colType:
                cell = QDateEdit()
                cell.setDisplayFormat('yyyy-MM-dd')
                cell.setDate(QDate(datetime.now().year,
                                           datetime.now().month,
                                           datetime.now().day))
                # cell.setEnabled(False)
                self.gui.tableWidget.setCellWidget(row, 6, cell)
            elif ('smallint' in colType or 'tinyint' in colType) and 'active' in colName:
                cell = QTableWidgetItem()
                cell.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                cell.setCheckState(QtCore.Qt.Checked)
                self.gui.tableWidget.setCellWidget(row, 6, cell)

    def readTable(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        rows = self.gui.tableWidget.rowCount()
        cols = self.gui.tableWidget.columnCount()

        columns = []
        values = []

        for row in range(rows):
            for column in range(cols):
                cell = self.gui.tableWidget.item(row, column)
                headerName = self.gui.tableWidget.horizontalHeaderItem(column).text()
                if headerName == 'ColName':
                    # colName = cell.text()
                    widget = self.gui.tableWidget.cellWidget(row, column)
                    colName = widget.text()
                if headerName == 'Value':
                    widget = self.gui.tableWidget.cellWidget(row, column)
                    if cell is not None:
                        if cell.text():
                            colValue = cell.text()
                            print(colValue)
                        elif cell.checkState() == QtCore.Qt.Checked:
                            colValue = 1
                        elif cell.checkState() == QtCore.Qt.Unchecked:
                            colValue = 0
                        columns.append(colName)
                        values.append(colValue)
                    elif widget:
                        if isinstance(widget, QDateTimeEdit):
                            colValue = widget.dateTime()
                            colValue = colValue.toPyDateTime()
                            columns.append(colName)
                            values.append(str(colValue))
        return tuple(columns), tuple(values)

    @staticmethod
    def getNewRowValues(cols):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        dialog = InsertNewRow(cols)
        result = dialog.exec_()
        cols, values = dialog.readTable()
        if result == QDialog.Accepted:
            return cols, values
        else:
            return None


def main():
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
