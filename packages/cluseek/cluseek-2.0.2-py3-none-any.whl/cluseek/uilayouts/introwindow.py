# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'introwindow.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_IntroWindow(object):
    def setupUi(self, IntroWindow):
        if not IntroWindow.objectName():
            IntroWindow.setObjectName(u"IntroWindow")
        IntroWindow.resize(439, 168)
        self.gridLayout = QGridLayout(IntroWindow)
        self.gridLayout.setObjectName(u"gridLayout")
        self.open_new_btn = QPushButton(IntroWindow)
        self.open_new_btn.setObjectName(u"open_new_btn")

        self.gridLayout.addWidget(self.open_new_btn, 2, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(121, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 2, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 13, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_2, 1, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 52, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 4, 1, 1, 1)

        self.open_old_btn = QPushButton(IntroWindow)
        self.open_old_btn.setObjectName(u"open_old_btn")

        self.gridLayout.addWidget(self.open_old_btn, 3, 1, 1, 1)

        self.welcome_lbl = QLabel(IntroWindow)
        self.welcome_lbl.setObjectName(u"welcome_lbl")

        self.gridLayout.addWidget(self.welcome_lbl, 0, 0, 1, 3)

        self.horizontalSpacer_2 = QSpacerItem(120, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 2, 2, 1, 1)


        self.retranslateUi(IntroWindow)

        QMetaObject.connectSlotsByName(IntroWindow)
    # setupUi

    def retranslateUi(self, IntroWindow):
        IntroWindow.setWindowTitle(QCoreApplication.translate("IntroWindow", u"Form", None))
        self.open_new_btn.setText(QCoreApplication.translate("IntroWindow", u"Start new analysis", None))
        self.open_old_btn.setText(QCoreApplication.translate("IntroWindow", u"Open previous analysis", None))
        self.welcome_lbl.setText(QCoreApplication.translate("IntroWindow", u"<html><head/><body><p align=\"center\"><span style=\" font-size:18pt; font-weight:600;\">CluSeek</span></p></body></html>", None))
    # retranslateUi

