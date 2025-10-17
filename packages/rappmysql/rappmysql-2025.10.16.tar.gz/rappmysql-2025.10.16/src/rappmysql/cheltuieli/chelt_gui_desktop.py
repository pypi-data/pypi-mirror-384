import sys
import os
import traceback
import decimal
import datetime as dt
from datetime import datetime, timedelta
import time
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtCore import *
# import sip
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas,
                                                NavigationToolbar2QT as NavigationToolbar)
import chelt_plan
from chelt_plan import CheltuieliPlanificate, Income, CheltuieliReale, CheltPlanVSReal, CheltApp
from rappmysql.mruser.myusers import Users
from rappmysql.mruser.myusers import DB_Connection as users_db_connection
from rappmysql.cheltuieli.chelt_plan import DB_Connection as chelt_db_connection
from rappmysql.mysqlquerys import connect
import rappmysql

compName = os.getenv('COMPUTERNAME')


class MyApp(QMainWindow):
    def __init__(self, users_db, chelt_db):
        super(MyApp, self).__init__()

        self.users_db_connection = users_db
        self.chelt_db_connection = chelt_db

        path2src, pyFileName = os.path.split(__file__)
        uiFileName = 'chelt_plan.ui'
        path2GUI = os.path.join(path2src, 'GUI', uiFileName)
        Ui_MainWindow, QtBaseClass = uic.loadUiType(path2GUI)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.conf = connect.Config(rappmysql.ini_chelt)
        self.setWindowTitle('{}'.format(self.conf.credentials['database']))

        self.user = None
        self.app = None
        # self.app_without_logged_user = Users(None, rappmysql.ini_users)

        self.ui.GB_when_loged.setVisible(False)
        self.ui.GB_user_options.setVisible(False)

        # self.prepare_login_window()
        fig = Figure()
        self.add_plots(fig)

        self.ui.PB_login.clicked.connect(self.login_user)
        self.ui.DE_pay_day.setCalendarPopup(True)
        self.ui.PB_export_profile.clicked.connect(self.export_full_profile)
        self.ui.PB_import_profile.clicked.connect(self.import_profile)
        self.ui.PB_DeleteProfile.clicked.connect(self.delete_profile)
        self.ui.PB_fire_req.clicked.connect(self.populate_current_tab_widget)
        self.ui.CBMonths.currentIndexChanged.connect(self.populateDatesInterval)
        self.ui.CB_next_x_days.currentIndexChanged.connect(self.populateDatesInterval)
        self.ui.SB_year.valueChanged.connect(self.populateDatesInterval)
        self.ui.planed_vs_realUnplanned_real_expenses.horizontalHeader().sectionClicked.connect(self.sortUnplanned_real)
        self.ui.planed_vs_realTable.horizontalHeader().sectionClicked.connect(self.sortPlaned_vs_realTable)
        # self.ui.PB_plotTablePie.clicked.connect(self.plotTablePie)
        # self.ui.PB_plotNamePie.clicked.connect(self.plotNamePie)
        # self.ui.PB_Plot.clicked.connect(self.plotGraf)
        self.ui.PB_add_one_time_transactions.clicked.connect(self.add_to_one_time_transactions)
        self.ui.PBComp.clicked.connect(self.compare_real_2plan)
        self.ui.pbImportCSV.clicked.connect(self.importCSV)
        self.ui.PB_backup_planned_expenses.clicked.connect(self.backup_chelt_planned)
        self.ui.TW_main_user_interface.currentChanged.connect(self.populate_current_tab_widget)
        self.ui.CBOrigTableHead.stateChanged.connect(self.populate_current_tab_widget)
        self.ui.CB_exclude_N26.stateChanged.connect(self.populate_current_tab_widget)
        self.ui.CB_hide_planned_but_not_found.stateChanged.connect(self.populate_current_tab_widget)
        self.ui.CB_hide_planned_and_found_in_real_expenses_table.stateChanged.connect(self.populate_current_tab_widget)
        self.ui.CB_hide_unplanned_real_expenses.stateChanged.connect(self.populate_current_tab_widget)
        # self.ui.CB_allHideIntercontotrans.stateChanged.connect(lambda: (self.prepareTabPlanned(), self.prepareTabReal(), self.prepareTabPlanVsReal()))
        self.ui.CB_allHideIntercontotrans.stateChanged.connect(self.populate_current_tab_widget)

        self.ui.planTable.horizontalHeader().sectionClicked.connect(self.sortTable)
        self.ui.realTable.horizontalHeader().sectionClicked.connect(self.sortTable)
        self.ui.TWsskm.horizontalHeader().sectionClicked.connect(self.sortTable)
        self.ui.TWdeubnk.horizontalHeader().sectionClicked.connect(self.sortTable)
        self.ui.TWn26.horizontalHeader().sectionClicked.connect(self.sortTable)
        self.ui.realTable.horizontalHeader().sectionDoubleClicked.connect(self.setFilter)
        self.ui.TWsskm.horizontalHeader().sectionDoubleClicked.connect(self.setFilter)
        self.ui.TWdeubnk.horizontalHeader().sectionDoubleClicked.connect(self.setFilter)
        self.ui.TWn26.horizontalHeader().sectionDoubleClicked.connect(self.setFilter)
        self.ui.RB_show_table.toggled.connect(self.populate_current_tab_widget)
        self.ui.RB_show_tree.toggled.connect(self.populate_current_tab_widget)

        self.ui.planTable.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.planTable.horizontalHeader().customContextMenuRequested.connect(self.contextMenu_plot_cols_from_table)
        self.ui.planed_vs_realUnplanned_real_expenses.horizontalHeader().setContextMenuPolicy(
            QtCore.Qt.CustomContextMenu)
        self.ui.planed_vs_realUnplanned_real_expenses.horizontalHeader().customContextMenuRequested.connect(
            self.contextMenu_plot_cols_from_table)
        self.ui.realTable.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.realTable.horizontalHeader().customContextMenuRequested.connect(self.contextMenu_plot_cols_from_table)
        self.ui.planed_vs_realTable.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.planed_vs_realTable.horizontalHeader().customContextMenuRequested.connect(
            self.contextMenu_plot_cols_from_table)

        if compName == 'DESKTOP-5HHINGF' or compName == 'MPCC6995':
            self.ui.LE_user_name.setText('radu')
            self.ui.LE_user_pass.setText('9876')
            # self.login_user()
            # zipFile = r"C:\_Development\Diverse\pypi\radu\cheltuieli\src\cheltuieli\static\backup_profile\000000001\2024_12_18__14_20_50_000000001.zip"
            # self.app_users.import_profile_with_files(zipFile, import_files=False)
            # self.login_user()

    def delete_profile(self):
        message = "Are you sure you want to delete the profile?"
        buttonReply = QMessageBox.question(self, 'Deletion Prompt', message,
                                           QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if buttonReply == QMessageBox.Yes:
            self.close()
            # time.sleep(3)
            self.user.chelt_app.erase_chelt_traces()
        else:
            return

    def export_full_profile(self):
        # expName, _ = QFileDialog.getSaveFileName(self, "Save file", "", "File (*.zip)")
        # expDir = QFileDialog.getExistingDirectory()
        # print(expDir)
        # if expName:
        if self.ui.CB_export_profile_with_files.isChecked():
            self.user.chelt_app.export_profile(output_dir=None, export_files=True)
        else:
            self.user.chelt_app.export_profile(output_dir=None, export_files=False)

    def backup_chelt_planned(self):
        self.user.chelt_app.export_chelt_plan_sql()

    def import_profile(self):
        import_files = self.ui.CB_import_profile_with_files.isChecked()
        zip_or_sql_file, _ = QFileDialog.getOpenFileName(self, "Open file", "", "File (*.zip;*.sql)")
        if zip_or_sql_file:
            if zip_or_sql_file.endswith('.zip'):
                zipFile = zip_or_sql_file
                if not self.user:
                    self.app_without_logged_user.import_profile_with_files(zipFile, import_files=import_files)
                    return
                self.user.chelt_app.import_profile(zipFile, import_files=import_files)
                self.login_user()
            elif zip_or_sql_file.endswith('.sql'):
                sqlFile = zip_or_sql_file
                if not self.user:
                    self.app_without_logged_user.import_profile_without_files(sqlFile)
                    return
                self.user.import_profile_without_files(sqlFile)
                self.login_user()

    def login_user(self):
        user_name = self.ui.LE_user_name.text()
        password = self.ui.LE_user_pass.text()

        self.user = Users(user_name=user_name,
                          users_table=self.users_db_connection.users_table,
                          user_apps_table=self.users_db_connection.user_apps_table)

        if self.user.verify_password(password):
            self.ui.GB_when_loged.setVisible(True)
            self.ui.GB_user_options.setVisible(True)
            # self.ui.CB_export_profile_with_files.setVisible(True)
            # self.ui.PB_DeleteProfile.setVisible(True)

            self.user.chelt_app = CheltApp(user_id=self.user.id,
                                           chelt_db=self.chelt_db_connection.chelt_db,
                                           chelt_plan=self.chelt_db_connection.chelt_plan,
                                           yearly_plan=self.chelt_db_connection.yearly_plan,
                                           myAccountsTable=self.chelt_db_connection.myAccountsTable,
                                           income_table=self.chelt_db_connection.income_table)

            if self.user.chelt_app.has_cheltuieli_planned:
                self.app_planned = CheltuieliPlanificate(chelt_db=self.chelt_db_connection.chelt_db,
                                                         chelt_plan=self.chelt_db_connection.chelt_plan,
                                                         yearly_plan=self.chelt_db_connection.yearly_plan)
            else:
                self.ui.GB_when_loged.setVisible(False)
                return
            if self.user.chelt_app.has_planned_income:
                self.app_planned_income = Income(income_table=self.chelt_db_connection.income_table)

            if self.user.chelt_app.has_cheltuieli_real:
                self.app_reale = CheltuieliReale(chelt_db=self.chelt_db_connection.chelt_db,
                                                 myAccountsTable=self.chelt_db_connection.myAccountsTable,
                                                 imported_csv=self.chelt_db_connection.imported_csv,
                                                 chelt_plan=self.chelt_db_connection.chelt_plan,
                                                 plan_vs_real=self.chelt_db_connection.plan_vs_real,
                                                 knowntrans=self.chelt_db_connection.knowntrans,
                                                 sskm=self.chelt_db_connection.sskm,
                                                 deubnk=self.chelt_db_connection.deubnk,
                                                 n26=self.chelt_db_connection.n26)
            else:
                # widget = self.ui.GB_when_loged
                # tabs = widget.findChildren(QTabWidget)
                # print('no_real', tabs)
                # for i, tab in enumerate(tabs):
                #     print(tab)
                #     print(tab.tabText(i))
                tabWidget = self.ui.TW_main_user_interface
                for i in range(tabWidget.count()):
                    if i == 0:
                        continue
                    # print(tabWidget.tabText(i))
                    tabWidget.setTabEnabled(i, False)
            self.populateCBConto()
            self.populateCBMonths()
            self.populateDatesInterval()
            self.populate_current_tab_widget()
        # else:
        #     print('User not registered in database')

    def populate_current_tab_widget(self):
        selectedStartDate = self.ui.DEFrom.date().toPyDate()
        selectedEndDate = self.ui.DEBis.date().toPyDate()
        currentConto = self.ui.cbActiveConto.currentText()
        sql_orig_table_head = self.ui.CBOrigTableHead.isChecked()
        hideintercontotrans = self.ui.CB_allHideIntercontotrans.isChecked()
        self.defaultFilter = True
        self.filterList = []

        chelt_type = self.ui.TW_main_user_interface.tabText(self.ui.TW_main_user_interface.currentIndex())
        if chelt_type == 'Planned Expenses':
            self.app_planned.prepareTablePlan(currentConto, selectedStartDate, selectedEndDate, hideintercontotrans)
            if sql_orig_table_head:
                tableHead = self.app_planned.tableHead
                table = self.app_planned.expenses
            else:
                tableHead = self.app_planned.displayExpensesTableHead
                tableHead, table = chelt_plan.convert_to_display_table(self.app_planned.tableHead,
                                                                       self.app_planned.expenses,
                                                                       self.app_planned.displayExpensesTableHead)
            qt_table_widget = self.ui.planTable
            if self.app_planned.expenses.shape != (1, 0):
                # self.populateExpensesPlan(displayExpensesTableHead)
                if self.ui.RB_show_table.isChecked():
                    self.populateTable(qt_table_widget, tableHead, table)
                    self.ui.TWmnthVSIrreg.setVisible(False)
                    self.ui.planTable.setVisible(True)
                elif self.ui.RB_show_tree.isChecked():
                    self.populateTree()
                    self.ui.planTable.setVisible(False)
                    self.ui.TWmnthVSIrreg.setVisible(True)
                self.populate_expenses_summary()
                self.prep_2Dplot()
            # self.prepareTabPlanned()
        elif chelt_type == 'Planned Income':
            self.app_planned_income.prepareTablePlan(currentConto, selectedStartDate, selectedEndDate)
            if sql_orig_table_head:
                tableHead = self.app_planned_income.tableHead
                table = self.app_planned_income.income
            else:
                tableHead = self.app_planned.displayExpensesTableHead
                tableHead, table = chelt_plan.convert_to_display_table(self.app_planned_income.tableHead,
                                                                       self.app_planned_income.income,
                                                                       self.app_planned_income.displayExpensesTableHead)
            qt_table_widget = self.ui.planTableIncome
            if self.app_planned_income.income.shape != (1, 0):
                self.populateTable(qt_table_widget, tableHead, table)
                self.ui.TWmnthVSIrreg.setVisible(False)
                self.ui.planTable.setVisible(True)
                self.populate_income_summary()
            #     self.prep_2Dplot()
            # self.prepareTabPlanned()
        elif chelt_type == 'Real Expenses':
            qt_table_widget = self.ui.realTable
            self.app_reale.prepareTableReal_new(currentConto, selectedStartDate, selectedEndDate, hideintercontotrans)
            # print('&&&&', self.app_reale.realExpenses.shape)
            if self.app_reale.realExpenses.shape[1] == 0:
                message = "There were no rows found in interval"
                QMessageBox.warning(self, 'Missing Data', message, QMessageBox.Ok)
                return
            if sql_orig_table_head:
                tableHead = self.app_reale.expensesTableReal.columnsNames
                table = self.app_reale.realExpenses
            else:
                tableHead, table = chelt_plan.convert_to_display_table(self.app_reale.plan_vs_real.columnsNames,
                                                                       self.app_reale.realExpenses,
                                                                       self.app_reale.displayRealTableHead)
            self.populateTable(qt_table_widget, tableHead, table)
            self.populate_table_dates()
            # self.populateDatesInterval()
            # self.prepareTabReal()
        elif chelt_type == 'Real Income':
            qt_table_widget = self.ui.realTableIncome
            self.app_reale.prepareTableReal_new(currentConto, selectedStartDate, selectedEndDate, hideintercontotrans)
            if self.app_reale.realIncome.shape[1] == 0:
                message = "There were no rows found in interval"
                QMessageBox.warning(self, 'Missing Data', message, QMessageBox.Ok)
                return
            if sql_orig_table_head:
                tableHead = self.app_reale.plan_vs_real.columnsNames
                table = self.app_reale.realIncome
            else:
                tableHead, table = chelt_plan.convert_to_display_table(self.app_reale.plan_vs_real.columnsNames,
                                                                       self.app_reale.realIncome,
                                                                       self.app_reale.displayRealTableHead)
            self.populateTable(qt_table_widget, tableHead, table)
            self.populate_table_dates()
            # self.populateDatesInterval()
            # self.prepareTabReal()
        elif chelt_type == 'PlanVsReal':
            puffer_days_to_plann = self.ui.SB_puffer_days_to_plann.value()
            self.app_reale.prepareTableReal_new(currentConto, selectedStartDate, selectedEndDate, hideintercontotrans)
            if self.app_reale.realExpenses.shape[1] == 0:
                message = "There were no rows found in interval"
                QMessageBox.warning(self, 'Missing Data', message, QMessageBox.Ok)
                return

            self.planvsReal = CheltPlanVSReal(chelt_db=self.chelt_db_connection.chelt_db,
                                              chelt_plan=self.chelt_db_connection.chelt_plan,
                                              yearly_plan=self.chelt_db_connection.yearly_plan,
                                              myAccountsTable=self.chelt_db_connection.myAccountsTable,
                                              imported_csv=self.chelt_db_connection.imported_csv,
                                              plan_vs_real=self.chelt_db_connection.plan_vs_real,
                                              knowntrans=self.chelt_db_connection.knowntrans,
                                              sskm=self.chelt_db_connection.sskm,
                                              deubnk=self.chelt_db_connection.deubnk,
                                              n26=self.chelt_db_connection.n26,
                                              currentConto=currentConto,
                                              selectedStartDate=selectedStartDate,
                                              selectedEndDate=selectedEndDate,
                                              hideintercontotrans=hideintercontotrans)
            self.planvsReal.find_planned_in_real_expenses_table(hideintercontotrans, puffer_days_to_plann)
            self.planvsReal.find_unplanned_real_expenses(hideintercontotrans, puffer_days_to_plann)
            if self.planvsReal.found_payments_from_planned.shape[0] == 1 and \
                    self.planvsReal.not_found_payments_from_planned.shape[0] == 1 and \
                    self.planvsReal.unplanned_real_expenses.shape[0] == 1:
                return

            min_buchungstag, max_buchungstag = self.app_reale.get_buchungstag_interval(currentConto)
            if min_buchungstag and max_buchungstag:
                self.ui.DE_Buchungstag_min_plvsre.setDate(min_buchungstag)
                self.ui.DE_Buchungstag_max_plvsre.setDate(max_buchungstag)

            if not self.ui.CB_hide_planned_and_found_in_real_expenses_table.isChecked():
                qt_table_planed_vs_realTable = self.ui.planed_vs_realTable
                if sql_orig_table_head:
                    tableHead, table = list(self.planvsReal.found_payments_from_planned[0]), \
                                       self.planvsReal.found_payments_from_planned[1:]
                else:
                    tableHead, table = list(self.planvsReal.found_payments_from_planned_display_table[0]), \
                                       self.planvsReal.found_payments_from_planned_display_table[1:]
                self.populateTable(qt_table_planed_vs_realTable, tableHead, table)
            else:
                self.ui.groupBox_18.setVisible(False)

            if not self.ui.CB_hide_planned_but_not_found.isChecked():
                self.ui.groupBox_19.setVisible(True)
                qt_table_planed_vs_realTable_notFound = self.ui.planed_vs_realTable_notFound
                if sql_orig_table_head:
                    tableHead, table = list(self.planvsReal.not_found_payments_from_planned[0]), \
                                       self.planvsReal.not_found_payments_from_planned[1:]
                else:
                    tableHead, table = list(self.planvsReal.not_found_payments_from_planned_display_table[0]), \
                                       self.planvsReal.not_found_payments_from_planned_display_table[1:]
                self.populateTable(qt_table_planed_vs_realTable_notFound, tableHead, table)
            else:
                self.ui.groupBox_19.setVisible(False)

            if not self.ui.CB_hide_unplanned_real_expenses.isChecked():
                qt_table_planed_vs_realTable_notFound = self.ui.planed_vs_realUnplanned_real_expenses
                if sql_orig_table_head:
                    tableHead, table = list(self.planvsReal.unplanned_real_expenses[0]), \
                                       self.planvsReal.unplanned_real_expenses[1:]
                    if self.ui.CB_exclude_N26.isChecked():
                        tableHead, table = list(self.planvsReal.unplanned_real_expenses_without_N26[0]), \
                                           self.planvsReal.unplanned_real_expenses_without_N26[1:]
                else:
                    tableHead, table = list(self.planvsReal.unplanned_real_expenses[0]), \
                                       self.planvsReal.unplanned_real_expenses[1:]
                    if self.ui.CB_exclude_N26.isChecked():
                        tableHead, table = list(self.planvsReal.unplanned_real_expenses_without_N26[0]), \
                                           self.planvsReal.unplanned_real_expenses_without_N26[1:]
                    tableHead, table = chelt_plan.convert_to_display_table(tableHead,
                                                                           table,
                                                                           self.planvsReal.displayPlanVsRealTableHead)

                self.populateTable(qt_table_planed_vs_realTable_notFound, tableHead, table)
            else:
                self.ui.groupBox_20.setVisible(False)
            self.populate_planvsReal_summary()
        elif chelt_type == 'sskm':
            qt_table_widget = self.ui.TWsskm
            matches = [('Buchungstag', (selectedStartDate, selectedEndDate))]
            table = self.app_reale.sskm.filterRows(matches)
            table = np.atleast_2d(table)
            table_head = self.app_reale.sskm.columnsNames
            if table.shape[1] == 0:
                message = "There were no rows found in interval"
                QMessageBox.warning(self, 'Missing Data', message, QMessageBox.Ok)
                return
            self.populateTable(qt_table_widget, table_head, table)
        elif chelt_type == 'deubnk':
            # self.preparedeubnk()
            qt_table_widget = self.ui.TWdeubnk
            matches = [('Buchungstag', (selectedStartDate, selectedEndDate))]
            table = self.app_reale.deubnk.filterRows(matches)
            table = np.atleast_2d(table)
            table_head = self.app_reale.deubnk.columnsNames
            self.populateTable(qt_table_widget, table_head, table)
        elif chelt_type == 'n26':
            # self.preparen26()
            qt_table_widget = self.ui.TWn26
            matches = [('Buchungstag', (selectedStartDate, selectedEndDate))]
            table = self.app_reale.n26.filterRows(matches)
            table = np.atleast_2d(table)
            # print('ÖÖÖÖ', table.shape)
            table_head = self.app_reale.n26.columnsNames
            self.populateTable(qt_table_widget, table_head, table)

    def populateTable(self, qt_table_widget, tableHead, table):
        qt_table_widget.parent().setVisible(True)
        if table.shape[0] == 0:
            qt_table_widget.parent().setVisible(False)
            return
        qt_table_widget.setColumnCount(len(tableHead))
        qt_table_widget.setHorizontalHeaderLabels(tableHead)
        qt_table_widget.setRowCount(table.shape[0])
        for col in range(table.shape[1]):
            for row in range(table.shape[0]):
                if isinstance(table[row, col], int) or isinstance(table[row, col], float):
                    item = QTableWidgetItem()
                    item.setData(QtCore.Qt.DisplayRole, table[row, col])
                elif isinstance(table[row, col], decimal.Decimal):
                    val = float(table[row, col])
                    item = QTableWidgetItem()
                    item.setData(QtCore.Qt.DisplayRole, val)
                else:
                    item = QTableWidgetItem(str(table[row, col]))
                qt_table_widget.setItem(row, col, item)
        self.ui.LE_table_total_trans.setText(str(table.shape[0]))
        if 'value' in tableHead:
            indxColVal = tableHead.index('value')
        elif 'Betrag' in tableHead:
            indxColVal = tableHead.index('Betrag')
        elif 'Amount' in tableHead:
            indxColVal = tableHead.index('Amount')
        elif 'Debit' in tableHead:
            indxColVal = tableHead.index('Debit')
        elif 'uberweisung' in tableHead:
            indxColVal = tableHead.index('uberweisung')
        # print('***table', type(table), table.shape)
        if table.shape[1] > 0:
            totalValue = sum(table[:, indxColVal].astype(float))
            totalValue = round(totalValue, 2)
            self.ui.LE_table_total_value.setText(str(totalValue))
        header = qt_table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

    def populate_expenses_summary(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.ui.LEtotalNoOfTransactions.setText(str(self.app_planned.tot_no_of_expenses))
        self.ui.LEtotalValue.setText(str(self.app_planned.tot_val_of_expenses))
        self.ui.LEnoOfMonthly.setText(str(self.app_planned.tot_no_of_monthly_expenses))
        self.ui.LEtotalMonthly.setText(str(self.app_planned.tot_val_of_monthly_expenses))
        self.ui.LEnoOfIrregular.setText(str(self.app_planned.tot_no_of_irregular_expenses))
        self.ui.LEirregular.setText(str(self.app_planned.tot_val_of_irregular_expenses))

    def populate_planvsReal_summary(self):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if self.ui.CB_exclude_N26.isChecked():
            self.ui.LE_sum_of_unplanned_real_expenses.setText(
                str(self.planvsReal.sum_of_unplanned_real_expenses_without_n26))
        else:
            self.ui.LE_sum_of_unplanned_real_expenses.setText(str(self.planvsReal.sum_of_unplanned_real_expenses))
        self.ui.LE_total_expenses_planned.setText(str(self.planvsReal.sum_planned))
        self.ui.LE_total_expenses_realised.setText(str(self.planvsReal.sum_realised))
        self.ui.LE_total_no_of_transactions_planned.setText(str(self.planvsReal.sum_realised_from_planned_found))
        self.ui.LE_sum_realised_from_planned_found_in_interval.setText(
            str(self.planvsReal.sum_realised_from_planned_found_in_interval))
        self.ui.LE_planned_but_not_realised.setText(
            str(self.planvsReal.sum_realised_from_not_found_payments_from_planned))
        # self.ui.LE_repeated_rows.setText(str(rows_more_than_one_time))
        self.ui.LE_sum_of_unplanned_real_expenses_without_n26.setText(
            str(self.planvsReal.sum_of_unplanned_real_expenses_without_n26))
        self.ui.LE_sum_of_unplanned_real_expenses_only_n26.setText(
            str(self.planvsReal.sum_of_unplanned_real_expenses_only_n26))
        self.ui.LE_sum_of_unplanned_real_expenses_no_category.setText(
            str(self.planvsReal.sum_of_unplanned_real_expenses_no_category))
        self.ui.LE_sum_of_unplanned_real_expenses_with_category.setText(
            str(self.planvsReal.sum_of_unplanned_real_expenses_with_category))

    def importCSV(self):
        print(sys._getframe().f_code.co_name)
        inpFile, _ = QFileDialog.getOpenFileName(None, 'Select .csv file', '', 'CSV files (*.csv)')
        if not inpFile:
            return
        currentConto = self.ui.cbActiveConto.currentText()
        if currentConto == 'all':
            message = 'please select the conto'
            QMessageBox.warning(self, 'Inconsistent Data', message, QMessageBox.Ok)
            return
        # print(inpFile)
        # print(currentConto)
        self.app_reale.import_CSV_new(currentConto, inpFile)

    def delete_items_of_layout(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        layout_grupa = self.gb_available_databases.layout()
        if layout_grupa is not None:
            while layout_grupa.count():
                item = layout_grupa.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                # else:
                #     delete_items_of_layout(item.layout())
            # sip.delete(layout_grupa)

    def compare_real_2plan(self):
        print(sys._getframe().f_code.co_name)
        # self.app_reale.compare2plan()
        self.app_reale.find_chelt_plan_rows_in_banks_tables_and_write_to_plan_vs_real_table()
        self.app_reale.find_knowntrans_in_banks_tables_and_write_to_plan_vs_real_table()

    # def totals_PlanVsReal(self, rows_more_than_one_time):
    #     print(sys._getframe().f_code.co_name)
    #     self.ui.LE_total_no_of_transactions_planned.setText(str(self.planvsReal.no_of_transactions_planned))
    #     self.ui.LE_total_expenses_realised.setText(str(self.planvsReal.sum_realised_from_planned_found))
    #
    #     self.ui.LE_no_of_unplanned_real_expenses.setText(str(self.planvsReal.no_of_unplanned_real_expenses))
    #     self.ui.LE_sum_of_unplanned_real_expenses.setText(str(self.planvsReal.sum_of_unplanned_real_expenses))

    def populate_table_dates(self):
        print(sys._getframe().f_code.co_name)
        self.ui.TW_real_table_dates.clear()
        self.ui.TW_real_table_dates.setRowCount(len(self.app_reale.real_table_dates))
        self.ui.TW_real_table_dates.setColumnCount(3)
        self.ui.TW_real_table_dates.setHorizontalHeaderLabels(['Bank', 'From', 'To'])

        for row, (bank, dates) in enumerate(self.app_reale.real_table_dates.items()):
            # print('****',row, bank, dates)
            date_from, date_to = dates[0], dates[1]
            itemBank = QTableWidgetItem(str(bank))
            self.ui.TW_real_table_dates.setItem(row, 0, itemBank)
            itemdate_from = QTableWidgetItem(str(date_from))
            self.ui.TW_real_table_dates.setItem(row, 1, itemdate_from)
            itemdate_to = QTableWidgetItem(str(date_to))
            self.ui.TW_real_table_dates.setItem(row, 2, itemdate_to)

    def populateTableIncome(self, table):
        print(sys._getframe().f_code.co_name)
        self.ui.realTableIncome.setColumnCount(len(self.app_reale.plan_vs_real.columnsNames))
        self.ui.realTableIncome.setHorizontalHeaderLabels(self.app_reale.plan_vs_real.columnsNames)
        self.ui.realTableIncome.setRowCount(table.shape[0])
        for col in range(table.shape[1]):
            for row in range(table.shape[0]):
                if isinstance(table[row, col], int) or isinstance(table[row, col], float):
                    item = QTableWidgetItem()
                    item.setData(QtCore.Qt.DisplayRole, table[row, col])
                elif isinstance(table[row, col], decimal.Decimal):
                    val = float(table[row, col])
                    item = QTableWidgetItem()
                    item.setData(QtCore.Qt.DisplayRole, val)
                else:
                    item = QTableWidgetItem(str(table[row, col]))
                self.ui.realTableIncome.setItem(row, col, item)

        totalVal = 0
        if table.shape[1] > 0:
            allValues = table[:, self.app_reale.plan_vs_real.columnsNames.index('Betrag')].astype(float)
            if None in allValues:
                allValues = allValues[allValues != np.array(None)]
            totalVal = sum(allValues)
        self.ui.LEtotalNoIncomeTrans.setText(str(len(table)))
        self.ui.LEtotalIncomeValue.setText(str(totalVal))

    def totals_r(self):
        print(sys._getframe().f_code.co_name)
        if self.ui.LEtotalNoExpensesTrans.text():
            expensesTrans = int(self.ui.LEtotalNoExpensesTrans.text())
        else:
            expensesTrans = 0
        if self.ui.LEtotalNoIncomeTrans.text():
            incomeTrans = int(self.ui.LEtotalNoIncomeTrans.text())
        else:
            incomeTrans = 0

        if self.ui.LEtotalExpensesValue.text():
            expenses = float(self.ui.LEtotalExpensesValue.text())
        else:
            expenses = 0
        if self.ui.LEtotalIncomeValue.text():
            income = float(self.ui.LEtotalIncomeValue.text())
        else:
            income = 0

        trans = expensesTrans + incomeTrans
        total = expenses + income
        print('trans', trans)
        print('total', total)
        # self.ui.LEtotalNoOfRealTransactions.setText(str(trans))
        # self.ui.LEtotalRealValue.setText(str(total))

    def populateCBMonths(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.ui.CBMonths.addItem('month')
        months = [dt.date(2000, m, 1).strftime('%B') for m in range(1, 13)]
        for month in months:
            self.ui.CBMonths.addItem(month)

        self.ui.SB_year.setValue(datetime.now().year)

    def populateCBConto(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.ui.cbActiveConto.addItem('all')
        self.ui.cbActiveConto.addItems(self.app_planned.myContos)
        self.ui.cballContos.addItems(self.app_planned.myContos)

    def populateDatesInterval(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        chelt_type = self.ui.TW_main_user_interface.tabText(self.ui.TW_main_user_interface.currentIndex())
        if chelt_type == "Planned Expenses":
            # startDate, lastDayOfMonth = chelt_plan.default_interval()
            startDate, lastDayOfMonth = self.app_planned.default_interval()
        else:
            startDate, lastDayOfMonth = self.app_reale.default_interval()

        if self.ui.CBMonths.currentText() != 'month':
            year = int(self.ui.SB_year.value())
            startDate, lastDayOfMonth = chelt_plan.get_monthly_interval(self.ui.CBMonths.currentText(), year)

        if self.ui.CB_next_x_days.currentText() != '':
            # print(self.ui.CB_next_x_days.currentText())
            txt = self.ui.CB_next_x_days.currentText()
            days = txt.strip(' days')
            days = int(days)
            lastDayOfMonth = chelt_plan.calculate_today_plus_x_days(days)

        self.ui.DEFrom.setDate(startDate)
        self.ui.DEBis.setDate(lastDayOfMonth)

        self.ui.DEFrom.setCalendarPopup(True)
        self.ui.DEBis.setCalendarPopup(True)

    def populateTree(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.ui.TWmnthVSIrreg.clear()
        if self.ui.CBOrigTableHead.isChecked():
            tableHead = self.app_planned.tableHead.copy()
            tableHead.insert(0, 'freq')
            self.ui.TWmnthVSIrreg.setHeaderLabels(tableHead)
        else:
            self.ui.TWmnthVSIrreg.setHeaderLabels(['freq', 'name', 'value'])
        monthly_level = QTreeWidgetItem(self.ui.TWmnthVSIrreg)
        monthly_level.setText(0, 'Monthly')
        irregular_level = QTreeWidgetItem(self.ui.TWmnthVSIrreg)
        irregular_level.setText(0, 'Irregular')
        monthlyIndx = np.where(self.app_planned.expenses[:, self.app_planned.tableHead.index('freq')] == 1)
        monthly = self.app_planned.expenses[monthlyIndx]
        for mnth in monthly:
            mnth_item_level = QTreeWidgetItem(monthly_level)
            if self.ui.CBOrigTableHead.isChecked():
                for iii, col in enumerate(mnth):
                    mnth_item_level.setText(iii + 1, str(col))
            else:
                mnth_item_level.setText(1, mnth[self.app_planned.tableHead.index('name')])
                mnth_item_level.setText(2, str(round(mnth[self.app_planned.tableHead.index('value')])))

        totalMonthly = self.app_planned.expenses[monthlyIndx, self.app_planned.tableHead.index('value')][0]
        monthly_level.setText(1, 'Total')
        monthly_level.setText(2, str(round(sum(totalMonthly), 2)))

        irregIndx = np.where(self.app_planned.expenses[:, self.app_planned.tableHead.index('freq')] != 1)
        irregular = self.app_planned.expenses[irregIndx]
        for irr in irregular:
            irr_item_level = QTreeWidgetItem(irregular_level)
            if self.ui.CBOrigTableHead.isChecked():
                for iii, col in enumerate(irr):
                    irr_item_level.setText(iii + 1, str(col))
            else:
                irr_item_level.setText(1, irr[self.app_planned.tableHead.index('name')])
                irr_item_level.setText(2, str(round(irr[self.app_planned.tableHead.index('value')], 2)))

        totalIrreg = self.app_planned.expenses[irregIndx, self.app_planned.tableHead.index('value')][0]
        irregular_level.setText(1, 'Total')
        irregular_level.setText(2, str(round(sum(totalIrreg), 2)))

    def populate_income_summary(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.ui.LE_total_netto.setText(str(self.app_planned_income.netto))
        self.ui.LE_total_taxes.setText(str(self.app_planned_income.taxes))
        self.ui.LE_total_brutto.setText(str(self.app_planned_income.brutto))
        self.ui.LE_salary_uberweisung.setText(str(self.app_planned_income.salary_uberweisung))
        self.ui.LE_salary_abzuge.setText(str(self.app_planned_income.salary_abzuge))
        self.ui.LE_salary_netto.setText(str(self.app_planned_income.salary_netto))
        self.ui.LE_salary_gesetzliche_abzuge.setText(str(self.app_planned_income.salary_gesetzliche_abzuge))
        self.ui.LE_salary_brutto.setText(str(self.app_planned_income.salary_brutto))

    def sortUnplanned_real(self, logical_index):
        print(sys._getframe().f_code.co_name)
        header = self.ui.planed_vs_realUnplanned_real_expenses.horizontalHeader()
        order = Qt.DescendingOrder
        if not header.isSortIndicatorShown():
            header.setSortIndicatorShown(True)
        elif header.sortIndicatorSection() == logical_index:
            order = header.sortIndicatorOrder()
        header.setSortIndicator(logical_index, order)
        self.ui.planed_vs_realUnplanned_real_expenses.sortItems(logical_index, order)

    def sortPlaned_vs_realTable(self, logical_index):
        print(sys._getframe().f_code.co_name)
        header = self.ui.planed_vs_realTable.horizontalHeader()
        order = Qt.DescendingOrder
        if not header.isSortIndicatorShown():
            header.setSortIndicatorShown(True)
        elif header.sortIndicatorSection() == logical_index:
            order = header.sortIndicatorOrder()
        header.setSortIndicator(logical_index, order)
        self.ui.planed_vs_realTable.sortItems(logical_index, order)

    # def readPlanExpenses(self):
    #     # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     rows = self.ui.planTable.rowCount()
    #     cols = self.ui.planTable.columnCount()
    #     planExpenseTable = np.empty((rows, cols), dtype=object)
    #     planExpenseTableHead = []
    #     for row in range(rows):
    #         for column in range(cols):
    #             cell = self.ui.planTable.item(row, column)
    #             planExpenseTable[row, column] = cell.text()
    #             colName = self.ui.planTable.horizontalHeaderItem(column).text()
    #             if colName not in planExpenseTableHead:
    #                 planExpenseTableHead.append(colName)
    #
    #     return planExpenseTable, planExpenseTableHead
    #
    # def readPlanIncome(self):
    #     # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     rows = self.ui.planTableIncome.rowCount()
    #     cols = self.ui.planTableIncome.columnCount()
    #     planIncomeTable = np.empty((rows, cols), dtype=object)
    #     planIncomeTableHead = []
    #     for row in range(rows):
    #         for column in range(cols):
    #             cell = self.ui.planTableIncome.item(row, column)
    #             planIncomeTable[row, column] = cell.text()
    #             colName = self.ui.planTableIncome.horizontalHeaderItem(column).text()
    #             print('000colName', colName)
    #             if colName not in planIncomeTableHead:
    #                 planIncomeTableHead.append(colName)
    #     print('****planIncomeTableHead', planIncomeTableHead)
    #     return planIncomeTable, planIncomeTableHead

    # def plotGraf(self):
    #     # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     realExpenseTable, realExpenseTableHead = self.readPlanExpenses()
    #     planIncomeTable, planIncomeTableHead = self.readPlanIncome()
    #     print('****planIncomeTableHead', planIncomeTableHead)
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

    def add_to_one_time_transactions(self):
        name = self.ui.LE_add_name.text()
        value = float(self.ui.LE_add_value.text())
        myconto = self.ui.cballContos.currentText()

        pay_day = self.ui.DE_pay_day.date().toPyDate()
        self.app_planned.add_one_time_transactions(name, value, myconto, pay_day)

    def sortTable(self, logical_index):
        print(sys._getframe().f_code.co_name)

        chelt_type = self.ui.TW_main_user_interface.tabText(self.ui.TW_main_user_interface.currentIndex())
        if chelt_type == 'Real Expenses':
            table = self.ui.realTable
        elif chelt_type == 'Planned Expenses':
            table = self.ui.planTable
        elif chelt_type == 'sskm':
            table = self.ui.TWsskm
        elif chelt_type == 'deubnk':
            table = self.ui.TWdeubnk
        elif chelt_type == 'n26':
            table = self.ui.TWn26

        header = table.horizontalHeader()
        order = Qt.DescendingOrder
        if not header.isSortIndicatorShown():
            header.setSortIndicatorShown(True)
        elif header.sortIndicatorSection() == logical_index:
            order = header.sortIndicatorOrder()
        header.setSortIndicator(logical_index, order)
        table.sortItems(logical_index, order)

    def setFilter(self, logical_index):
        print(sys._getframe().f_code.co_name)

        chelt_type = self.ui.TW_main_user_interface.tabText(self.ui.TW_main_user_interface.currentIndex())
        if chelt_type == 'Real Expenses':
            qt_table = self.ui.realTable
            sql_table = self.app_reale.plan_vs_real
        elif chelt_type == 'Planned Expenses':
            qt_table = self.ui.planTable
            sql_table = self.app_reale.chelt_plan
        elif chelt_type == 'sskm':
            qt_table = self.ui.TWsskm
            sql_table = self.app_reale.sskm
        elif chelt_type == 'deubnk':
            qt_table = self.ui.TWdeubnk
            sql_table = self.app_reale.deubnk
        elif chelt_type == 'n26':
            qt_table = self.ui.TWn26
            sql_table = self.app_reale.n26
        # print('ÖÖÖÖÖÖÖ', qt_table.objectName())
        # print('logical_index', logical_index)
        colName = qt_table.horizontalHeaderItem(logical_index).text()
        # print('colName', colName)
        # return
        # colName = self.plan_vs_real.columnsNames[logical_index]
        colType = sql_table.get_column_type(colName)
        if colType == 'int':
            filt = FilterWindow.getIntInterval(colName)
            if not filt:
                return
            if isinstance(filt, tuple):
                minInt, maxInt = filt
                filterVals = (str(minInt), str(maxInt))
            elif isinstance(filt, str):
                filterVals = filt
            self.applyFilter(colName, filterVals)
        elif colType == 'date':
            filt = FilterWindow.getDateInterval(colName)
            if not filt:
                return
            if isinstance(filt, tuple):
                minDate, maxDate = filt
                minDate = minDate.toPyDate()
                maxDate = maxDate.toPyDate()
                filterVals = (str(minDate), str(maxDate))
            elif isinstance(filt, str):
                filterVals = filt
            self.applyFilter(colName, filterVals)
        else:
            header = qt_table.horizontalHeader()
            geom = QtCore.QRect(header.sectionViewportPosition(logical_index), 0, header.sectionSize(logical_index),
                                header.height())
            item = QLineEdit(header)
            item.setGeometry(geom)
            item.show()
            item.setFocus()
            item.editingFinished.connect(lambda: (self.applyFilter(colName, item.text(), qt_table, sql_table),
                                                  item.clear(),
                                                  item.hide(),
                                                  item.deleteLater()))

    def applyFilter(self, colName, filter, qt_table, sql_table):
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
        selectedStartDate = self.ui.DEFrom.date().toPyDate()
        selectedEndDate = self.ui.DEBis.date().toPyDate()
        match2 = ('Buchungstag', (selectedStartDate, selectedEndDate))
        self.filterList.append(match2)

        currentConto = self.ui.cbActiveConto.currentText()
        if currentConto != 'all':
            match3 = ('myconto', currentConto)
            self.filterList.append(match3)

        filtered_vals = sql_table.filterRows(self.filterList)
        filtered_vals = np.atleast_2d(filtered_vals)
        if filtered_vals.shape == (1, 0):
            filtered_vals = np.empty((0, len(sql_table.columnsNames)))

        sql_orig_table_head = self.ui.CBOrigTableHead.isChecked()
        if qt_table.objectName() == 'realTable':
            # self.populateTableReal(filtered_vals)
            if sql_orig_table_head:
                tableHead = self.app_reale.plan_vs_real.columnsNames
                table = self.app_reale.realExpenses
            else:
                tableHead, table = chelt_plan.convert_to_display_table(self.app_reale.plan_vs_real.columnsNames,
                                                                       filtered_vals,
                                                                       self.app_reale.displayRealTableHead)
            self.populateTable(qt_table, tableHead, table)
        if qt_table.objectName() == 'TWsskm' or qt_table.objectName() == 'TWdeubnk' or qt_table.objectName() == 'TWn26':
            # self.preparesskm(filtered_vals)
            self.populateTable(qt_table, sql_table.columnsNames, filtered_vals)

    # def plotTablePie(self):
    #     # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     realExpenseTable, realExpenseTableHead = self.readPlanExpenses()
    #     allValues = realExpenseTable[:, realExpenseTableHead.index('value')].astype(float)
    #     if None in allValues:
    #         allValues = allValues[allValues != np.array(None)]
    #     totalVal = sum(allValues)
    #
    #     colTableName = realExpenseTable[:, realExpenseTableHead.index('category')]
    #     labels = []
    #     sizes = []
    #     for table in np.unique(colTableName):
    #         indx = np.where(realExpenseTable[:, realExpenseTableHead.index('category')] == table)
    #         smallArray = realExpenseTable[indx]
    #         values = sum(smallArray[:, realExpenseTableHead.index('value')].astype(float))
    #         txt = '{} = {:.2f}'.format(table, values)
    #         labels.append(txt)
    #         size = (values / totalVal) * 100
    #         sizes.append(size)
    #
    #     fig1, ax1 = plt.subplots()
    #     ax1.pie(sizes, labels=labels, autopct='%1.2f%%', startangle=90)
    #     ax1.axis('equal')
    #     plt.legend(title='Total: {:.2f}'.format(totalVal))
    #
    #     plt.show()

    # def plotNamePie(self):
    #     # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
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
    #         indx = np.where(realExpenseTable[:, realExpenseTableHead.index('name')] == table)
    #         smallArray = realExpenseTable[indx]
    #         values = sum(smallArray[:, realExpenseTableHead.index('value')].astype(float))
    #         txt = '{} = {:.2f}'.format(table, values)
    #         labels.append(txt)
    #         size = (values / totalVal) * 100
    #         sizes.append(size)
    #
    #     fig1, ax1 = plt.subplots()
    #     ax1.pie(sizes, labels=labels, autopct='%1.2f%%', startangle=90)
    #     ax1.axis('equal')
    #     plt.legend(title='Total: {:.2f}'.format(totalVal))
    #
    #     plt.show()

    # def plotPie(self, cols):
    #     print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    #     realExpenseTable, realExpenseTableHead = self.readPlanExpenses()
    #     try:
    #         allValues = realExpenseTable[:, realExpenseTableHead.index(cols[0])].astype(float)
    #         if None in allValues:
    #             allValues = allValues[allValues != np.array(None)]
    #         totalVal = sum(allValues)
    #         values_col = cols[0]
    #         names_col = cols[1]
    #     except:
    #         allValues = realExpenseTable[:, realExpenseTableHead.index(cols[1])].astype(float)
    #         if None in allValues:
    #             allValues = allValues[allValues != np.array(None)]
    #         totalVal = sum(allValues)
    #         values_col = cols[1]
    #         names_col = cols[0]
    #
    #     colTableName = realExpenseTable[:, realExpenseTableHead.index(names_col)]
    #     labels = []
    #     sizes = []
    #     for table in np.unique(colTableName):
    #         indx = np.where(realExpenseTable[:, realExpenseTableHead.index(names_col)] == table)
    #         smallArray = realExpenseTable[indx]
    #         values = sum(smallArray[:, realExpenseTableHead.index(values_col)].astype(float))
    #         txt = '{} = {:.2f}'.format(table, values)
    #         labels.append(txt)
    #         size = (values / totalVal) * 100
    #         sizes.append(size)
    #
    #     fig1, ax1 = plt.subplots()
    #     ax1.pie(sizes, labels=labels, autopct='%1.2f%%', startangle=90)
    #     ax1.axis('equal')
    #     plt.legend(title='Total: {:.2f}'.format(totalVal))
    #
    #     plt.show()

    def prep_2Dplot(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        # realExpenseTable, realExpenseTableHead = self.readPlanExpenses()
        qtablewidget = self.ui.planTable
        realExpenseTable, realExpenseTableHead = self.read_table(qtablewidget)
        allValues = realExpenseTable[:, realExpenseTableHead.index('value')].astype(float)
        if None in allValues:
            allValues = allValues[allValues != np.array(None)]
        totalVal = sum(allValues)

        colTableName = realExpenseTable[:, realExpenseTableHead.index('category')]
        labels = []
        sizes = []
        for table in np.unique(colTableName):
            indx = np.where(realExpenseTable[:, realExpenseTableHead.index('category')] == table)
            smallArray = realExpenseTable[indx]
            values = sum(smallArray[:, realExpenseTableHead.index('value')].astype(float))
            txt = '{} = {:.2f}'.format(table, values)
            labels.append(txt)
            size = (values / totalVal) * 100
            sizes.append(size)

        fig1 = Figure()
        spec5 = fig1.add_gridspec(ncols=1, nrows=2, height_ratios=[2, 1])
        ax1f1 = fig1.add_subplot(spec5[0, 0])  #
        ax1f1.grid(True)
        ax1f1.pie(sizes, labels=labels, autopct='%1.2f%%', startangle=90)
        ax1f1.axis('equal')
        ax1f1.legend()

        ax1f2 = fig1.add_subplot(spec5[1, 0])
        ax1f2.grid(True)

        payments_dict, labels = self.app_planned.prep_yearly_graf()
        ##########################################################################
        # monthly_plus_irregular = payments_dict['monthly+irregular']
        # monthly = payments_dict['monthly']
        # irregular = payments_dict['irregular']
        x = np.arange(len(labels))  # the label locations
        # width = 0.35  # the width of the bars
        # rects1 = ax1f2.bar(x - width / 2, monthly_plus_irregular, width, label='monthly+irregular')
        # rects2 = ax1f2.bar(x + width / 2, monthly, width, label='monthly')
        ##########################################################################
        sex_counts = {
            'monthly': payments_dict['monthly'],
            'irregular': payments_dict['irregular'],
        }
        bottom = np.zeros(len(labels))
        width = 0.6  # the width of the bars: can also be len(x) sequence
        for sex, sex_count in sex_counts.items():
            # print(bottom)
            p = ax1f2.bar(labels, sex_count, width, label=sex, bottom=bottom)
            bottom += sex_count

            ax1f2.bar_label(p, label_type='center')
        ##########################################################################

        ax1f2.set_xticks(x)
        ax1f2.set_xticklabels(labels)
        ax1f2.tick_params(axis='x', rotation=55)
        ax1f2.legend()
        self.rmmpl()
        self.add_plots(fig1)

    def add_plots(self, fig):
        # print(sys._getframe().f_code.co_name)
        self.canvas = FigureCanvas(fig)
        self.ui.loc_de_plot.addWidget(self.canvas)

    def rmmpl(self):
        # print(sys._getframe().f_code.co_name)
        self.ui.loc_de_plot.removeWidget(self.canvas)
        self.canvas.close()

    # def contextTableList(self, event):
    #     # print(sys._getframe().f_code.co_name)
    #     contextMenu = QMenu(self)
    #     item = self.ui.planTable.itemAt(event)
    #     if item is not None:
    #         table2Delete = item.text()
    #         contextMenu.addAction("plot pie")
    #         # contextMenu.addAction("delete all data in table")
    #         # contextMenu.addAction("delete")
    #     action = contextMenu.exec_(self.ui.planTable.mapToGlobal(event))
    #
    #     if action is not None:
    #         if action.text() == "plot pie":
    #             selectedColsIndexes = self.ui.planTable.selectionModel().selectedColumns()
    #             cols = []
    #             for tt in selectedColsIndexes:
    #                 # print(tt, type(tt))
    #                 # print(tt.row(), tt.column())
    #                 col_name = self.ui.planTable.horizontalHeaderItem(tt.column()).text()
    #                 cols.append(col_name)
    #             self.plotPie(cols)

    def contextMenu_plot_cols_from_table(self, event):
        # print(sys._getframe().f_code.co_name)
        # print('self.sender()', self.sender().parent())
        # print('self.sender()', self.sender().parent().objectName())
        qtablewidget = self.sender().parent()
        contextMenu = QMenu(self)
        item = qtablewidget.itemAt(event)
        if item is not None:
            contextMenu.addAction("plot pie")
        action = contextMenu.exec_(qtablewidget.mapToGlobal(event))

        if action is not None:
            if action.text() == "plot pie":
                selectedColsIndexes = qtablewidget.selectionModel().selectedColumns()
                cols = []
                for tt in selectedColsIndexes:
                    # print(tt, type(tt))
                    # print(tt.row(), tt.column())
                    col_name = qtablewidget.horizontalHeaderItem(tt.column()).text()
                    cols.append(col_name)
                print(cols)
                self.plotPie_new(cols, qtablewidget)

    def read_table(self, qtablewidget):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        rows = qtablewidget.rowCount()
        cols = qtablewidget.columnCount()
        planExpenseTable = np.empty((rows, cols), dtype=object)
        planExpenseTableHead = []
        for row in range(rows):
            for column in range(cols):
                cell = qtablewidget.item(row, column)
                planExpenseTable[row, column] = cell.text()
                colName = qtablewidget.horizontalHeaderItem(column).text()
                if colName not in planExpenseTableHead:
                    planExpenseTableHead.append(colName)

        return planExpenseTable, planExpenseTableHead

    def plotPie_new(self, cols, qtablewidget):
        print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        realExpenseTable, realExpenseTableHead = self.read_table(qtablewidget)
        # return
        try:
            allValues = realExpenseTable[:, realExpenseTableHead.index(cols[0])].astype(float)
            if None in allValues:
                allValues = allValues[allValues != np.array(None)]
            totalVal = sum(allValues)
            values_col = cols[0]
            names_col = cols[1]
        except:
            allValues = realExpenseTable[:, realExpenseTableHead.index(cols[1])].astype(float)
            if None in allValues:
                allValues = allValues[allValues != np.array(None)]
            totalVal = sum(allValues)
            values_col = cols[1]
            names_col = cols[0]

        colTableName = realExpenseTable[:, realExpenseTableHead.index(names_col)]
        labels = []
        sizes = []
        for table in np.unique(colTableName):
            indx = np.where(realExpenseTable[:, realExpenseTableHead.index(names_col)] == table)
            smallArray = realExpenseTable[indx]
            values = sum(smallArray[:, realExpenseTableHead.index(values_col)].astype(float))
            txt = '{} = {:.2f}'.format(table, values)
            labels.append(txt)
            size = (values / totalVal) * 100
            sizes.append(size)

        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct='%1.2f%%', startangle=90)
        ax1.axis('equal')
        plt.legend(title='Total: {:.2f}'.format(totalVal))

        plt.show()

    # def applyFilter_old(self, colName, filter):
    #     print(sys._getframe().f_code.co_name)
    #     if filter == '':
    #         return
    #
    #     if self.defaultFilter:
    #         self.ui.lineEditFilterList.clear()
    #         self.defaultFilter = False
    #
    #     filterText = self.ui.lineEditFilterList.text()
    #     if not filterText:
    #         if isinstance(filter, str):
    #             filterText += '{}="{}"'.format(colName, filter)
    #         elif isinstance(filter, tuple):
    #             filterText += '{} < {} < {}'.format(filter[0], colName, filter[1])
    #         elif isinstance(filter, list):
    #             filterText += '{} in {}"'.format(str(filter), colName)
    #     else:
    #         if isinstance(filter, str):
    #             filterText += '; {}="{}"'.format(colName, filter)
    #         elif isinstance(filter, tuple):
    #             filterText += '; {} < {} < {}'.format(filter[0], colName, filter[1])
    #         elif isinstance(filter, list):
    #             filterText += '; {} in {}"'.format(str(filter), colName)
    #     self.ui.lineEditFilterList.setText(filterText)
    #     tup = (colName, filter)
    #     self.filterList.append(tup)
    #     selectedStartDate = self.ui.DEFrom.date().toPyDate()
    #     selectedEndDate = self.ui.DEBis.date().toPyDate()
    #     match2 = ('Buchungstag', (selectedStartDate, selectedEndDate))
    #     self.filterList.append(match2)
    #
    #     currentConto = self.ui.cbActiveConto.currentText()
    #     if currentConto != 'all':
    #         match3 = ('myconto', currentConto)
    #         self.filterList.append(match3)
    #
    #     realExpenses = self.app_reale.plan_vs_real.filterRows(self.filterList)
    #     # print(50*'Ü')
    #     # for i in self.filterList:
    #     #     print('--', i)
    #     # print()
    #     payments, income = self.app_reale.split_expenses_income(realExpenses)
    #     realExpenses = np.atleast_2d(payments)
    #     realIncome = np.atleast_2d(income)
    #     if realExpenses.shape == (1, 0):
    #         realExpenses = np.empty((0, len(self.app_reale.plan_vs_real.columnsNames)))
    #     if realIncome.shape == (1, 0):
    #         realIncome = np.empty((0, len(self.app_reale.plan_vs_real.columnsNames)))
    #     self.populateTableReal(realExpenses)
    #     self.populateTableIncome(realIncome)


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


def main():
    chelt_db = chelt_db_connection(rappmysql.ini_chelt)
    users_db = users_db_connection(rappmysql.ini_users)

    app = QApplication(sys.argv)
    window = MyApp(users_db, chelt_db)
    window.show()
    # sys.exit(app.exec_())
    app.exec_()


if __name__ == '__main__':
    main()
