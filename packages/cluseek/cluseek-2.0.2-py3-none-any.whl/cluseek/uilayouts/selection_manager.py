# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'selection_manager.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_SelectionManager(object):
    def setupUi(self, SelectionManager):
        if not SelectionManager.objectName():
            SelectionManager.setObjectName(u"SelectionManager")
        SelectionManager.resize(375, 550)
        self.gridLayout = QGridLayout(SelectionManager)
        self.gridLayout.setSpacing(3)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(3, 3, 3, 3)
        self.label_4 = QLabel(SelectionManager)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 2)

        self.new_rule_lay = QHBoxLayout()
        self.new_rule_lay.setObjectName(u"new_rule_lay")
        self.add_rule_btn = QPushButton(SelectionManager)
        self.add_rule_btn.setObjectName(u"add_rule_btn")

        self.new_rule_lay.addWidget(self.add_rule_btn)

        self.rule_combo = QComboBox(SelectionManager)
        self.rule_combo.setObjectName(u"rule_combo")

        self.new_rule_lay.addWidget(self.rule_combo)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.new_rule_lay.addItem(self.horizontalSpacer_3)


        self.gridLayout.addLayout(self.new_rule_lay, 4, 0, 1, 1)

        self.widget = QWidget(SelectionManager)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)

        self.gridLayout.addWidget(self.widget, 2, 0, 1, 2)

        self.line_2 = QFrame(SelectionManager)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_2, 7, 0, 1, 2)

        self.rules_scroller = QScrollArea(SelectionManager)
        self.rules_scroller.setObjectName(u"rules_scroller")
        self.rules_scroller.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.rules_scroller.setWidgetResizable(True)
        self.rules_scrollable = QWidget()
        self.rules_scrollable.setObjectName(u"rules_scrollable")
        self.rules_scrollable.setGeometry(QRect(0, 0, 364, 451))
        self.rules_lay = QVBoxLayout(self.rules_scrollable)
        self.rules_lay.setSpacing(1)
        self.rules_lay.setObjectName(u"rules_lay")
        self.rules_lay.setContentsMargins(1, 1, 1, 1)
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.rules_lay.addItem(self.verticalSpacer_2)

        self.rules_scroller.setWidget(self.rules_scrollable)

        self.gridLayout.addWidget(self.rules_scroller, 5, 0, 1, 1)

        self.control_lay = QHBoxLayout()
        self.control_lay.setObjectName(u"control_lay")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.control_lay.addItem(self.horizontalSpacer_2)

        self.select_btn = QPushButton(SelectionManager)
        self.select_btn.setObjectName(u"select_btn")

        self.control_lay.addWidget(self.select_btn)

        self.show_btn = QPushButton(SelectionManager)
        self.show_btn.setObjectName(u"show_btn")

        self.control_lay.addWidget(self.show_btn)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.control_lay.addItem(self.horizontalSpacer_4)


        self.gridLayout.addLayout(self.control_lay, 10, 0, 1, 2)

        self.line = QFrame(SelectionManager)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line, 9, 0, 1, 2)


        self.retranslateUi(SelectionManager)

        QMetaObject.connectSlotsByName(SelectionManager)
    # setupUi

    def retranslateUi(self, SelectionManager):
        SelectionManager.setWindowTitle(QCoreApplication.translate("SelectionManager", u"Form", None))
        self.label_4.setText(QCoreApplication.translate("SelectionManager", u"<html><head/><body><p><span style=\" font-weight:600;\">Gene cluster selection rules:</span></p></body></html>", None))
        self.add_rule_btn.setText(QCoreApplication.translate("SelectionManager", u"Add Rule", None))
        self.select_btn.setText(QCoreApplication.translate("SelectionManager", u"Select fitting", None))
        self.show_btn.setText(QCoreApplication.translate("SelectionManager", u"Show only fitting", None))
    # retranslateUi

