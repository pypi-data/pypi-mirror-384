# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'info_region.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_InfoRegion(object):
    def setupUi(self, InfoRegion):
        if not InfoRegion.objectName():
            InfoRegion.setObjectName(u"InfoRegion")
        InfoRegion.resize(113, 43)
        self.gridLayout = QGridLayout(InfoRegion)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setVerticalSpacing(2)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(InfoRegion)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)

        self.info_start_lbl = QLabel(InfoRegion)
        self.info_start_lbl.setObjectName(u"info_start_lbl")
        self.info_start_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_start_lbl, 0, 1, 1, 1)

        self.label_4 = QLabel(InfoRegion)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 1, 0, 1, 1)

        self.info_stop_lbl = QLabel(InfoRegion)
        self.info_stop_lbl.setObjectName(u"info_stop_lbl")
        self.info_stop_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_stop_lbl, 1, 1, 1, 1)

        self.info_length_lbl = QLabel(InfoRegion)
        self.info_length_lbl.setObjectName(u"info_length_lbl")
        self.info_length_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_length_lbl, 2, 1, 1, 1)

        self.label_5 = QLabel(InfoRegion)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 2, 0, 1, 1)


        self.retranslateUi(InfoRegion)

        QMetaObject.connectSlotsByName(InfoRegion)
    # setupUi

    def retranslateUi(self, InfoRegion):
        InfoRegion.setWindowTitle(QCoreApplication.translate("InfoRegion", u"Form", None))
        self.label_3.setText(QCoreApplication.translate("InfoRegion", u"Start:", None))
        self.info_start_lbl.setText(QCoreApplication.translate("InfoRegion", u"info_start_lbl", None))
        self.label_4.setText(QCoreApplication.translate("InfoRegion", u"Stop:", None))
        self.info_stop_lbl.setText(QCoreApplication.translate("InfoRegion", u"info_stop_lbl", None))
        self.info_length_lbl.setText(QCoreApplication.translate("InfoRegion", u"info_length_lbl", None))
        self.label_5.setText(QCoreApplication.translate("InfoRegion", u"Length:", None))
    # retranslateUi

