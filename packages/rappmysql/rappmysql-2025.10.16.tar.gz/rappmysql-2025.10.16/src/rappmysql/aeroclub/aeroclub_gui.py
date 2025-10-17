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
import pathlib
import datetime as dt
import matplotlib.pyplot as plt
import rappmysql
from rappmysql.mysqlquerys import connect
from rappmysql.mruser.myusers import Users
from rappmysql.aeroclub.aeroclub import AeroclubSQL
np.set_printoptions(linewidth=600)

compName = os.getenv('COMPUTERNAME')
table_head_conversion = {
    'table_last_records': ['data', 'type', 'brutto', 'amount', 'eProvider', 'km'],
    'TW_all_alimentari': ['data', 'type', 'brutto', 'amount', 'eProvider', 'km'],
}


class CheckRequiredFiles:
    def __init__(self):
        path2GUI = pathlib.Path(__file__)
        self.path2GUI = path2GUI.resolve(path2GUI).parent / 'GUI'
        self.main_window = self.path2GUI / 'aeroclub.ui'
        # self.add_auto_window = self.path2GUI / 'add_auto.ui'
        guiFiles = [self.main_window]
        self.checkExistance(guiFiles)

    def checkExistance(self, listOfFiles):
        for file in listOfFiles:
            if not os.path.exists(file):
                raise FileNotFoundError('{}'.format(file))


