# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about_neiview.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_AboutNeiview(object):
    def setupUi(self, AboutNeiview):
        if not AboutNeiview.objectName():
            AboutNeiview.setObjectName(u"AboutNeiview")
        AboutNeiview.resize(819, 444)
        self.gridLayout = QGridLayout(AboutNeiview)
        self.gridLayout.setObjectName(u"gridLayout")
        self.creation_info_lbl = QLabel(AboutNeiview)
        self.creation_info_lbl.setObjectName(u"creation_info_lbl")
        self.creation_info_lbl.setWordWrap(True)

        self.gridLayout.addWidget(self.creation_info_lbl, 3, 0, 1, 1)

        self.label = QLabel(AboutNeiview)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.label_2 = QLabel(AboutNeiview)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)

        self.general_info_lbl = QLabel(AboutNeiview)
        self.general_info_lbl.setObjectName(u"general_info_lbl")
        self.general_info_lbl.setWordWrap(True)

        self.gridLayout.addWidget(self.general_info_lbl, 1, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 4, 0, 1, 1)


        self.retranslateUi(AboutNeiview)

        QMetaObject.connectSlotsByName(AboutNeiview)
    # setupUi

    def retranslateUi(self, AboutNeiview):
        AboutNeiview.setWindowTitle(QCoreApplication.translate("AboutNeiview", u"Form", None))
        self.creation_info_lbl.setText(QCoreApplication.translate("AboutNeiview", u"TextLabel", None))
        self.label.setText(QCoreApplication.translate("AboutNeiview", u"<html><head/><body><p><span style=\" font-weight:600;\">General</span></p></body></html>", None))
        self.label_2.setText(QCoreApplication.translate("AboutNeiview", u"<html><head/><body><p><span style=\" font-weight:600;\">Creation parameters</span></p></body></html>", None))
        self.general_info_lbl.setText(QCoreApplication.translate("AboutNeiview", u"TextLabel", None))
    # retranslateUi

