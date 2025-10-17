import numpy as np
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QDateTime, QTime
import sip
import pathlib
import sys
from datetime import datetime
from mysqlquerys import connect
from mysqlquerys import postgresql_rm
from mysqlquerys import mysql_rm
import inspect
np.set_printoptions(linewidth=600)


class CheckRequiredFiles:
    def __init__(self):
        path2GUI = pathlib.Path(__file__)
        self.path2GUI = path2GUI.resolve(path2GUI).parent / 'gui'
        self.gui = self.path2GUI / 'gui.ui'
        self.postgresql_gui = self.path2GUI / 'postgresql_gui.ui'
        self.mysql_gui = self.path2GUI / 'postgresql_gui.ui'
        self.filterWindow = self.path2GUI / 'filterWindow.ui'
        self.inputsWindow = self.path2GUI / 'inputs_sql.ui'


class guiSqlRM(QMainWindow, CheckRequiredFiles):
    def __init__(self, connection):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        super(guiSqlRM, self).__init__()
        Ui_MysqlWindow, QtBaseClass = uic.loadUiType(self.mysql_gui)
        self.ui = Ui_MysqlWindow()
        self.ui.setupUi(self)
        self.credentials = connection.credentials
        self.db_type = connection.db_type
        if self.db_type == 'mysql':
            self.sql_rm = mysql_rm
            self.ui.TBox_db_sch_tab.setItemEnabled(1, False)
        elif self.db_type == 'postgresql':
            self.sql_rm = postgresql_rm

        self.ui.GB_db_defs.setVisible(False)
        self.ui.GB_schema_defs.setVisible(False)
        self.ui.LW_schemas_available_in_db.setVisible(False)
        self.ui.GB_table_defs.setVisible(False)

        self.GB_db_defs = self.ui.GB_db_defs
        self.GB_db_not_callable = self.ui.GB_db_not_callable
        self.GB_db_callable_without_args = self.ui.GB_db_callable_without_args
        self.GB_db_callable_with_args = self.ui.GB_db_callable_with_args
        self.GB_schema_not_callable = self.ui.GB_schema_not_callable
        self.GB_schema_callable_without_args = self.ui.GB_schema_callable_without_args
        self.GB_schema_callable_with_args = self.ui.GB_schema_callable_with_args
        self.GB_table_defs = self.ui.GB_table_defs
        self.GB_table_not_callable = self.ui.GB_table_not_callable
        self.GB_table_callable_without_args = self.ui.GB_table_callable_without_args
        self.GB_table_callable_with_args = self.ui.GB_table_callable_with_args
        self.ui.TBox_db_sch_tab.setCurrentIndex(0)

        self.ui.CheckB_db_methods.toggled.connect(self.populate_class_methods)
        self.ui.CheckB_schema_methods.toggled.connect(self.populate_class_methods)
        self.ui.CheckB_table_methods.toggled.connect(self.populate_class_methods)

        self.db = self.sql_rm.DataBase(self.credentials)
        title = '{} {}'.format(self.credentials['database'], self.db.dataBaseVersion)
        self.setWindowTitle(title)

        self.ui.CheckB_hide_schemas_list.toggled.connect(lambda: self.populate_list(self.db.allAvailableTablesInDatabase, self.ui.LW_schemas_available_in_db))
        self.ui.CheckB_hide_tables_list.toggled.connect(lambda: self.populate_list(self.schema.allAvailableTablesInSchema, self.ui.LW_tables_available))
        self.ui.CheckB_hide_table.toggled.connect(lambda: self.hide_table_widget(self.ui.TW_table_data))

        if self.db_type == 'mysql':
            self.populate_list(self.db.allAvailableTablesInDatabase, self.ui.LW_schemas_available_in_db)
            self.ui.LW_schemas_available_in_db.itemDoubleClicked.connect(self.connect_to_table)
        elif self.db_type == 'postgresql':
            self.populate_list(self.db.allAvailableSchemas, self.ui.LW_schemas_available_in_db)
            self.ui.LW_schemas_available_in_db.itemDoubleClicked.connect(self.connect_to_schema)
            self.ui.LW_tables_available.itemDoubleClicked.connect(self.connect_to_table)

        self.ui.TW_table_data.horizontalHeader().sectionClicked.connect(self.sort)
        self.ui.TW_table_data.horizontalHeader().sectionDoubleClicked.connect(self.setFilter)
        self.ui.PB_default_filter.clicked.connect(self.set_default_filter_filter)
        self.ui.PB_show_full_table.clicked.connect(self.show_full_table)

    def populate_list(self, list_items, list_widget):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if isinstance(self.sender(), QCheckBox):
            if self.sender().isChecked():
                list_widget.setVisible(False)
                list_widget.clear()
                for i, schema in enumerate(list_items):
                    list_widget.insertItem(i, schema)
            else:
                list_widget.setVisible(True)
        elif isinstance(self.sender(), QPushButton):
            list_widget.setVisible(True)
            list_widget.clear()
            for i, schema in enumerate(list_items):
                list_widget.insertItem(i, schema)

    def hide_table_widget(self, table_widget):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if isinstance(self.sender(), QCheckBox):
            if self.sender().isChecked():
                table_widget.setVisible(False)
            else:
                table_widget.setVisible(True)

    def populate_class_methods(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if 'DataBase' in self.sender().text():
            module_class = self.sql_rm.DataBase
            module_instance = self.db
            module_class_name = 'self.sql_rm.DataBase'
            group_box = self.GB_db_defs
            GB_not_callable = self.GB_db_not_callable
            GB_callable_without_args = self.GB_db_callable_without_args
            GB_callable_with_args = self.GB_db_callable_with_args
            definitions = [x for x in dir(self.sql_rm.DataBase) if not x.startswith('__')]
        elif 'Schema' in self.sender().text():
            module_class = self.sql_rm.Schema
            module_instance = self.schema
            module_class_name = 'self.sql_rm.Schema'
            group_box = self.GB_schema_defs
            GB_not_callable = self.GB_schema_not_callable
            GB_callable_without_args = self.GB_schema_callable_without_args
            GB_callable_with_args = self.GB_schema_callable_with_args
            definitions_DB = [x for x in dir(self.sql_rm.DataBase) if not x.startswith('__')]
            definitions = [x for x in dir(self.sql_rm.Schema) if not x.startswith('__')]
            for item in definitions:
                if item in definitions_DB:
                    definitions.remove(item)
        elif 'Table' in self.sender().text():
            module_class = self.sql_rm.Table
            module_instance = self.table
            module_class_name = 'self.sql_rm.Table'
            group_box = self.GB_table_defs
            GB_not_callable = self.GB_table_not_callable
            GB_callable_without_args = self.GB_table_callable_without_args
            GB_callable_with_args = self.GB_table_callable_with_args
            definitions_DB = [x for x in dir(self.sql_rm.DataBase) if not x.startswith('__')]
            definitions = [x for x in dir(self.sql_rm.Table) if not x.startswith('__')]
            new_def = []
            for item in definitions:
                if item in definitions_DB:
                    continue
                else:
                    new_def.append(item)
            definitions = new_def

        if isinstance(self.sender(), QCheckBox):
            if self.sender().isChecked():
                group_box.setVisible(True)
                vbox_not_callable = QGridLayout()
                vbox_callable_without_args = QGridLayout()
                vbox_callable_with_args = QGridLayout()
                for i, meth_name in enumerate(definitions):
                    radio = QRadioButton(meth_name)
                    radio.col = 0
                    radio.row = i
                    radio.module_class = module_class
                    radio.module_instance = module_instance
                    radio.meth_name = meth_name
                    meth = getattr(module_class, meth_name)
                    if callable(meth):
                        print('meth', meth_name)
                        docs = None
                        # if hasattr(meth, '__doc__'):
                        #     docs = getattr(meth, '__doc__')
                        varname = 'def_args'
                        loc = locals()
                        exec('{}=inspect.getfullargspec({}.{})'.format(varname, module_class_name, meth_name), globals(), loc)
                        meth_args = (loc[varname]).args
                        coloana = 1
                        if len(meth_args) == 1 and meth_args[0] == 'self':
                            radio.toggled.connect(self.start_noncallable_method)
                            vbox_callable_without_args.addWidget(radio, i, radio.col)
                        else:
                            vbox_callable_with_args.addWidget(radio, i, radio.col)
                            tool_button = QPushButton('inputs')
                            tool_button.meth_name = meth_name
                            tool_button.clicked.connect(self.get_method_arguments)
                            vbox_callable_with_args.addWidget(tool_button, i, 2)
                            push_button = QPushButton('Fire')
                            push_button.row = len(definitions) + 1
                            push_button.col = 2
                            push_button.clicked.connect(self.start_callable_method)
                            vbox_callable_with_args.addWidget(push_button, push_button.row, push_button.col)
                    else:
                        radio.toggled.connect(self.start_noncallable_method)
                        vbox_not_callable.addWidget(radio, i, radio.col)
                GB_not_callable.setLayout(vbox_not_callable)
                GB_callable_without_args.setLayout(vbox_callable_without_args)
                GB_callable_with_args.setLayout(vbox_callable_with_args)
            else:
                group_box.setVisible(False)

    def get_method_arguments(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if self.ui.TBox_db_sch_tab.currentIndex() == 0:
            layout_grupa = self.GB_callable_with_args.layout()
            module_class_name = 'self.sql_rm.DataBase'
            module_instance = self.db
        elif self.ui.TBox_db_sch_tab.currentIndex() == 1:
            layout_grupa = self.GB_schema_callable_with_args.layout()
            module_class_name = 'self.sql_rm.DataBase'
            module_instance = self.db
        elif self.ui.TBox_db_sch_tab.currentIndex() == 2:
            layout_grupa = self.GB_table_callable_with_args.layout()
            module_class_name = 'self.sql_rm.Table'
            module_instance = self.table
        args_dict = {}
        meth = None
        for x in range(layout_grupa.count()):
            item = layout_grupa.itemAt(x)
            widget = item.widget()
            if isinstance(widget, QRadioButton):
                if widget.isChecked():
                    meth = widget.text()
                    print(meth)
                    varname = 'def_args'
                    loc = locals()
                    exec('{}=inspect.getfullargspec({}.{})'.format(varname, module_class_name, meth), globals(), loc)
                    meth_args = (loc[varname]).args
                    print('\t', meth_args)

                    docs = None
                    if hasattr(meth, '__doc__'):
                        docs = getattr(meth, '__doc__')
                    for co, arg in enumerate(meth_args):
                        if arg == 'self':
                            continue

                        if docs:
                            for line in docs.split('\n'):
                                line = line.strip()
                                print(line)
                                if ':param' in line and arg in line:
                                    if 'QFileDialog.getOpenFileNames' in line:
                                        print('BINGO')

    def connect_to_schema(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        schema_name = self.ui.LW_schemas_available_in_db.currentItem().text()
        self.schema = self.sql_rm.Schema(self.credentials, schema_name)
        self.schema.set_schema_as_default()
        self.ui.TBox_db_sch_tab.setCurrentIndex(1)
        list_items = self.schema.allAvailableTablesInSchema
        list_widget = self.ui.LW_tables_available
        list_widget.setVisible(True)
        list_widget.clear()
        for i, schema in enumerate(list_items):
            list_widget.insertItem(i, schema)

    def connect_to_table(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.filterList = []
        if self.db_type == 'mysql':
            table_name = self.ui.LW_schemas_available_in_db.currentItem().text()
            self.table = self.sql_rm.Table(self.credentials, table_name)
        elif self.db_type == 'postgresql':
            schema_name = self.ui.LW_schemas_available_in_db.currentItem().text()
            table_name = self.ui.LW_tables_available.currentItem().text()
            self.table = self.sql_rm.Table(self.credentials, schema_name, table_name)

        self.ui.LE_tot_no_of_rows.setText(str(self.table.noOfRows))
        self.ui.TBox_db_sch_tab.setCurrentIndex(2)
        table_data = self.table.returnLastRecords('id', 100)
        table_data = np.atleast_2d(table_data)
        self.ui.lineEditFilterList.setText("last 100 id's")
        self.populate_table(table_data)

    def populate_table(self, table_data):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.ui.TW_table_data.clear()
        self.ui.TW_table_data.setRowCount(table_data.shape[0])
        self.ui.TW_table_data.setColumnCount(table_data.shape[1])
        tableHead = self.table.columnsNames
        self.ui.TW_table_data.setHorizontalHeaderLabels(tableHead)
        for col in range(table_data.shape[1]):
            for row in range(table_data.shape[0]):
                if isinstance(table_data[row, col], int):
                    item = QTableWidgetItem()
                    item.setData(QtCore.Qt.DisplayRole, table_data[row, col])
                else:
                    item = QTableWidgetItem(str(table_data[row, col]))
                self.ui.TW_table_data.setItem(row, col, item)
        self.ui.LE_showing.setText(str(table_data.shape[0]))

    def deleteItemsOfLayout(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        layout_grupa = self.GB_db_defs.layout()
        if layout_grupa is not None:
            while layout_grupa.count():
                item = layout_grupa.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.deleteItemsOfLayout(item.layout())
            sip.delete(layout_grupa)

    def start_noncallable_method(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if self.sender().isChecked():
            method = self.sender().text()
            if not callable(getattr(self.sender().module_class, method)):
                text = getattr(self.sender().module_instance, self.sender().text())
                self.ui.TE_result.setPlainText(str(text))
            else:
                text = getattr(self.sender().module_instance, self.sender().text())()
                self.ui.TE_result.setPlainText(str(text))

    def start_callable_method(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if self.ui.TBox_db_sch_tab.currentIndex() == 0:
            layout_grupa = self.GB_db_defs.layout()
            module_class_name = 'self.sql_rm.DataBase'
            module_instance = self.db
        elif self.ui.TBox_db_sch_tab.currentIndex() == 1:
            layout_grupa = self.GB_schema_defs.layout()
            module_class_name = 'self.sql_rm.Schema'
            module_instance = self.schema
        elif self.ui.TBox_db_sch_tab.currentIndex() == 2:
            layout_grupa = self.GB_table_defs.layout()
            module_class_name = 'self.sql_rm.Table'
            module_instance = self.table

        args_dict = {}
        meth = None
        for x in range(layout_grupa.count()):
            item = layout_grupa.itemAt(x)
            widget = item.widget()
            if isinstance(widget, QRadioButton):
                if widget.isChecked():
                    meth = widget.text()
                    print(meth)
                    varname = 'def_args'
                    loc = locals()
                    exec('{}=inspect.getfullargspec({}.{})'.format(varname, module_class_name, meth), globals(), loc)
                    meth_args = (loc[varname]).args
                    for arg in meth_args:
                        if arg == 'self':
                            continue
                        for x in range(layout_grupa.count()):
                            item = layout_grupa.itemAt(x)
                            widget = item.widget()
                            if isinstance(widget, QLineEdit):
                                if widget.arument == arg:
                                    args_dict[arg] = widget.text()
                                    break
                            elif isinstance(widget, QListWidget):
                                if widget.arument == arg:
                                    args_dict = []
                                    for i in range(widget.count()):
                                        args_dict.append(widget.item(i).text())
                                        break
        if not meth:
            message = "Please select the a method"
            QMessageBox.warning(self, 'Fehlende Daten', message, QMessageBox.Ok)
            return

        text = getattr(module_instance, meth)(**args_dict)
        self.ui.TE_result.setPlainText(str(text))

    def sort(self, logical_index):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        header = self.ui.TW_table_data.horizontalHeader()
        order = Qt.DescendingOrder
        if not header.isSortIndicatorShown():
            header.setSortIndicatorShown(True)
        elif header.sortIndicatorSection() == logical_index:
            order = header.sortIndicatorOrder()
        header.setSortIndicator(logical_index, order)
        self.ui.TW_table_data.sortItems(logical_index, order)

    def setFilter(self, logical_index):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        colName = self.table.columnsNames[logical_index]

        if self.table.columnsProperties[colName] == 'datetime' or \
                self.table.columnsProperties[colName] == 'timestamp' or \
                self.table.columnsProperties[colName] == 'timestamp without time zone':
            filt = FilterWindow.getDateTimeInterval(colName)
            if not filt:
                return
            if isinstance(filt, tuple):
                minDate, maxDate = filt
                minDate = minDate.toPyDateTime()
                maxDate = maxDate.toPyDateTime()
                filterVals = (str(minDate), str(maxDate))
            elif isinstance(filt, QDateTime):
                filterVals = filt.toPyDateTime()
            self.applyFilter(colName, filterVals)
        elif self.table.columnsProperties[colName] == 'time' or \
                self.table.columnsProperties[colName] == 'time without time zone':
            filt = FilterWindow.getTimeInterval(colName)
            if not filt:
                return
            if isinstance(filt, tuple):
                minTime, maxTime = filt
                minTime = minTime.toPyTime()
                maxTime = maxTime.toPyTime()
                filterVals = (str(minTime), str(maxTime))
            elif isinstance(filt, QTime):
                filterVals = filt.toPyTime()
            self.applyFilter(colName, filterVals)
        elif self.table.columnsProperties[colName] == 'int' or \
                self.table.columnsProperties[colName] == 'integer' or \
                self.table.columnsProperties[colName] == 'mediumint':
            filt = FilterWindow.getIntInterval(colName)
            if not filt:
                return
            if isinstance(filt, tuple):
                minTime, maxTime = filt
                filterVals = (str(minTime), str(maxTime))
            elif isinstance(filt, str):
                filterVals = filt
            self.applyFilter(colName, filterVals)
        else:
            header = self.ui.TW_table_data.horizontalHeader()
            geom = QtCore.QRect(header.sectionViewportPosition(logical_index), 0, header.sectionSize(logical_index),
                                header.height())
            item = QLineEdit(header)
            item.setGeometry(geom)
            item.show()
            item.setFocus()
            item.editingFinished.connect(lambda: (self.applyFilter(colName, item.text()), item.clear(),
                                                  item.hide(), item.deleteLater()))

    def applyFilter(self, colName, filter):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if filter == "":
            return

        filterText = self.ui.lineEditFilterList.text()
        if filterText == "last 100 id's":
            filterText = ""
            self.ui.lineEditFilterList.setText(filterText)
        if not filterText:
            if isinstance(filter, str):
                filterText += '{}="{}"'.format(colName, filter)
            elif isinstance(filter, tuple):
                filterText += '{} < {} < {}'.format(filter[0], colName, filter[1])
            elif isinstance(filter, list):
                filterText += '{} in {}'.format(str(filter), colName)
        else:
            if isinstance(filter, str):
                filterText += '; {}="{}"'.format(colName, filter)
            elif isinstance(filter, tuple):
                filterText += '; {} < {} < {}'.format(filter[0], colName, filter[1])
            elif isinstance(filter, list):
                filterText += '{} in {}'.format(str(filter), colName)

        self.ui.lineEditFilterList.setText(filterText)
        tup = (colName, filter)
        self.filterList.append(tup)

        table_data = self.table.filterRows(self.filterList)

        if table_data:
            table_data = np.atleast_2d(table_data)
        else:
            table_data = np.zeros((0, len(self.tableHead)), dtype=str)

        self.populate_table(table_data)

    def set_default_filter_filter(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        table_data = self.table.returnLastRecords('id', 100)
        table_data = np.atleast_2d(table_data)
        self.populate_table(table_data)
        self.ui.lineEditFilterList.setText("last 100 id's")

    def show_full_table(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        table_data = self.table.returnAllRecordsFromTable()
        table_data = np.atleast_2d(table_data)
        self.populate_table(table_data)
        self.ui.lineEditFilterList.setText("")


class FilterWindow(QDialog, CheckRequiredFiles):
    def __init__(self, colType, colName):
        super(FilterWindow, self).__init__()
        self.colName = colName
        Ui_MainWindow, QtBaseClass = uic.loadUiType(self.filterWindow)
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)
        self.gui.GBDateTime.setVisible(False)
        self.gui.GBLineEdit.setVisible(False)
        self.gui.GBTime.setVisible(False)
        self.gui.checkBoxDateTime.stateChanged.connect(self.openDateTimeInterval)
        self.gui.checkBoxTime.stateChanged.connect(self.openTimeInterval)
        self.gui.checkBoxMaxVal.stateChanged.connect(self.openValInterval)
        if colType == 'dateTime':
            self.gui.GBDateTime.setVisible(True)
            self.gui.dateTimeEdit_MaxVal.setEnabled(False)
            self.gui.label_dateTime.setText('= {}'.format(self.colName))
            self.gui.dateTimeEdit_MinVal.setDateTime(QDateTime(datetime.now().year,
                                                               datetime.now().month,
                                                               1, 0, 0, 0))
            self.gui.dateTimeEdit_MaxVal.setDateTime(QDateTime(datetime.now().year,
                                                               datetime.now().month,
                                                               datetime.now().day,
                                                               datetime.now().hour,
                                                               datetime.now().minute,
                                                               datetime.now().second))
        elif colType == 'time':
            self.gui.GBTime.setVisible(True)
            self.gui.timeEditMax.setEnabled(False)
        elif colType == 'int':
            self.gui.GBLineEdit.setVisible(True)
            self.gui.lineEditMax.setEnabled(False)

        self.rejected.connect(self.byebye)

    def openDateTimeInterval(self):
        if self.gui.checkBoxDateTime.isChecked():
            self.gui.dateTimeEdit_MaxVal.setEnabled(True)
            self.gui.label_dateTime.setText('< {} <'.format(self.colName))
        else:
            self.gui.dateTimeEdit_MaxVal.setEnabled(False)
            self.gui.label_dateTime.setText('= {}'.format(self.colName))

    def openTimeInterval(self):
        if self.gui.checkBoxTime.isChecked():
            self.gui.timeEditMax.setEnabled(True)
            self.gui.label_Time.setText('< {} <'.format(self.colName))
        else:
            self.gui.timeEditMax.setEnabled(False)
            self.gui.label_Time.setText('= {}'.format(self.colName))

    def openValInterval(self):
        if self.gui.checkBoxMaxVal.isChecked():
            self.gui.lineEditMax.setEnabled(True)
            self.gui.label_val.setText('< {} <'.format(self.colName))
        else:
            self.gui.lineEditMax.setEnabled(False)
            self.gui.label_val.setText('= {}'.format(self.colName))

    def byebye(self):
        self.close()

    def dateTimeInterval(self):
        if self.gui.checkBoxDateTime.isChecked():
            tup = (self.gui.dateTimeEdit_MinVal.dateTime(), self.gui.dateTimeEdit_MaxVal.dateTime())
            return tup
        else:
            return self.gui.dateTimeEdit_MinVal.dateTime()

    def timeInterval(self):
        if self.gui.checkBoxTime.isChecked():
            tup = (self.gui.timeEditMin.time(), self.gui.timeEditMax.time())
            return tup
        else:
            return self.gui.timeEditMin.time()

    def intInterval(self):
        if self.gui.checkBoxMaxVal.isChecked():
            tup = (self.gui.lineEditMin.text(), self.gui.lineEditMax.text())
            return tup
        else:
            return self.gui.lineEditMin.text()

    @staticmethod
    def getDateTimeInterval(colName):
        dialog = FilterWindow('dateTime', colName)
        result = dialog.exec_()
        filt = dialog.dateTimeInterval()
        if result == QDialog.Accepted:
            return filt
        else:
            return None

    @staticmethod
    def getTimeInterval(colName):
        dialog = FilterWindow('time', colName)
        result = dialog.exec_()
        filt = dialog.timeInterval()
        if result == QDialog.Accepted:
            return filt
        else:
            return None

    @staticmethod
    def getIntInterval(colName):
        dialog = FilterWindow('int', colName)
        result = dialog.exec_()
        filt = dialog.intInterval()
        if result == QDialog.Accepted:
            return filt
        else:
            return None


class InputsSQL(QDialog, CheckRequiredFiles):
    def __init__(self, colType, colName):
        super(InputsSQL, self).__init__()
        Ui_MainWindow, QtBaseClass = uic.loadUiType(self.inputsWindow)
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)


class window1(QMainWindow, CheckRequiredFiles):
    def __init__(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        super(window1, self).__init__()
        Ui_MainWindow, QtBaseClass = uic.loadUiType(self.gui)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.conf = None
        self.GB_dbs_available = self.ui.GB_dbs_available
        self.ui.PB_connect_to_db.setVisible(False)
        self.ui.GB_dbs_available.setVisible(False)
        self.ui.TB_load_config_ini.clicked.connect(lambda: (self.load_config_ini(), self.read_config_ini()))
        self.ui.PB_connect_to_db.clicked.connect(self.connect_to_db)

    def load_config_ini(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        inpFile, _ = QFileDialog.getOpenFileName(None, "", "", '*.ini')
        if not inpFile:
            return
        self.ui.LE_load_config_ini.setText(inpFile)

    def read_config_ini(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        file_name = self.ui.LE_load_config_ini.text()
        self.conf = connect.Config(file_name)
        if len(self.conf.sections) == 1:
            self.ui.PB_connect_to_db.setVisible(True)
            # self.conf.credentials = 0
        elif len(self.conf.sections) > 1:
            self.ui.GB_dbs_available.setVisible(True)
            self.populate_available_dbs()

    def populate_available_dbs(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if self.GB_dbs_available.layout() is not None:
            self.deleteItemsOfLayout()
        vbox = QGridLayout()
        for i, variab in enumerate(self.conf.sections):
            radio = QRadioButton(variab)
            radio.index = i
            radio.toggled.connect(lambda: (self.ui.PB_connect_to_db.setVisible(True), self.set_section_ini()))
            vbox.addWidget(radio, i, 0)
        self.GB_dbs_available.setLayout(vbox)

    def set_section_ini(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.conf.credentials = self.sender().index

    def connect_to_db(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.window = guiSqlRM(self.conf)
        self.window.show()
        self.close()

    def deleteItemsOfLayout(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        layout_grupa = self.GB_dbs_available.layout()
        if layout_grupa is not None:
            while layout_grupa.count():
                item = layout_grupa.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.deleteItemsOfLayout(item.layout())
            sip.delete(layout_grupa)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = window1()
    window.show()
    sys.exit(app.exec_())