class MyApp(QMainWindow, CheckRequiredFiles):
    def __init__(self):
        super(MyApp, self).__init__()
        # print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
        #                                                           sys._getframe().f_back.f_code.co_name))
        caller = sys._getframe().f_back.f_code.co_name
        Ui_MainWindow, QtBaseClass = uic.loadUiType(self.main_window)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.conf = connect.Config(rappmysql.ini_aeroclub)
        self.setWindowTitle('{}'.format(self.conf.credentials['database']))

        # self.user = None
        # self.app = None
        # self.app_users = Users(self.user)

        self.ui.GB_add_alim.setVisible(False)

        self.ui.PB_login.clicked.connect(self.login_user)
        self.ui.PB_export_profile.clicked.connect(self.export_full_profile)
        self.ui.PB_import_profile.clicked.connect(self.import_profile)
        self.ui.CBMonths.currentIndexChanged.connect(self.populateDatesInterval)
        self.ui.PB_fire_filter.clicked.connect(self.populateDetailsTab)
        self.ui.TW_all_alimentari.horizontalHeader().sectionClicked.connect(self.sortTable)
        self.ui.PB_fire_add_row.clicked.connect(self.import_csv)
        self.ui.TB_add_file.clicked.connect(self.get_file_pth)

        # self.ui.PB_add_car.clicked.connect(self.add_car)
        # self.ui.PB_Export_csv.clicked.connect(self.export_CSV)
        # self.ui.TW_all_alimentari.horizontalHeader().sectionClicked.connect(self.sortPlan)
        # self.ui.TW_all_alimentari.itemDoubleClicked.connect(self.upload_download_file)
        # self.ui.CB_airplanes.currentIndexChanged.connect(self.populate_GB_additional_for_add_row)
        # self.ui.CB_all_user_cars.currentIndexChanged.connect(self.fill_in_tab)
        # self.ui.CB_add_alim.toggled.connect(self.add_cost)
        # self.ui.TW_main_user_interface.currentChanged.connect(self.fill_in_tab)

        if compName == 'DESKTOP-5HHINGF' or compName == 'MPCC6995':
            self.ui.LE_user_name.setText('radu')
            self.ui.LE_user_pass.setText('9876')
            self.login_user()

    def login_user(self):
        user_name = self.ui.LE_user_name.text()
        password = self.ui.LE_user_pass.text()
        self.user = Users(user_name, rappmysql.ini_users)
        if self.user.verify_password(password):
            # self.ui.PB_export_profile.setVisible(True)
            # self.ui.TW_main_user_interface.setVisible(True)
            self.user.init_app('aeroclub', rappmysql.ini_aeroclub)
            self.app = AeroclubSQL(rappmysql.ini_aeroclub)
            # all_user_cars = list(self.user.masini)
            # # print('all_user_cars', all_user_cars)
            # if all_user_cars:
            #     self.ui.CB_all_user_cars.addItems(all_user_cars)
            #     self.ui.TW_main_user_interface.setTabText(0, all_user_cars[0])
            #     table_name = self.ui.TW_main_user_interface.tabText(self.ui.TW_main_user_interface.currentIndex())
            #     id_car = int(self.user.get_id_all_cars(table_name))
            #     # print('--id_car', id_car)
            #     # self.app = Masina(rappmysql.ini_masina, all_user_cars[0].lower(), 1)

            self.prepare_aeroclub_interface()
            #     # for car in all_user_cars[1:]:
            #     #     tab = QWidget()
            #     #     self.ui.TW_main_user_interface.addTab(tab, car)
            # else:
            #     self.ui.TW_main_user_interface.setVisible(False)

    def export_full_profile(self):
        # expName, _ = QFileDialog.getSaveFileName(self, "Save file", "", "File (*.zip)")
        # expDir = QFileDialog.getExistingDirectory()
        # print(expDir)
        # if expName:
        if self.ui.CB_export_profile_with_files.isChecked():
            self.user.aeroclub_app.export_aeroclub_profile(output_dir=None, export_files=True)
        else:
            self.user.aeroclub_app.export_aeroclub_profile(output_dir=None, export_files=False)

    def import_profile(self):
        import_files=self.ui.CB_import_profile_with_files.isChecked()
        zipFile, _ = QFileDialog.getOpenFileName(self, "Open file", "", "File (*.zip)")
        if zipFile:
            if self.user:
                self.user.import_aeroclub_profile(zipFile, import_files=import_files)
            else:
                self.app_users.import_aeroclub_profile(zipFile, import_files=import_files)
            self.login_user()

    def prepare_aeroclub_interface(self):
        self.populateSummaryTab()

        self.populate_CB_airplanes()
        self.populateCBMonths()
        # self.alim_date()
        self.populateDatesInterval()
        self.populateDetailsTab()

    def populateDetailsTab(self):
        # self.populate_table_widget(self.ui.TW_all_alimentari, self.app.get_all_alimentari())
        selectedStartDate = self.ui.DEFrom.date().toPyDate()
        selectedEndDate = self.ui.DEBis.date().toPyDate()
        airplane = self.ui.CB_airplanes_filter.currentText()
        if self.ui.CB_airplanes_filter.currentText() == 'all':
            airplane = None
        res_table = self.app.get_flights_for_interval_type(selectedStartDate, selectedEndDate, airplane)
        self.populate_table_widget(self.ui.TW_all_alimentari, res_table)
        self.ui.LE_filter_showing.setText(str(res_table.shape[0] - 1))
        self.ui.LE_total_rows.setText(str(self.app.table_zbor_log.noOfRows))
        return res_table

    def populateDatesInterval(self):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        startDate, lastDayOfMonth = self.app.default_interval

        if self.ui.CBMonths.currentText() != 'interval':
            year = int(self.ui.SB_year.value())
            startDate, lastDayOfMonth = self.app.get_monthly_interval(self.ui.CBMonths.currentText(), year)

        self.ui.DEFrom.setDate(startDate)
        self.ui.DEBis.setDate(lastDayOfMonth)

        self.ui.DEFrom.setCalendarPopup(True)
        self.ui.DEBis.setCalendarPopup(True)

    def populateCBMonths(self):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.ui.CBMonths.addItem('interval')
        months = [dt.date(2000, m, 1).strftime('%B') for m in range(1, 13)]
        for month in months:
            self.ui.CBMonths.addItem(month)

        self.ui.SB_year.setValue(datetime.now().year)

    def populate_CB_airplanes(self):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.ui.CB_airplanes.addItems(self.app.all_airplanes_registrations)
        self.ui.CB_airplanes_filter.addItem('all')
        self.ui.CB_airplanes_filter.addItems(self.app.all_airplanes_registrations)

    def populate_table_widget(self, widget, table):
        tableHead, table_data = list(table[0]), table[1:]
        if self.ui.CB_SQL_table_head.isChecked() or widget.objectName() not in list(table_head_conversion.keys()):
            widget.setColumnCount(len(tableHead))
            widget.setHorizontalHeaderLabels(tableHead)
            widget.setRowCount(table_data.shape[0])
            for col in range(table_data.shape[1]):
                for row in range(table_data.shape[0]):
                    # if isinstance(table_data[row, col], int) or isinstance(table_data[row, col], float):
                    #     item = QTableWidgetItem()
                    #     item.setData(QtCore.Qt.DisplayRole, table[row, col])
                    # elif isinstance(table_data[row, col], decimal.Decimal):
                    #     val = float(table_data[row, col])
                    #     item = QTableWidgetItem()
                    #     item.setData(QtCore.Qt.DisplayRole, val)
                    # # elif tableHead[col] == 'file_name':
                    # #     text = "<a href={}>{}</a>".format(str(table_data[row, col]), str(table_data[row, col]))
                    # #     item = QTableWidgetItem(text)
                    # #     # item.setText(text)
                    # #     # item.setOpenExternalLinks(True)
                    # #     # item.clicked.connect(self.download_file)
                    # #     # widget.setCellWidget(row, col, item)
                    # #     # continue
                    # else:
                    #     item = QTableWidgetItem(str(table_data[row, col]))
                    item = QTableWidgetItem(str(table_data[row, col]))
                    widget.setItem(row, col, item)
        else:
            newTableHead = table_head_conversion[widget.objectName()]
            widget.setColumnCount(len(newTableHead))
            widget.setHorizontalHeaderLabels(newTableHead)
            widget.setRowCount(table_data.shape[0])
            for col in range(table_data.shape[1]):
                # print(tableHead[col], newTableHead, tableHead[col] in newTableHead)
                if tableHead[col] in newTableHead:
                    for row in range(table_data.shape[0]):
                        # if isinstance(table_data[row, col], int) or isinstance(table_data[row, col], float):
                        #     item = QTableWidgetItem()
                        #     item.setData(QtCore.Qt.DisplayRole, table[row, col])
                        # elif isinstance(table_data[row, col], decimal.Decimal):
                        #     val = float(table_data[row, col])
                        #     item = QTableWidgetItem()
                        #     item.setData(QtCore.Qt.DisplayRole, val)
                        # # elif tableHead[col] == 'file_name':
                        # #     text = "<a href={}>{}</a>".format(str(table_data[row, col]), str(table_data[row, col]))
                        # #     item = QTableWidgetItem(text)
                        # #     # item.setText(text)
                        # #     # item.setOpenExternalLinks(True)
                        # #     # item.clicked.connect(self.download_file)
                        # #     # widget.setCellWidget(row, col, item)
                        # #     # continue
                        # else:
                        #     item = QTableWidgetItem(str(table_data[row, col]))
                        new_col = newTableHead.index(tableHead[col])
                        item = QTableWidgetItem(str(table_data[row, col]))
                        widget.setItem(row, new_col, item)
        header = widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

    def sortTable(self, logical_index):
        print(sys._getframe().f_code.co_name)
        header = self.ui.TW_all_alimentari.horizontalHeader()
        order = Qt.DescendingOrder
        if not header.isSortIndicatorShown():
            header.setSortIndicatorShown(True)
        elif header.sortIndicatorSection() == logical_index:
            order = header.sortIndicatorOrder()
        header.setSortIndicator(logical_index, order)
        self.ui.TW_all_alimentari.sortItems(logical_index, order)

    def get_file_pth(self):
        self.loadFile, _ = QFileDialog.getOpenFileName(self, "File", "", "File (*.csv;*.CSV;)")
        if self.loadFile:
            self.ui.LE_add_file.setText(self.loadFile)

    def import_csv(self):
        csvfile = self.ui.LE_add_file.text()
        self.app.import_csv(csvfile)

    def populateSummaryTab(self):
        # print('***self.app.table_totals', self.app.table_totals)
        self.ui.LE_total_unpaid_flights.setText(str(self.app.total_unpaid_flights))
        self.ui.LE_flight_time_this_year.setText(str(self.app.flight_time_this_year))
        self.ui.LE_total_flight_time.setText(str(self.app.total_flight_time))


