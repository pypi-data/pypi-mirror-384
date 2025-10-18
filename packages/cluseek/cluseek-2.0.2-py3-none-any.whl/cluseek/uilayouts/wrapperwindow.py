# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'wrapperwindow.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1286, 828)
        self.action_aboutme = QAction(MainWindow)
        self.action_aboutme.setObjectName(u"action_aboutme")
        self.action_aboutqt = QAction(MainWindow)
        self.action_aboutqt.setObjectName(u"action_aboutqt")
        self.actionOffline_Mode = QAction(MainWindow)
        self.actionOffline_Mode.setObjectName(u"actionOffline_Mode")
        self.action_offlinemode = QAction(MainWindow)
        self.action_offlinemode.setObjectName(u"action_offlinemode")
        self.action_offlinemode.setCheckable(True)
        self.action_offlinemode.setChecked(False)
        self.action_export_filtergraph = QAction(MainWindow)
        self.action_export_filtergraph.setObjectName(u"action_export_filtergraph")
        self.action_export_filterdata = QAction(MainWindow)
        self.action_export_filterdata.setObjectName(u"action_export_filterdata")
        self.action_export_neighborimage = QAction(MainWindow)
        self.action_export_neighborimage.setObjectName(u"action_export_neighborimage")
        self.action_export_neighborexcel = QAction(MainWindow)
        self.action_export_neighborexcel.setObjectName(u"action_export_neighborexcel")
        self.action_nei_proportional = QAction(MainWindow)
        self.action_nei_proportional.setObjectName(u"action_nei_proportional")
        self.action_nei_proportional.setCheckable(True)
        self.action_nei_proportional.setChecked(True)
        self.action_nei_fixed = QAction(MainWindow)
        self.action_nei_fixed.setObjectName(u"action_nei_fixed")
        self.action_nei_fixed.setCheckable(True)
        self.action_nei_setpropsizes = QAction(MainWindow)
        self.action_nei_setpropsizes.setObjectName(u"action_nei_setpropsizes")
        self.action_nei_setfixedsizes = QAction(MainWindow)
        self.action_nei_setfixedsizes.setObjectName(u"action_nei_setfixedsizes")
        self.action_codeinteract = QAction(MainWindow)
        self.action_codeinteract.setObjectName(u"action_codeinteract")
        self.file_save_act = QAction(MainWindow)
        self.file_save_act.setObjectName(u"file_save_act")
        self.file_saveas_act = QAction(MainWindow)
        self.file_saveas_act.setObjectName(u"file_saveas_act")
        self.file_load_act = QAction(MainWindow)
        self.file_load_act.setObjectName(u"file_load_act")
        self.file_export_act = QAction(MainWindow)
        self.file_export_act.setObjectName(u"file_export_act")
        self.file_new_act = QAction(MainWindow)
        self.file_new_act.setObjectName(u"file_new_act")
        self.offline_action = QAction(MainWindow)
        self.offline_action.setObjectName(u"offline_action")
        self.offline_action.setCheckable(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.maintabs = QTabWidget(self.centralwidget)
        self.maintabs.setObjectName(u"maintabs")
        self.tab_filter = QWidget()
        self.tab_filter.setObjectName(u"tab_filter")
        self.lay_tab_filter = QGridLayout(self.tab_filter)
        self.lay_tab_filter.setObjectName(u"lay_tab_filter")
        self.lay_tab_filter.setHorizontalSpacing(1)
        self.lay_tab_filter.setContentsMargins(1, 1, 1, 1)
        self.maintabs.addTab(self.tab_filter, "")

        self.verticalLayout.addWidget(self.maintabs)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1286, 21))
        self.menuAbout = QMenu(self.menubar)
        self.menuAbout.setObjectName(u"menuAbout")
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuDatabase = QMenu(self.menubar)
        self.menuDatabase.setObjectName(u"menuDatabase")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuDatabase.menuAction())
        self.menubar.addAction(self.menuAbout.menuAction())
        self.menuAbout.addAction(self.action_aboutme)
        self.menuAbout.addAction(self.action_aboutqt)
        self.menuFile.addAction(self.file_save_act)
        self.menuFile.addAction(self.file_saveas_act)
        self.menuDatabase.addAction(self.offline_action)

        self.retranslateUi(MainWindow)

        self.maintabs.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.action_aboutme.setText(QCoreApplication.translate("MainWindow", u"About software", None))
        self.action_aboutqt.setText(QCoreApplication.translate("MainWindow", u"About Qt", None))
        self.actionOffline_Mode.setText(QCoreApplication.translate("MainWindow", u"Offline Mode", None))
        self.action_offlinemode.setText(QCoreApplication.translate("MainWindow", u"Offline Mode", None))
        self.action_export_filtergraph.setText(QCoreApplication.translate("MainWindow", u"Export current BLAST results graph", None))
        self.action_export_filterdata.setText(QCoreApplication.translate("MainWindow", u"Export colocalization results", None))
        self.action_export_neighborimage.setText(QCoreApplication.translate("MainWindow", u"Export Neighborhood view as image", None))
        self.action_export_neighborexcel.setText(QCoreApplication.translate("MainWindow", u"Export neighborhood view as Excel spreadsheet", None))
        self.action_nei_proportional.setText(QCoreApplication.translate("MainWindow", u"Use proportional sequence sizes", None))
        self.action_nei_fixed.setText(QCoreApplication.translate("MainWindow", u"Use fixed sequence sizes", None))
        self.action_nei_setpropsizes.setText(QCoreApplication.translate("MainWindow", u"Set proportional sequence sizes", None))
        self.action_nei_setfixedsizes.setText(QCoreApplication.translate("MainWindow", u"Set fixed sequence sizes", None))
        self.action_codeinteract.setText(QCoreApplication.translate("MainWindow", u"Code Interact", None))
        self.file_save_act.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.file_saveas_act.setText(QCoreApplication.translate("MainWindow", u"Save as", None))
        self.file_load_act.setText(QCoreApplication.translate("MainWindow", u"Load", None))
        self.file_export_act.setText(QCoreApplication.translate("MainWindow", u"Export", None))
        self.file_new_act.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.offline_action.setText(QCoreApplication.translate("MainWindow", u"Offline mode", None))
        self.maintabs.setTabText(self.maintabs.indexOf(self.tab_filter), QCoreApplication.translate("MainWindow", u"Markers and colocalization", None))
        self.menuAbout.setTitle(QCoreApplication.translate("MainWindow", u"About", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuDatabase.setTitle(QCoreApplication.translate("MainWindow", u"Database", None))
    # retranslateUi

