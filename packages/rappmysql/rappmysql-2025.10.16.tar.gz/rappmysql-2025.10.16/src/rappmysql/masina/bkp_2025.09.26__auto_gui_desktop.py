import sys
import os
import traceback
import decimal
import datetime as dt
from datetime import datetime, timedelta
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtCore import *
# import sip
import pathlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas,
                                                NavigationToolbar2QT as NavigationToolbar)
import csv
import rappmysql
from rappmysql.masina.auto import Masina, CheckAutoRequiredFiles
from rappmysql.mruser.myusers import Users
from rappmysql.mysqlquerys import connect

np.set_printoptions(linewidth=600)

compName = os.getenv('COMPUTERNAME')

table_head_conversion = {
    'table_last_records': ['data', 'type', 'brutto', 'amount', 'eProvider', 'km'],
    'TW_all_alimentari': ['data', 'type', 'brutto', 'amount', 'eProvider', 'km'],
}
path2GUI = pathlib.Path(__file__)
path2GUI = path2GUI.resolve(path2GUI).parent / 'GUI'


class MyApp(QMainWindow):
    def __init__(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        super(MyApp, self).__init__()
        main_window = path2GUI / 'masina.ui'
        Ui_MainWindow, QtBaseClass = uic.loadUiType(main_window)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.conf = connect.Config(rappmysql.ini_masina)
        self.setWindowTitle('{}'.format(self.conf.credentials['database']))

        CheckAutoRequiredFiles(rappmysql.ini_masina)

        fig = Figure()
        self.add_plots(fig)

        self.ui.GB_add_alim.setVisible(False)
        self.ui.GB_user_options.setVisible(False)
        self.ui.TW_main_user_interface.setVisible(False)
        # self.setWindowTitle('{}: {}'.format(self.package_name, str(py_oper.get_package_version(self.package_name))))

        self.ui.PB_login.clicked.connect(self.login_user)
        self.ui.PB_add_car.clicked.connect(self.add_car)
        self.ui.PB_fire_add_row.clicked.connect(self.add_row)
        self.ui.PB_fire_filter.clicked.connect(self.populateDetailsTab)
        self.ui.TB_add_file.clicked.connect(self.get_file_pth)
        self.ui.PB_Export_csv.clicked.connect(self.export_CSV)
        self.ui.PB_export_profile.clicked.connect(self.export_full_profile)
        self.ui.PB_import_profile.clicked.connect(self.import_profile)
        self.ui.PB_erase_traces.clicked.connect(self.erase_traces)
        self.ui.TW_all_alimentari.horizontalHeader().sectionClicked.connect(self.sortPlan)
        self.ui.TW_all_alimentari.itemDoubleClicked.connect(self.upload_download_file)
        self.ui.CB_alim_types.currentIndexChanged.connect(self.populate_GB_additional_for_add_row)
        self.ui.CBMonths.currentIndexChanged.connect(self.populateDatesInterval)
        self.ui.CB_add_alim.toggled.connect(self.add_cost)
        self.ui.TW_plot_summary_det.currentChanged.connect(self.TW_plot_summary_det_currentChanged)

        if compName == 'DESKTOP-5HHINGF' or compName == 'MPCC6995':
            self.ui.LE_user_name.setText('radu')
            self.ui.LE_user_pass.setText('9876')
        #     self.login_user()
        #     # zipFile = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\static\backup_profile\000000001\2024_12_13__16_44_16_000000001.zip"
        #     # self.app_users.import_profile_with_files(zipFile, import_files=False)
        #     # self.login_user()

    def TW_plot_summary_det_currentChanged(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        tab_name = self.ui.TW_plot_summary_det.tabText(self.ui.TW_plot_summary_det.currentIndex())
        if tab_name == 'Plots':
            self.prep_2Dplot()

    def login_user(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        user_name = self.ui.LE_user_name.text()
        password = self.ui.LE_user_pass.text()
        self.user = Users(user_name, rappmysql.ini_users)
        if self.user.verify_password(password):
            self.user.init_app('auto', rappmysql.ini_masina)
            self.ui.GB_user_options.setVisible(True)
            self.ui.TW_main_user_interface.setVisible(True)
            all_user_cars = list(self.user.auto_app.masini.values())
            if all_user_cars:
                self.ui.CB_all_user_cars.addItems(all_user_cars)
                self.ui.TW_main_user_interface.setTabText(0, all_user_cars[0])
                table_name = self.ui.TW_main_user_interface.tabText(self.ui.TW_main_user_interface.currentIndex())
                id_car = int(self.user.auto_app.get_id_all_cars(table_name))
                # print('--id_car', id_car)
                self.app = Masina(rappmysql.ini_masina, self.user.id, id_car)
                self.prepare_masina_interface()
                self.prep_2Dplot()
                self.ui.CB_all_user_cars.currentIndexChanged.connect(self.fill_in_tab)
                self.ui.CB_all_user_cars.setCurrentIndex(len(all_user_cars)-1)
                # for car in all_user_cars[1:]:
                #     tab = QWidget()
                #     self.ui.TW_main_user_interface.addTab(tab, car)
            else:
                self.ui.TW_main_user_interface.setVisible(False)

    def erase_traces(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        self.user.auto_app.erase_autoapp_traces()
        print('Done')

    def add_cost(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        if self.ui.CB_add_alim.isChecked():
            self.ui.GB_add_alim.setVisible(True)
        else:
            self.ui.GB_add_alim.setVisible(False)

    def add_car(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        car_type, car_brand, car_model = AddCarWindow.get_def_arguments()
        self.user.auto_app.add_car(car_brand, car_model, car_type)

    def prepare_masina_interface(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        self.populateSummaryTab()

        self.populate_CB_alim_types()
        self.populateCBMonths()
        self.alim_date()
        self.populateDatesInterval()
        self.populateDetailsTab()

    def fill_in_tab(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        current_car = self.ui.CB_all_user_cars.currentText()
        self.ui.TW_main_user_interface.setTabText(0, current_car)
        table_name = self.ui.TW_main_user_interface.tabText(self.ui.TW_main_user_interface.currentIndex())
        id_car = int(self.user.auto_app.get_id_all_cars(table_name))
        self.app = Masina(rappmysql.ini_masina, self.user.id, id_car)
        self.prepare_masina_interface()

    def prepare_login_window(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        self.ui.TW_main_user_interface.setVisible(False)
        self.ui.PB_export_profile.setVisible(False)
        if not self.app_users.all_users:
            self.ui.PB_login.setVisible(False)

    def populate_table_widget(self, widget, table):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
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

    def upload_download_file(self, item):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        # print(item.column(), item.row(), item.text())
        if self.ui.TW_all_alimentari.horizontalHeaderItem(item.column()).text() == 'file_name':
            # print(item)
            id_ = self.ui.TW_all_alimentari.item(item.row(), 0).text()
            if item.text() != 'None':
                # print('ÄÄ', id_)
                print('id', id_)
                print('ÖÖ', self.ui.TW_all_alimentari.horizontalHeaderItem(0).text())
                expName, _ = QFileDialog.getSaveFileName(self, "Save file", "", "")
                print(expName)
                if expName:
                    file_content = self.app.alimentari.returnCellsWhere('file', ('id', id_))[0]
                    self.app.alimentari.write_file(file_content, expName)
                else:
                    return
            else:
                print('upload')
                uploadFile, _ = QFileDialog.getOpenFileName(self, "upload file", "", "")
                self.app.upload_file(uploadFile, id_)
                self.populateDetailsTab()

    def populateSummaryTab(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        # print('***self.app.table_totals', self.app.table_totals)
        if self.app.table_totals is not None:
            self.populate_table_widget(self.ui.table_totals, self.app.table_totals)
            self.populate_table_widget(self.ui.table_alimentari, self.app.table_alimentari)
            self.populate_table_widget(self.ui.table_last_records, self.app.last_records)

    def populateDetailsTab(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        # self.populate_table_widget(self.ui.TW_all_alimentari, self.app.get_all_alimentari())
        selectedStartDate = self.ui.DEFrom.date().toPyDate()
        selectedEndDate = self.ui.DEBis.date().toPyDate()
        alim_type = self.ui.CB_alim_types_filter.currentText()
        if self.ui.CB_alim_types_filter.currentText() == 'all':
            alim_type = None
        res_table = self.app.get_alimentari_for_interval_type(selectedStartDate, selectedEndDate, alim_type)
        self.populate_table_widget(self.ui.TW_all_alimentari, res_table)
        self.ui.LE_filter_showing.setText(str(res_table.shape[0]))
        self.ui.LE_total_rows.setText(str(self.app.alimentari.noOfRows))
        return res_table

    def add_row(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        # print('self.app.insert_new_alim()')
        data = self.ui.alim_date.date().toPyDate()
        alim_type = self.ui.CB_alim_types.currentText()
        brutto = self.ui.LE_brutto.text()
        file = self.ui.LE_add_file.text()

        amount = self.ui.LE_amount.text()
        refuel = self.ui.LE_refuel.text()
        other = self.ui.LE_other.text()
        recharges = self.ui.LE_recharges.text()
        provider = self.ui.CB_eProvider.currentText()
        km = self.ui.LE_km.text()
        comment = self.ui.LE_comment.text()
        table_name = self.ui.TW_main_user_interface.tabText(self.ui.TW_main_user_interface.currentIndex())
        id_all_cars = self.user.auto_app.get_id_all_cars(table_name.lower())
        # print('**', self.user.id, table_name.lower(), id_all_cars)
        # current_user_id, id_all_cars, data, alim_type, brutto, amount, refuel, other, recharges, km, comment, file
        self.app.insert_new_alim(current_id_users=self.user.id,
                                 id_all_cars=id_all_cars,
                                 data=data,
                                 alim_type=alim_type,
                                 brutto=brutto,
                                 file=file,
                                 amount=amount,
                                 refuel=refuel,
                                 other=other,
                                 recharges=recharges,
                                 provider=provider,
                                 km=km,
                                 comment=comment)

    def populate_CB_alim_types(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        self.ui.CB_alim_types.addItems(self.app.types_of_costs)
        self.ui.CB_alim_types_filter.addItem('all')
        self.ui.CB_alim_types_filter.addItems(self.app.types_of_costs)

    def populate_GB_additional_for_add_row(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        # print(self.ui.CB_alim_types.currentText())
        self.ui.GB_Amount.setVisible(False)
        self.ui.GB_Refuel.setVisible(False)
        self.ui.GB_other.setVisible(False)
        self.ui.GB_Charges.setVisible(False)
        self.ui.GB_provider.setVisible(False)
        self.ui.GB_Km.setVisible(False)
        self.ui.GB_Comment.setVisible(False)
        if self.ui.CB_alim_types.currentText() == 'electric':
            self.ui.GB_Amount.setVisible(True)
            self.ui.GB_Refuel.setVisible(True)
            self.ui.GB_other.setVisible(True)
            self.ui.GB_Charges.setVisible(True)
            self.ui.GB_provider.setVisible(True)
            self.ui.GB_Comment.setVisible(True)
            self.ui.label_L_KwH.setText('KwH')
            self.ui.label_Refuel_eCharge.setText('Echarge')
            self.ui.CB_eProvider.addItem('')
            # self.ui.CB_eProvider.addItems(self.app.electric_providers)
            self.ui.CB_eProvider.addItems(self.user.auto_app.electric_providers)
        elif self.ui.CB_alim_types.currentText() == 'benzina':
            self.ui.GB_Amount.setVisible(True)
            self.ui.GB_Refuel.setVisible(True)
            self.ui.GB_other.setVisible(True)
            self.ui.GB_Charges.setVisible(True)
            self.ui.GB_Km.setVisible(True)
            self.ui.GB_Comment.setVisible(True)
            self.ui.label_L_KwH.setText('L')
            self.ui.label_Refuel_eCharge.setText('Refuel')
        elif self.ui.CB_alim_types.currentText() == 'intretinere':
            self.ui.GB_Km.setVisible(True)
            self.ui.GB_Comment.setVisible(True)
        else:
            self.ui.GB_Comment.setVisible(True)

    def alim_date(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        self.ui.alim_date.setDate(datetime.now())
        self.ui.alim_date.setCalendarPopup(True)

    def get_file_pth(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        self.loadFile, _ = QFileDialog.getOpenFileName(self, "File", "", "File (*.jpg;*.JPG;*.pdf)")
        if self.loadFile:
            self.ui.LE_add_file.setText(self.loadFile)

    def populateCBMonths(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        self.ui.CBMonths.addItem('interval')
        months = [dt.date(2000, m, 1).strftime('%B') for m in range(1, 13)]
        for month in months:
            self.ui.CBMonths.addItem(month)

        self.ui.SB_year.setValue(datetime.now().year)

    def populateDatesInterval(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        startDate, lastDayOfMonth = self.app.default_interval

        if self.ui.CBMonths.currentText() != 'interval':
            year = int(self.ui.SB_year.value())
            startDate, lastDayOfMonth = self.app.get_monthly_interval(self.ui.CBMonths.currentText(), year)

        self.ui.DEFrom.setDate(startDate)
        self.ui.DEBis.setDate(lastDayOfMonth)

        self.ui.DEFrom.setCalendarPopup(True)
        self.ui.DEBis.setCalendarPopup(True)

    def sortPlan(self, logical_index):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name,
                                                                  sys._getframe().f_back.f_code.co_name))
        header = self.ui.TW_all_alimentari.horizontalHeader()
        order = Qt.DescendingOrder
        if not header.isSortIndicatorShown():
            header.setSortIndicatorShown(True)
        elif header.sortIndicatorSection() == logical_index:
            order = header.sortIndicatorOrder()
        header.setSortIndicator(logical_index, order)
        self.ui.TW_all_alimentari.sortItems(logical_index, order)

    def export_CSV(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        expName, _ = QFileDialog.getSaveFileName(self, "Save file", "", "File (*.csv)")
        # print(expName)
        if expName:
            res_table = self.populateDetailsTab()
            with open(expName, 'w', newline='') as file:
                writer = csv.writer(file, delimiter=';')
                # if isinstance(array, list) or isinstance(array, np.ndarray):
                for row in res_table:
                    writer.writerow(row)

    def export_full_profile(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        # expName, _ = QFileDialog.getSaveFileName(self, "Save file", "", "File (*.zip)")
        # expDir = QFileDialog.getExistingDirectory()
        # print(expDir)
        # if expName:
        if self.ui.CB_export_profile_with_files.isChecked():
            self.user.auto_app.export_profile(output_dir=None, export_files=True)
        else:
            self.user.auto_app.export_profile(output_dir=None, export_files=False)

    def import_profile(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        import_files = self.ui.CB_import_profile_with_files.isChecked()
        zipFile, _ = QFileDialog.getOpenFileName(self, "Open file", "", "File (*.zip)")
        if zipFile:
            self.user.auto_app.import_car_with_files(zipFile, import_files=import_files)

    def prep_2Dplot(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        fig1 = Figure()
        spec5 = fig1.add_gridspec(ncols=1, nrows=1)#, height_ratios=[1, 1]
        ax1f2 = fig1.add_subplot(spec5[0, 0])
        ax1f2.grid(True)
        payments_dict = self.app.dict_last_months()
        labels = list(payments_dict.keys())
        x = np.arange(len(labels))  # the label locations
        sex_counts = {}
        for type_of_cost in self.app.types_of_costs:
            sex_counts[type_of_cost] = []
            for lab, vals in payments_dict.items():
                if type_of_cost not in vals.keys():
                    sex_counts[type_of_cost].append(0)
                else:
                    sex_counts[type_of_cost].append(vals[type_of_cost])
        bottom = np.zeros(len(labels))
        width = 0.6  # the width of the bars: can also be len(x) sequence
        for sex, sex_count in sex_counts.items():
            p = ax1f2.bar(labels, sex_count, width, label=sex, bottom=bottom)
            bottom += sex_count
            ax1f2.bar_label(p, label_type='center')
        plot_lr = self.app.last_records_for_plot()
        for k, v in plot_lr.items():
            lll = k
            pos = v*len(labels)
            ax1f2.axvline(x=pos, linewidth=2, label=lll)  # color='#d62728'
        ax1f2.set_xticks(x)
        ax1f2.set_xticklabels(labels)
        # print('self.app.monthly_electric')
        # print(self.app.monthly_electric)
        # print()
        # print('self.app.monthly_benzina')
        # print(self.app.monthly_benzina)
        # print()
        # print('self.app.monthly')
        # print(self.app.monthly)
        # print()
        ax1f2.set_yticks([self.app.monthly_electric, self.app.monthly_benzina, self.app.monthly], [])
        ax1f2.set_yticklabels(['monthly_electric', 'monthly_benzina', 'monthly'])
        ax1f2.tick_params(axis='x', rotation=55)
        ax1f2.legend()
        self.rmmpl()
        self.add_plots(fig1)

    def add_plots(self, fig):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        # print(sys._getframe().f_code.co_name)
        self.canvas = FigureCanvas(fig)
        self.ui.loc_de_plot.addWidget(self.canvas)

    def rmmpl(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        # print(sys._getframe().f_code.co_name)
        self.ui.loc_de_plot.removeWidget(self.canvas)
        self.canvas.close()


class AddCarWindow(QDialog):
    def __init__(self, ):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        super(AddCarWindow, self).__init__()
        add_auto_window = path2GUI / 'add_auto.ui'
        Ui_MainWindow, QtBaseClass = uic.loadUiType(add_auto_window)
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)

    def load_inputs(self):
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        car_type = self.gui.CB_car_type.currentText()
        car_brand = self.gui.CB_car_brand.currentText()
        car_model = self.gui.CB_car_model.currentText()
        return car_type, car_brand, car_model

    @staticmethod
    def get_def_arguments():
        print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        dialog = AddCarWindow()
        result = dialog.exec_()
        if result == QDialog.Accepted:
            car_type, car_brand, car_model = dialog.load_inputs()
            return car_type, car_brand, car_model
        else:
            return None


def main():
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    # sys.exit(app.exec_())
    app.exec_()


if __name__ == '__main__':
    main()