######################################################################

    # def add_cost(self):
    #     if self.ui.CB_add_alim.isChecked():
    #         self.ui.GB_add_alim.setVisible(True)
    #     else:
    #         self.ui.GB_add_alim.setVisible(False)
    #
    # def add_car(self):
    #     car_type, car_brand, car_model = AddCarWindow.get_def_arguments()
    #     self.user.add_car(car_brand, car_model, car_type)
    #
    # def fill_in_tab(self):
    #     current_car = self.ui.CB_all_user_cars.currentText()
    #     self.ui.TW_main_user_interface.setTabText(0, current_car)
    #     table_name = self.ui.TW_main_user_interface.tabText(self.ui.TW_main_user_interface.currentIndex())
    #     id_car = int(self.user.get_id_all_cars(table_name))
    #     self.app = Masina(rappmysql.ini_masina, self.user.id, id_car)
    #     self.prepare_aeroclub_interface()

    # def prepare_login_window(self):
    #     print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
    #                                                               sys._getframe().f_back.f_code.co_name))
    #     self.ui.TW_main_user_interface.setVisible(False)
    #     self.ui.PB_export_profile.setVisible(False)
    #     if not self.app_users.all_users:
    #         self.ui.PB_login.setVisible(False)

    # def upload_download_file(self, item):
    #     # print(item.column(), item.row(), item.text())
    #     if self.ui.TW_all_alimentari.horizontalHeaderItem(item.column()).text() == 'file_name':
    #         # print(item)
    #         id_ = self.ui.TW_all_alimentari.item(item.row(), 0).text()
    #         if item.text() != 'None':
    #             # print('ÄÄ', id_)
    #             print('id', id_)
    #             print('ÖÖ', self.ui.TW_all_alimentari.horizontalHeaderItem(0).text())
    #             expName, _ = QFileDialog.getSaveFileName(self, "Save file", "", "")
    #             print(expName)
    #             if expName:
    #                 file_content = self.app.alimentari.returnCellsWhere('file', ('id', id_))[0]
    #                 self.app.alimentari.write_file(file_content, expName)
    #             else:
    #                 return
    #         else:
    #             print('upload')
    #             uploadFile, _ = QFileDialog.getOpenFileName(self, "upload file", "", "")
    #             self.app.upload_file(uploadFile, id_)
    #             self.populateDetailsTab()
    #
    # def add_row(self):
    #     # print('self.app.insert_new_alim()')
    #     data = self.ui.alim_date.date().toPyDate()
    #     alim_type = self.ui.CB_airplanes.currentText()
    #     brutto = self.ui.LE_brutto.text()
    #
    #
    #     amount = self.ui.LE_amount.text()
    #     refuel = self.ui.LE_refuel.text()
    #     other = self.ui.LE_other.text()
    #     recharges = self.ui.LE_recharges.text()
    #     provider = self.ui.CB_eProvider.currentText()
    #     km = self.ui.LE_km.text()
    #     comment = self.ui.LE_comment.text()
    #     table_name = self.ui.TW_main_user_interface.tabText(self.ui.TW_main_user_interface.currentIndex())
    #     id_all_cars = self.user.get_id_all_cars(table_name.lower())
    #     # print('**', self.user.id, table_name.lower(), id_all_cars)
    #     # current_user_id, id_all_cars, data, alim_type, brutto, amount, refuel, other, recharges, km, comment, file
    #     self.app.insert_new_alim(current_user_id=self.user.id,
    #                              id_all_cars=id_all_cars,
    #                              data=data,
    #                              alim_type=alim_type,
    #                              brutto=brutto,
    #                              file=file,
    #                              amount=amount,
    #                              refuel=refuel,
    #                              other=other,
    #                              recharges=recharges,
    #                              provider=provider,
    #                              km=km,
    #                              comment=comment)
    #
    # def populate_GB_additional_for_add_row(self):
    #     print(self.ui.CB_airplanes.currentText())
    #     self.ui.GB_Amount.setVisible(False)
    #     self.ui.GB_Refuel.setVisible(False)
    #     self.ui.GB_other.setVisible(False)
    #     self.ui.GB_Charges.setVisible(False)
    #     self.ui.GB_provider.setVisible(False)
    #     self.ui.GB_Km.setVisible(False)
    #     self.ui.GB_Comment.setVisible(False)
    #     if self.ui.CB_airplanes.currentText() == 'electric':
    #         self.ui.GB_Amount.setVisible(True)
    #         self.ui.GB_Refuel.setVisible(True)
    #         self.ui.GB_other.setVisible(True)
    #         self.ui.GB_Charges.setVisible(True)
    #         self.ui.GB_provider.setVisible(True)
    #         self.ui.GB_Comment.setVisible(True)
    #         self.ui.label_L_KwH.setText('KwH')
    #         self.ui.label_Refuel_eCharge.setText('Echarge')
    #         self.ui.CB_eProvider.addItem('')
    #         # self.ui.CB_eProvider.addItems(self.app.electric_providers)
    #         self.ui.CB_eProvider.addItems(self.user.electric_providers)
    #     elif self.ui.CB_airplanes.currentText() == 'benzina':
    #         self.ui.GB_Amount.setVisible(True)
    #         self.ui.GB_Refuel.setVisible(True)
    #         self.ui.GB_other.setVisible(True)
    #         self.ui.GB_Charges.setVisible(True)
    #         self.ui.GB_Km.setVisible(True)
    #         self.ui.GB_Comment.setVisible(True)
    #         self.ui.label_L_KwH.setText('L')
    #         self.ui.label_Refuel_eCharge.setText('Refuel')
    #     elif self.ui.CB_airplanes.currentText() == 'intretinere':
    #         self.ui.GB_Km.setVisible(True)
    #         self.ui.GB_Comment.setVisible(True)
    #     else:
    #         self.ui.GB_Comment.setVisible(True)
    #
    # def alim_date(self):
    #     self.ui.alim_date.setDate(datetime.now())
    #     self.ui.alim_date.setCalendarPopup(True)
    #
    # def export_CSV(self):
    #     expName, _ = QFileDialog.getSaveFileName(self, "Save file", "", "File (*.csv)")
    #     print(expName)
    #     if expName:
    #         res_table = self.populateDetailsTab()
    #         with open(expName, 'w', newline='') as file:
    #             writer = csv.writer(file, delimiter=';')
    #             # if isinstance(array, list) or isinstance(array, np.ndarray):
    #             for row in res_table:
    #                 writer.writerow(row)
    #
    # def delete_items_of_layout(self):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     layout_grupa = self.gb_available_databases.layout()
    #     if layout_grupa is not None:
    #         while layout_grupa.count():
    #             item = layout_grupa.takeAt(0)
    #             widget = item.widget()
    #             if widget is not None:
    #                 widget.setParent(None)
    #             # else:
    #             #     delete_items_of_layout(item.layout())
    #         # sip.delete(layout_grupa)

    # def connect_to_db(self):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     print('self.sender().objectName()', self.sender().text())
    #     self.ui.GB_planned_expenses.setVisible(True)
    #     self.populateCBMonths()
    #     self.populateDatesInterval()
    #     self.get_table_info(self.sender().text())
    #     # self.populateCBConto()

    # def get_table_info(self):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     displayExpensesTableHead = ['table', 'name', 'value', 'myconto', 'payDay', 'freq']
    #     displayIncomeTableHead = ['name', 'brutto', 'lohnsteuer', 'rentenvers', 'arbeitslosvers', 'gesetzliche_abzuge',
    #                               'netto', 'krankenvers', 'privatvers', 'abzuge', 'uberweisung', 'myconto', 'payDay',
    #                               'freq', 'in_salary']
    #     selectedStartDate = self.ui.DEFrom.date().toPyDate()
    #     selectedEndDate = self.ui.DEBis.date().toPyDate()
    #     self.app.prepareTablePlan(self.ui.cbActiveConto.currentText(), selectedStartDate, selectedEndDate)
    #     self.income.prepareTablePlan(self.ui.cbActiveConto.currentText(), selectedStartDate, selectedEndDate)
    #
    #     self.populateExpensesPlan(displayExpensesTableHead)
    #     self.populate_expenses_summary()
    #     self.populateTree()
    #     self.populateIncomePlan(displayIncomeTableHead)
    #     self.populate_income_summary()
    #     self.totals()

    # def export(self):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     expName, _ = QFileDialog.getSaveFileName(self, "Save file", "", "Excel Files (*.xlsx)")
    #     worksheets = [('Complete', datetime(datetime.now().year, 1, 1),datetime(datetime.now().year, 12, 31))]
    #     for mnth in range(1, 13):
    #         firstDayOfMonth = datetime(datetime.now().year, mnth, 1)
    #         if mnth != 12:
    #             lastDayOfMonth = datetime(datetime.now().year, mnth+1, 1) - timedelta(days=1)
    #         else:
    #             lastDayOfMonth = datetime(datetime.now().year + 1, 1, 1) - timedelta(days=1)
    #
    #         tup = (firstDayOfMonth.strftime("%B"), firstDayOfMonth, lastDayOfMonth)
    #         worksheets.append(tup)
    #
    #     wb = Workbook()
    #     ws = wb.active
    #     for mnth, firstDayOfMonth, lastDayOfMonth in worksheets:
    #         # print(mnth, firstDayOfMonth, lastDayOfMonth)
    #         if mnth == 'Complete':
    #             ws.title = mnth
    #         else:
    #             wb.create_sheet(mnth)
    #         ws = wb[mnth]
    #         self.ui.DEFrom.setDate(QDate(firstDayOfMonth))
    #         self.ui.DEBis.setDate(QDate(lastDayOfMonth))
    #         self.prepareTablePlan()
    #
    #         planExpenseTable, planExpenseTableHead = self.readPlanExpenses()
    #         cheltData = np.insert(planExpenseTable, 0, planExpenseTableHead, 0)
    #
    #         for i, row in enumerate(cheltData):
    #             for j, col in enumerate(row):
    #                 ws.cell(row=i + 1, column=j + 1).value = cheltData[i][j]
    #
    #         firstRow = 1
    #         firstCol = get_column_letter(1)
    #         lastRow = len(cheltData)
    #         lastCol = get_column_letter(len(cheltData[0]))
    #
    #         table_title = '{}_{}'.format('chelt', mnth )
    #         new_text = ('{}{}:{}{}'.format(firstCol, firstRow, lastCol, lastRow))
    #         tab = Table(displayName=table_title, ref=new_text)
    #         # Add a default style with striped rows and banded columns
    #         style = TableStyleInfo(name="TableStyleMedium9", showFirstColumn=False,
    #                                showLastColumn=False, showRowStripes=True, showColumnStripes=True)
    #         tab.tableStyleInfo = style
    #         ws.add_table(tab)
    #         ws.cell(row=lastRow + 1, column=1).value = 'Total Number of Expenses'
    #         ws.cell(row=lastRow + 1, column=2).value = self.ui.LEtotalNoOfTransactions.text()
    #         ws.cell(row=lastRow + 2, column=1).value = 'Total Expenses'
    #         ws.cell(row=lastRow + 2, column=2).value = self.ui.LEtotalValue.text()
    #         #######income
    #
    #         planIncomeTable, planIncomeTableHead = self.readPlanIncome()
    #         incomeData = np.insert(planIncomeTable, 0, planIncomeTableHead, 0)
    #         firstRow = lastRow + 5
    #         firstCol = get_column_letter(1)
    #         lastRow = firstRow + len(incomeData)
    #         lastCol = get_column_letter(len(incomeData[0]))
    #
    #         for i, row in enumerate(incomeData):
    #             for j, col in enumerate(row):
    #                 ws.cell(row=i + firstRow, column=j + 1).value = incomeData[i][j]
    #
    #         table_title = '{}_{}'.format('income', mnth )
    #         new_text1 = ('{}{}:{}{}'.format(firstCol, firstRow, lastCol, lastRow))
    #         tab = Table(displayName=table_title, ref=new_text1)
    #         # Add a default style with striped rows and banded columns
    #         style = TableStyleInfo(name="TableStyleMedium9", showFirstColumn=False,
    #                                showLastColumn=False, showRowStripes=True, showColumnStripes=True)
    #         tab.tableStyleInfo = style
    #         ws.add_table(tab)
    #         ws.cell(row=lastRow + 1, column=1).value = 'Total Number of Incomes'
    #         ws.cell(row=lastRow + 1, column=2).value = self.ui.LEtotalNoOfIncome.text()
    #         ws.cell(row=lastRow + 2, column=1).value = 'Total Income'
    #         ws.cell(row=lastRow + 2, column=2).value = self.ui.LEtotalIncome.text()
    #
    #     wb.save(expName)

    # def populateTree(self):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     self.ui.TWmnthVSIrreg.clear()
    #     self.ui.TWmnthVSIrreg.setHeaderLabels(['freq', 'name', 'value'])
    #     monthly_level = QTreeWidgetItem(self.ui.TWmnthVSIrreg)
    #     monthly_level.setText(0, 'Monthly')
    #     irregular_level = QTreeWidgetItem(self.ui.TWmnthVSIrreg)
    #     irregular_level.setText(0, 'Irregular')
    #     monthlyIndx = np.where(self.app.expenses[:, self.app.tableHead.index('freq')] == 1)
    #     monthly = self.app.expenses[monthlyIndx]
    #     for mnth in monthly:
    #         mnth_item_level = QTreeWidgetItem(monthly_level)
    #         mnth_item_level.setText(1, mnth[self.app.tableHead.index('name')])
    #         mnth_item_level.setText(2, str(round(mnth[self.app.tableHead.index('value')])))
    #
    #     totalMonthly = self.app.expenses[monthlyIndx,self.app.tableHead.index('value')][0]
    #     monthly_level.setText(1, 'Total')
    #     monthly_level.setText(2, str(round(sum(totalMonthly), 2)))
    #
    #     irregIndx = np.where(self.app.expenses[:, self.app.tableHead.index('freq')] != 1)
    #     irregular = self.app.expenses[irregIndx]
    #     for irr in irregular:
    #         irr_item_level = QTreeWidgetItem(irregular_level)
    #         irr_item_level.setText(1, irr[self.app.tableHead.index('name')])
    #         irr_item_level.setText(2, str(round(irr[self.app.tableHead.index('value')], 2)))
    #
    #     totalIrreg = self.app.expenses[irregIndx,self.app.tableHead.index('value')][0]
    #     irregular_level.setText(1, 'Total')
    #     irregular_level.setText(2, str(round(sum(totalIrreg), 2)))
    #
    # def populateExpensesPlan(self, displayTableHead=None):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     if displayTableHead:
    #         tableHead, table = self.app.convert_to_display_table(self.app.tableHead, self.app.expenses, displayTableHead)
    #     else:
    #         tableHead, table = self.app.tableHead, self.app.expenses
    #
    #     self.ui.planTable.setColumnCount(len(tableHead))
    #     self.ui.planTable.setHorizontalHeaderLabels(tableHead)
    #     self.ui.planTable.setRowCount(table.shape[0])
    #     for col in range(table.shape[1]):
    #         for row in range(table.shape[0]):
    #             if isinstance(table[row, col], int) or isinstance(table[row, col], float):
    #                 item = QTableWidgetItem()
    #                 item.setData(QtCore.Qt.DisplayRole, table[row, col])
    #             elif isinstance(table[row, col], decimal.Decimal):
    #                 val = float(table[row, col])
    #                 item = QTableWidgetItem()
    #                 item.setData(QtCore.Qt.DisplayRole, val)
    #             else:
    #                 item = QTableWidgetItem(str(table[row, col]))
    #             self.ui.planTable.setItem(row, col, item)
    #
    # def populate_expenses_summary(self):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     self.ui.LEtotalNoOfTransactions.setText(str(self.app.tot_no_of_expenses()))
    #     self.ui.LEtotalValue.setText(str(self.app.tot_val_of_expenses()))
    #     self.ui.LEnoOfMonthly.setText(str(self.app.tot_no_of_monthly_expenses()))
    #     self.ui.LEtotalMonthly.setText(str(self.app.tot_val_of_monthly_expenses()))
    #     self.ui.LEnoOfIrregular.setText(str(self.app.tot_no_of_irregular_expenses()))
    #     self.ui.LEirregular.setText(str(self.app.tot_val_of_irregular_expenses()))
    #
    # def populateIncomePlan(self, displayTableHead=None):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     if displayTableHead:
    #         tableHead, table = self.income.convert_to_display_table(self.income.tableHead, self.income.income, displayTableHead)
    #     else:
    #         tableHead, table = self.income.tableHead, self.income.income
    #
    #     self.ui.planTableIncome.setColumnCount(len(tableHead))
    #     self.ui.planTableIncome.setHorizontalHeaderLabels(tableHead)
    #     self.ui.planTableIncome.setRowCount(table.shape[0])
    #     for col in range(table.shape[1]):
    #         for row in range(table.shape[0]):
    #             if isinstance(table[row, col], int) or isinstance(table[row, col], float):
    #                 item = QTableWidgetItem()
    #                 item.setData(QtCore.Qt.DisplayRole, table[row, col])
    #             elif isinstance(table[row, col], decimal.Decimal):
    #                 val = float(table[row, col])
    #                 item = QTableWidgetItem()
    #                 item.setData(QtCore.Qt.DisplayRole, val)
    #             else:
    #                 item = QTableWidgetItem(str(table[row, col]))
    #             self.ui.planTableIncome.setItem(row, col, item)
    #
    # def populate_income_summary(self):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     self.ui.LE_total_netto.setText(str(self.income.netto))
    #     self.ui.LE_total_taxes.setText(str(self.income.taxes))
    #     self.ui.LE_total_brutto.setText(str(self.income.brutto))
    #     self.ui.LE_salary_uberweisung.setText(str(self.income.salary_uberweisung))
    #     self.ui.LE_salary_abzuge.setText(str(self.income.salary_abzuge))
    #     self.ui.LE_salary_netto.setText(str(self.income.salary_netto))
    #     self.ui.LE_salary_gesetzliche_abzuge.setText(str(self.income.salary_gesetzliche_abzuge))
    #     self.ui.LE_salary_brutto.setText(str(self.income.salary_brutto))
    #
    # def totals(self):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     total = round(self.app.tot_val_of_expenses() + self.income.netto, 2)
    #     self.ui.LEtotalVa.setText(str(total))

    # def sortPlan(self, logical_index):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     header = self.ui.TW_all_alimentari.horizontalHeader()
    #     order = Qt.DescendingOrder
    #     if not header.isSortIndicatorShown():
    #         header.setSortIndicatorShown(True)
    #     elif header.sortIndicatorSection() == logical_index:
    #         order = header.sortIndicatorOrder()
    #     header.setSortIndicator(logical_index, order)
    #     self.ui.TW_all_alimentari.sortItems(logical_index, order)

    def readPlanExpenses(self):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        rows = self.ui.planTable.rowCount()
        cols = self.ui.planTable.columnCount()
        planExpenseTable = np.empty((rows, cols), dtype=object)
        planExpenseTableHead = []
        for row in range(rows):
            for column in range(cols):
                cell = self.ui.planTable.item(row, column)
                planExpenseTable[row, column] = cell.text()
                colName = self.ui.planTable.horizontalHeaderItem(column).text()
                if colName not in planExpenseTableHead:
                    planExpenseTableHead.append(colName)

        return planExpenseTable, planExpenseTableHead

    def readPlanIncome(self):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        rows = self.ui.planTableIncome.rowCount()
        cols = self.ui.planTableIncome.columnCount()
        planIncomeTable = np.empty((rows, cols), dtype=object)
        planIncomeTableHead = []
        for row in range(rows):
            for column in range(cols):
                cell = self.ui.planTableIncome.item(row, column)
                planIncomeTable[row, column] = cell.text()
                colName = self.ui.planTableIncome.horizontalHeaderItem(column).text()
                if colName not in planIncomeTableHead:
                    planIncomeTableHead.append(colName)

        return planIncomeTable, planIncomeTableHead

    def plotTablePie(self):
        #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        realExpenseTable, realExpenseTableHead = self.readPlanExpenses()
        allValues = realExpenseTable[:, realExpenseTableHead.index('value')].astype(float)
        if None in allValues:
            allValues = allValues[allValues != np.array(None)]
        totalVal = sum(allValues)

        colTableName = realExpenseTable[:, realExpenseTableHead.index('table')]
        labels = []
        sizes = []
        for table in np.unique(colTableName):
            indx = np.where(realExpenseTable[:, realExpenseTableHead.index('table')]==table)
            smallArray = realExpenseTable[indx]
            values = sum(smallArray[:, realExpenseTableHead.index('value')].astype(float))
            txt = '{} = {:.2f}'.format(table, values)
            labels.append(txt)
            size = (values/totalVal)*100
            sizes.append(size)

        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct='%1.2f%%', startangle=90)
        ax1.axis('equal')
        plt.legend(title='Total: {:.2f}'.format(totalVal))

        plt.show()

    # def plotNamePie(self):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     realExpenseTable, realExpenseTableHead = self.readPlanExpenses()
    #     allValues = realExpenseTable[:, realExpenseTableHead.index('value')].astype(float)
    #     if None in allValues:
    #         allValues = allValues[allValues != np.array(None)]
    #     totalVal = sum(allValues)
    #
    #     colTableName = realExpenseTable[:, realExpenseTableHead.index('name')]
    #     labels = []
    #     sizes = []
    #     for table in np.unique(colTableName):
    #         indx = np.where(realExpenseTable[:, realExpenseTableHead.index('name')]==table)
    #         smallArray = realExpenseTable[indx]
    #         values = sum(smallArray[:, realExpenseTableHead.index('value')].astype(float))
    #         txt = '{} = {:.2f}'.format(table, values)
    #         labels.append(txt)
    #         size = (values/totalVal)*100
    #         sizes.append(size)
    #
    #     fig1, ax1 = plt.subplots()
    #     ax1.pie(sizes, labels=labels, autopct='%1.2f%%', startangle=90)
    #     ax1.axis('equal')
    #     plt.legend(title='Total: {:.2f}'.format(totalVal))
    #
    #     plt.show()
    #
    # def plotGraf(self):
    #     #print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     realExpenseTable, realExpenseTableHead = self.readPlanExpenses()
    #     planIncomeTable, planIncomeTableHead = self.readPlanIncome()
    #     x_exp = []
    #     y_exp = []
    #     for date in np.unique(realExpenseTable[:, realExpenseTableHead.index('payDay')]):
    #         indx = np.where(realExpenseTable[:, realExpenseTableHead.index('payDay')] == date)
    #         arr = realExpenseTable[indx, realExpenseTableHead.index('value')].astype(float)
    #         x_exp.append(date)
    #         y_exp.append(abs(sum(arr[0])))
    #
    #     x_inc = []
    #     y_inc = []
    #     for date in np.unique(planIncomeTable[:, planIncomeTableHead.index('payDay')]):
    #         indx = np.where(planIncomeTable[:, planIncomeTableHead.index('payDay')] == date)
    #         arr = planIncomeTable[indx, planIncomeTableHead.index('value')].astype(float)
    #         x_inc.append(date)
    #         y_inc.append(abs(sum(arr[0])))
    #
    #     fig1, ax1 = plt.subplots()
    #     ax1.plot(x_exp, y_exp)
    #     ax1.plot(x_inc, y_inc)
    #     # plt.setp(plt.get_xticklabels(), rotation=30, ha="right")
    #     fig1.autofmt_xdate()
    #     plt.grid()
    #     plt.show()
    #


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

    #todo erase traces