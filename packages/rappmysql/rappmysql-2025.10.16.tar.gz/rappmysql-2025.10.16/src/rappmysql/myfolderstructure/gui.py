import decimal
import sys
import csv
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui
from PyQt5 import QtCore
from PyQt5.QtCore import *
import numpy as np
from datetime import datetime
import os
from mysqlquerys import connect


class MyApp(QMainWindow):
    def __init__(self):
        super(MyApp, self).__init__()
        path2src, pyFileName = os.path.split(__file__)
        uiFileName = 'gui.ui'
        path2GUI = os.path.join(path2src, 'GUI', uiFileName)
        Ui_MainWindow, QtBaseClass = uic.loadUiType(path2GUI)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        ini_file = r"D:\Python\MySQL\database.ini"
        self.db = connect.DbConnection(ini_file)

        self.ui.GB_tablesList.setVisible(False)
        self.ui.tableTab.setVisible(False)
        self.populate_listWidgetDataBases()
        self.ui.listWidgetDataBases.itemDoubleClicked.connect(self.setActiveDataBase)
        self.ui.listWidgetTables.itemDoubleClicked.connect(self.setActiveTable)
        self.ui.PBDefaultFilter.clicked.connect(self.populateTableWidget)
        self.ui.pbImportCSV.clicked.connect(self.importCSV)
        self.ui.pbExportCSV.clicked.connect(self.exportCSV)

        self.ui.tableWidget.horizontalHeader().sectionClicked.connect(self.sort)
        self.ui.tableWidget.horizontalHeader().sectionDoubleClicked.connect(self.setFilter)

        self.ui.pbEditTable.clicked.connect(self.editTable)
        self.ui.PBEditTableColsProps.clicked.connect(self.editTableColsProps)
        self.ui.PBSaveTableColsProps.clicked.connect(self.saveEditedValuesColsProps)

        self.ui.pushButtonCreateTable.clicked.connect(self.createTable)
        self.ui.pbCreateDB.clicked.connect(self.createDataBase)
        self.ui.pbAddRow.clicked.connect(self.addRow)
        self.ui.pbSave.clicked.connect(self.saveEditedValues)
        self.ui.listWidgetDataBases.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.listWidgetDataBases.customContextMenuRequested.connect(self.contextListDataBases)

        self.ui.listWidgetTables.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.listWidgetTables.customContextMenuRequested.connect(self.contextListTables)
        self.ui.tableTab.currentChanged.connect(self.showColsProps)

        vHeader = self.ui.tableWidget.verticalHeader()
        vHeader.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        vHeader.customContextMenuRequested.connect(self.contextVHeader)

        vHeader = self.ui.tableColsProps.verticalHeader()
        vHeader.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        vHeader.customContextMenuRequested.connect(self.contextVHeaderTableColsProps)
        self.editModeTableColsProps = False

    def contextVHeaderTableColsProps(self, event):
        print(sys._getframe().f_code.co_name)
        if self.editModeTableColsProps:
            item = self.ui.tableColsProps.itemAt(event)
            contextMenu = QMenu(self)
            if item is not None:
                contextMenu.addAction('Insert Column(s)')
                contextMenu.addAction('Delete Column(s)')
                #
                # print(selectedRowsIndexes)
            elif item is None:
                contextMenu.addAction('AddColumn(s)')

            action = contextMenu.exec_(self.ui.tableColsProps.mapToGlobal(event))
            if action is not None:
                if action.text() == 'Insert Column(s)':
                    selectedRowsIndexes = self.ui.tableColsProps.selectionModel().selectedRows()
                    newCols = CreateTable.createColumnQuery(self.activeTable.table_name)
                    indxs = []
                    for indx in selectedRowsIndexes:
                        indxs.append(indx.row())
                    position2Insert = min(indxs)
                    for newCol in newCols:
                        name, type, lengthVal = newCol
                        self.activeTable.addColumn(name, type, lengthVal, position2Insert)
                        position2Insert += 1
                elif action.text() == 'AddColumn(s)':
                    newCols = CreateTable.createColumnQuery(self.activeTable.table_name)
                    if newCols:
                        for newCol in newCols:
                            name, typeCol, lengthVal = newCol
                            self.activeTable.addColumn(name, typeCol, lengthVal, None)
                elif action.text() == 'Delete Column(s)':
                    selectedColumnsIndexes = self.ui.tableColsProps.selectionModel().selectedRows()
                    cols2Del = []
                    for indx in selectedColumnsIndexes:
                        cols2Del.append(self.activeTable.columnsNames[indx.row()])

                    for col in cols2Del:
                        self.activeTable.dropColumn(col)
                self.showColsProps()

    def editTableColsProps(self):
        print(sys._getframe().f_code.co_name)
        self.editModeTableColsProps = True
        self.ui.tableColsProps.setEditTriggers(QTableWidget.AllEditTriggers)
        self.ui.tableColsProps.cellChanged.connect(self.bufferChangesColsProps)
        # self.ui.tableColsProps.currentCellChanged.connect(self.bufferChangesColsProps)

    def bufferChangesColsProps(self, row, column):
        print(sys._getframe().f_code.co_name)
        if self.editModeTableColsProps:
            cell = self.ui.tableColsProps.item(row, column)
            if cell:
                val2Moify = cell.text()
            prop2Modify = self.ui.tableColsProps.horizontalHeaderItem(column).text()
            if prop2Modify == 'ColName':
                oldColName = self.activeTable.columnsNames[row]
                tup = ('renameColumn', oldColName, val2Moify)
                self.colsPropsEditArr.append(tup)
            elif prop2Modify == 'Type':
                colName = self.activeTable.columnsNames[row]
                tup = ('modifyColType', colName, val2Moify)
                self.colsPropsEditArr.append(tup)
            elif prop2Modify == 'Null':
                colName = self.activeTable.columnsNames[row]
                colTypee = self.ui.tableColsProps.item(row, 1).text()
                colVals = self.activeTable.returnColumn(colName)
                cell = self.ui.tableColsProps.item(row, column)
                if cell.checkState() == QtCore.Qt.Checked:
                    null = True
                elif cell.checkState() == QtCore.Qt.Unchecked:
                    null = False
                    if None in colVals:
                        message = 'Column has empty cells already'
                        QMessageBox.warning(self, 'Missing Data', message, QMessageBox.Ok)
                        cell.setCheckState(QtCore.Qt.Checked)
                        return
                tup = ('modifyColNullConstrain', colName, colTypee, null)
                self.colsPropsEditArr.append(tup)
            elif prop2Modify == 'Key':
                colName = self.activeTable.columnsNames[row]
                widget = self.ui.tableColsProps.cellWidget(row, column)
                keyType = widget.currentText()
                if keyType == 'NONE':
                    key = None
                    refTable = None
                    refColumn = None
                elif keyType == 'PRI':
                    key = 'PRI'
                    refTable = None
                    refColumn = None
                elif keyType == 'FOREIGN':
                    key = 'FOREIGN'
                    refTable, okPress = QInputDialog.getItem(self, 'Select Reference Table', 'Table',
                                                             self.activeDataBase.tables, 0, False)
                    rtab = connect.Table(self.db.data_base_type, self.activeDataBase.data_base_name, refTable)
                    refColumn, okPress = QInputDialog.getItem(self, 'Select Reference Table', 'Table',
                                                              rtab.columnsNames, 0, False)
                tup = ('modifyColKey', colName, key, refTable, refColumn)
                self.colsPropsEditArr.append(tup)
            elif prop2Modify == 'Default':
                colName = self.activeTable.columnsNames[row]
                colTypee = self.ui.tableColsProps.item(row, 1).text()
                tup = ('colDefaultVal', colName, colTypee, val2Moify)
                self.colsPropsEditArr.append(tup)
            elif prop2Modify == 'AutoIncrement':
                colName = self.activeTable.columnsNames[row]
                colTypee = self.ui.tableColsProps.item(row, 1).text()
                cell = self.ui.tableColsProps.item(row, column)
                if cell.checkState() == QtCore.Qt.Checked:
                    autoIncrement = True
                elif cell.checkState() == QtCore.Qt.Unchecked:
                    autoIncrement = False
                tup = ('modify2AutoIncrement', colName, colTypee, autoIncrement)
                self.colsPropsEditArr.append(tup)

    def saveEditedValuesColsProps(self):
        print(sys._getframe().f_code.co_name)
        for edit in self.colsPropsEditArr:
            definition, args = edit[0], edit[1:]
            getattr(self.activeTable, definition)(*args)
        self.colsPropsEditArr = []

    def bufferChanges(self, row, column):
        print(sys._getframe().f_code.co_name)
        if self.editMode:
            cell = self.ui.tableWidget.item(row, column)
            val2Moify = cell.text()
            column2Modify = self.activeTable.columnsNames[column]
            cell = self.ui.tableWidget.item(row, 0)
            refValue = cell.text()
            refColumn = self.activeTable.columnsNames[0]
            tup = (column2Modify, val2Moify, refColumn, refValue)
            self.editArr.append(tup)

    def saveEditedValues(self):
        for edit in self.editArr:
            column2Modify, val2Moify, refColumn, refValue = edit
            self.activeTable.changeCellContent(column2Modify, val2Moify, refColumn, refValue)

    def populate_listWidgetDataBases(self):
        print(sys._getframe().f_code.co_name)
        self.ui.listWidgetDataBases.clear()
        for i, db in enumerate(self.db.databases):
            self.ui.listWidgetDataBases.addItem(str(db))

    def setActiveDataBase(self, item):
        print(sys._getframe().f_code.co_name)
        self.ui.GB_tablesList.setVisible(True)
        self.db.active_data_base = item.text()
        self.activeDataBase = self.db.active_data_base
        self.populate_listWidgetTables()

    def populate_listWidgetTables(self):
        print(sys._getframe().f_code.co_name)
        self.ui.listWidgetTables.clear()
        for i, tab in enumerate(self.activeDataBase.tables):
            self.ui.listWidgetTables.addItem(str(tab))

    def setActiveTable(self, item):
        print(sys._getframe().f_code.co_name)
        self.ui.tableTab.setVisible(True)
        self.activeDataBase.active_table = item.text()
        self.activeTable = self.activeDataBase.active_table
        self.defaultFilter = True
        self.filterList = []
        self.editMode = False
        self.editArr = []
        self.colsPropsEditArr = []
        self.populateTableWidget()

    def populateTableWidget(self):
        print(sys._getframe().f_code.co_name)
        self.ui.tableTab.setTabText(0, self.activeTable.table_name)
        self.ui.tableTab.setTabText(1, 'Data Type')
        self.ui.tableTab.setCurrentIndex(0)

        self.data = np.atleast_2d(self.activeTable.data)
        if self.data.shape == (1, 0):
            self.data = np.empty((0, len(self.activeTable.columnsNames)))

        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.populateTable()

    def populateTable(self):
        print(sys._getframe().f_code.co_name)
        self.ui.tableWidget.clear()
        self.ui.tableWidget.setColumnCount(len(self.activeTable.columnsNames))
        self.ui.tableWidget.setHorizontalHeaderLabels(self.activeTable.columnsNames)
        self.ui.tableWidget.setRowCount(self.data.shape[0])
        for col in range(self.data.shape[1]):
            headerName = self.ui.tableWidget.horizontalHeaderItem(col).text()
            for row in range(self.data.shape[0]):
                if isinstance(self.data[row, col], int):
                    item = QTableWidgetItem()
                    item.setData(QtCore.Qt.DisplayRole, self.data[row, col])
                elif isinstance(self.data[row, col], decimal.Decimal):
                    val = float(self.data[row, col])
                    item = QTableWidgetItem()
                    item.setData(QtCore.Qt.DisplayRole, val)
                elif headerName == 'path':
                    path = self.data[row, col]
                    if path:
                        url = bytearray(QUrl.fromLocalFile(path).toEncoded()).decode()
                        item = QLabel()
                        text = "<a href={}>Link</a>".format(url)
                        item.setText(text)
                        item.setOpenExternalLinks(True)
                        self.ui.tableWidget.setCellWidget(row, col, item)
                        continue
                    else:
                        item = QTableWidgetItem(str(self.data[row, col]))
                else:
                    item = QTableWidgetItem(str(self.data[row, col]))
                self.ui.tableWidget.setItem(row, col, item)

    def editTable(self):
        print(sys._getframe().f_code.co_name)
        self.editMode = True
        self.ui.tableWidget.setEditTriggers(QTableWidget.AllEditTriggers)
        self.ui.tableWidget.cellChanged.connect(self.bufferChanges)

    def addRow(self):
        print(sys._getframe().f_code.co_name)
        colsProps = self.activeTable.columnsProperties
        for k, v in colsProps.items():
            colType, null, key, default, extra = v
            if 'auto_increment' in extra:
                v.append(self.activeTable.noOfRows + 1)

        res = InsertNewRow.getNewRowValues(colsProps)
        if res:
            cols, values = res
            if 0 < len(cols) == len(values) > 0:
                self.activeTable.add_row(cols, values)
        self.populateTableWidget()

    def readTable(self):
        print(sys._getframe().f_code.co_name)
        array = np.empty([self.ui.tableWidget.rowCount(), self.ui.tableWidget.columnCount()], dtype=object)
        for col in range(self.ui.tableWidget.columnCount()):
            for row in range(self.ui.tableWidget.rowCount()):
                cell = self.ui.tableWidget.item(row, col)
                if cell.text():
                    array[row, col] = cell.text()
                else:
                    array[row, col] = ''
        return array

    def contextListDataBases(self, event):
        print(sys._getframe().f_code.co_name)
        contextMenu = QMenu(self)
        item = self.ui.listWidgetDataBases.itemAt(event)
        if item is not None:
            contextMenu.addAction('Drop')
        else:
            contextMenu.addAction('new schema')

        action = contextMenu.exec_(self.ui.listWidgetDataBases.mapToGlobal(event))

        if action is not None:
            if action.text() == 'Drop':
                self.db.drop_data_base(item.text())
                self.populate_listWidgetDataBases()
            elif action.text() == 'new schema':
                self.createDataBase()

    def contextListTables(self, event):
        print(sys._getframe().f_code.co_name)
        contextMenu = QMenu(self)
        item = self.ui.listWidgetTables.itemAt(event)
        if item is not None:
            contextMenu.addAction('Drop')
            contextMenu.addAction('Rename')
            contextMenu.addAction('Delete all data')
        else:
            contextMenu.addAction('new table')

        action = contextMenu.exec_(self.ui.listWidgetTables.mapToGlobal(event))

        if action is not None:
            if action.text() == 'Drop':
                self.activeDataBase.drop_table(item.text())
                self.populate_listWidgetTables()
            elif action.text() == 'new table':
                self.createTable()
            elif action.text() == 'Delete all data':
                self.activeDataBase.deleteAllRows(item.text())
                self.populate_listWidgetTables()
            elif action.text() == 'Rename':
                text, okPressed = QInputDialog.getText(self, "Get text", "New Table Name:", QLineEdit.Normal, "")
                if okPressed and text != '':
                    self.activeDataBase.renameTable(item.text(), text)
                self.populate_listWidgetTables()

    def contextVHeader(self, event):
        print(sys._getframe().f_code.co_name)
        item = self.ui.tableWidget.itemAt(event)
        contextMenu = QMenu(self)
        if item is not None:
            contextMenu.addAction('Delete')
            selectedRowsIndexes = self.ui.tableWidget.selectionModel().selectedRows()
            ids = []
            for indx in selectedRowsIndexes:
                cell = self.ui.tableWidget.item(indx.row(), self.activeTable.columnsNames.index('id'))
                ids.append(cell.text())

        action = contextMenu.exec_(self.ui.tableColsProps.mapToGlobal(event))

        if action is not None:
            if action.text() == 'Delete':
                for row in ids:
                    condition = ('id', row)
                    self.activeTable.deleteRow(condition)
                self.populateTableWidget()

    def createDataBase(self):
        text, okPressed = QInputDialog.getText(self, 'schema name', 'schema name', QLineEdit.Normal, '')
        self.db.create_data_base(text)
        self.populate_listWidgetDataBases()

    def createTable(self):
        print(sys._getframe().f_code.co_name)
        tableName, okPressed = QInputDialog.getText(self, 'table name', 'table name', QLineEdit.Normal, '')
        if tableName == '':
            message = 'Please give a name to table'
            QMessageBox.warning(self, 'Missing Data', message, QMessageBox.Ok)
            return()
        self.activeDataBase.create_new_table(tableName)
        self.populate_listWidgetTables()

    def showColsProps(self):
        print(sys._getframe().f_code.co_name)
        self.ui.tableColsProps.setEditTriggers(QTableWidget.NoEditTriggers)
        if self.ui.tableTab.currentIndex() == 1:
            self.ui.tableColsProps.setRowCount(len(self.activeTable.columnsProperties))
            for row, colName in enumerate(self.activeTable.columnsProperties):
                self.ui.tableColsProps.setItem(row, 0, QTableWidgetItem(colName))
                colType, null, key, default, extra = self.activeTable.columnsProperties[colName]
                # print('{}_{}_{}_{}_{}_{}'.format(colName, colType, null, key, default, extra))
                # print(type(colName), type(colType), type(colName), type(null), type(key), type(default), type(extra))
                if isinstance(default, bytes):
                    default = default.decode('utf-8')
                self.ui.tableColsProps.setItem(row, 1, QTableWidgetItem(colType))

                cell = QTableWidgetItem()
                cell.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                if str(null) == 'NO':
                    cell.setCheckState(QtCore.Qt.Unchecked)
                elif str(null) == 'YES':
                    cell.setCheckState(QtCore.Qt.Checked)
                self.ui.tableColsProps.setItem(row, 2, cell)
                cell = QComboBox()
                keys = ['NONE', 'PRI', 'FOREIGN']
                cell.addItems(keys)
                if key == 'PRI':
                    cell.setCurrentText('PRI')
                else:
                    cell.setCurrentText('NONE')
                cell.currentIndexChanged.connect(lambda i, row=row: self.bufferChangesColsProps(row, 3))

                self.ui.tableColsProps.setCellWidget(row, 3, cell)
                self.ui.tableColsProps.setItem(row, 4, QTableWidgetItem(default))

                cell = QTableWidgetItem()
                cell.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                if 'auto_increment' in extra:
                    cell.setCheckState(QtCore.Qt.Checked)
                else:
                    cell.setCheckState(QtCore.Qt.Unchecked)
                self.ui.tableColsProps.setItem(row, 5, cell)

    def sort(self, logical_index):
        print(sys._getframe().f_code.co_name)
        header = self.ui.tableWidget.horizontalHeader()
        order = Qt.DescendingOrder
        if not header.isSortIndicatorShown():
            header.setSortIndicatorShown(True)
        elif header.sortIndicatorSection() == logical_index:
            order = header.sortIndicatorOrder()
        header.setSortIndicator(logical_index, order)
        self.ui.tableWidget.sortItems(logical_index, order)

    def setFilter(self, logical_index):
        print(sys._getframe().f_code.co_name)
        #toDo fa mai departe
        # print(self.activeTable.columnsNames)
        colName = self.activeTable.columnsNames[logical_index]
        header = self.ui.tableWidget.horizontalHeader()

        geom = QtCore.QRect(header.sectionViewportPosition(logical_index), 0, header.sectionSize(logical_index), header.height())
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

        if self.defaultFilter:
            self.ui.lineEditFilterList.clear()
            self.defaultFilter = False

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

        tup = (colName, filter)
        self.filterList.append(tup)
        self.data = self.activeTable.filterRows(self.filterList)
        self.data = np.atleast_2d(self.data)
        if self.data.shape == (1, 0):
            self.data = np.empty((0, len(self.activeTable.columnsNames)))

        self.populateTable()

    def importCSV(self):
        print(sys._getframe().f_code.co_name)
        inpFile, _ = QFileDialog.getOpenFileName(None, 'Select .csv file', '', 'CSV files (*.csv)')
        with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
            linereader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for i, row in enumerate(linereader):
                if i == 0:
                    tableHead = row

        for col in tableHead:
            if col == 'id':
                continue
            if col not in self.activeTable.columnsNames:
                message = 'column {} missing in SQL table'.format(col)
                QMessageBox.warning(self, 'Inconsistent Data', message, QMessageBox.Ok)
                return ()

        self.activeTable.importCSV(inpFile)
        self.populateTableWidget()

    def exportCSV(self):
        inpFile, _ = QFileDialog.getSaveFileName(None, 'Select .csv file', '', 'CSV files (*.csv)')

        tableHead = []
        for colNo in range(self.ui.tableWidget.columnCount()):
            colName = self.ui.tableWidget.horizontalHeaderItem(colNo).text()
            tableHead.append(colName)

        array = self.readTable()
        with open(inpFile, mode='w', newline='') as csvFile:
            fileWriter = csv.writer(csvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            fileWriter.writerow(tableHead)
            for i in array:
                fileWriter.writerow(i)


class CreateTable(QDialog):
    def __init__(self, tableName):
        super(CreateTable, self).__init__()
        Ui_createTableWindow, QtBaseClass = uic.loadUiType('createTable.ui')
        self.gui = Ui_createTableWindow()
        self.gui.setupUi(self)
        self.gui.toolButtonAddRow.clicked.connect(self.addRow)
        self.tableName = tableName

    def addRow(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        row = self.gui.tableWidgetCreateTable.rowCount()
        self.gui.tableWidgetCreateTable.insertRow(row)

        for col in range(self.gui.tableWidgetCreateTable.columnCount()):
            headerName = self.gui.tableWidgetCreateTable.horizontalHeaderItem(col).text()
            if headerName == 'Type':
                cell = QComboBox()
                self.dataTypes = ['INT', 'FLOAT', 'VARCHAR', 'TEXT', 'DATE']
                cell.addItems(self.dataTypes)
                self.gui.tableWidgetCreateTable.setCellWidget(row, col, cell)
                # cell.currentIndexChanged.connect(self.setDefaultDataTypeLength)

    # def setDefaultDataTypeLength(self, item):
    #     print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     print(item, type(item))
    #     print(self.dataTypes[item])
    #     # print(row, col)

    def tableQuery(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        print(sys._getframe().f_code.co_name)
        print('caller: ', sys._getframe().f_back.f_code.co_name)
        #todo cand se modifica col type in varchar automat are nevoie de length
        rows = self.gui.tableWidgetCreateTable.rowCount()
        cols = self.gui.tableWidgetCreateTable.columnCount()
        tableHead = []
        for col in range(self.gui.tableWidgetCreateTable.columnCount()):
            headerName = self.gui.tableWidgetCreateTable.horizontalHeaderItem(col).text()
            tableHead.append(headerName)

        query = "CREATE TABLE IF NOT EXISTS {} ( ".format(self.tableName)
        extra = ''
        for row in range(rows):
            for column in range(cols):
                cell = self.gui.tableWidgetCreateTable.item(row, column)
                headerName = self.gui.tableWidgetCreateTable.horizontalHeaderItem(column).text()
                if headerName == 'Name':
                    if cell is None:
                        message = 'Please give a name to column'
                        QMessageBox.warning(self, 'Missing Data', message, QMessageBox.Ok)
                        return ()
                    name = cell.text()
                    rowQuery = '{} '.format(name)
                elif headerName == 'Type':
                    widget = self.gui.tableWidgetCreateTable.cellWidget(row, column)
                    type = widget.currentText()
                    rowQuery += '{}'.format(type)
                elif headerName == 'Length':
                    if cell is not None:
                        lengthVal = '({})'.format(cell.text())
                        rowQuery += lengthVal
                elif headerName == 'Null':
                    if cell is not None and cell.checkState() == QtCore.Qt.Unchecked:
                        rowQuery += ' NOT NULL '
                elif headerName == 'Default':
                    if cell is None:
                        if 'NOT NULL' not in rowQuery:
                            rowQuery += ' DEFAULT NULL '
                    else:
                        rowQuery += ' {} '.format(cell.text())
                elif headerName == 'AutoIncrement':
                    if cell and cell.checkState() == QtCore.Qt.Checked:
                        # extra += '\n ALTER TABLE {} MODIFY {} {}{} AUTO_INCREMENT;'.format(self.tableName, name, type, lengthVal)
                        rowQuery += ' AUTO_INCREMENT '
                elif headerName == 'Key':
                    widget = self.gui.tableWidgetCreateTable.cellWidget(row, column)
                    keyType = widget.currentText()
                    if keyType == 'None':
                        continue
                    elif keyType == 'PRIMARY KEY':
                        extra += '\n ALTER TABLE {} ADD PRIMARY KEY ({});'.format(self.tableName, name)
                    elif keyType == 'FOREIGN KEY':
                        refTableindx = tableHead.index('Ref_Table')
                        refColindx = tableHead.index('Ref_Column')
                        refTab = self.gui.tableWidgetCreateTable.item(row, refTableindx).text()
                        refCol = self.gui.tableWidgetCreateTable.item(row, refColindx).text()
                        contraint = '´{}_ibfk´'.format(refTab)
                        extra += '\n ALTER TABLE {} ' \
                                 'ADD CONSTRAINT {} FOREIGN KEY ({}) ' \
                                 'REFERENCES {} ({}) ON DELETE CASCADE ON UPDATE CASCADE;'.format(self.tableName, contraint, name, refTab, refCol)

                    # rowQuery += ', \n'
            rowQuery += ', '
            query += rowQuery

        # print('_{}_'.format(query))
        query = query[:-2]
        query += ' );'

        completeQuery = query + extra
        print(50*'--')
        print(completeQuery)
        print(50 * '--')

        return completeQuery

    def colQuery(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        rows = self.gui.tableWidgetCreateTable.rowCount()
        cols = self.gui.tableWidgetCreateTable.columnCount()

        newRows = []
        for row in range(rows):
            for column in range(cols):
                cell = self.gui.tableWidgetCreateTable.item(row, column)
                headerName = self.gui.tableWidgetCreateTable.horizontalHeaderItem(column).text()
                if headerName == 'Name':
                    if cell is None:
                        message = 'Please give a name to column'
                        QMessageBox.warning(self, 'Missing Data', message, QMessageBox.Ok)
                        return
                    name = cell.text()
                elif headerName == 'Type':
                    widget = self.gui.tableWidgetCreateTable.cellWidget(row, column)
                    typeCol = widget.currentText()
                elif headerName == 'Length':
                    if cell is not None:
                        lengthVal = cell.text()
                    elif cell is None and typeCol == 'VARCHAR':
                        message = 'Please give a length to column'
                        QMessageBox.warning(self, 'Missing Data', message, QMessageBox.Ok)
                        return
                    else:
                        lengthVal = None
            tup = (name, typeCol, lengthVal)
            newRows.append(tup)
        return newRows

    @staticmethod
    def createTableQuery(tableName):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        dialog = CreateTable(tableName)
        result = dialog.exec_()
        query = dialog.tableQuery()
        if result == QDialog.Accepted:
            return query
        else:
            return None

    @staticmethod
    def createColumnQuery(tableName):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        dialog = CreateTable(tableName)
        result = dialog.exec_()
        query = dialog.colQuery()
        if result == QDialog.Accepted:
            return query
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
