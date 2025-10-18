# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dbprogressbar.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_DBProgressBar(object):
    def setupUi(self, DBProgressBar):
        if not DBProgressBar.objectName():
            DBProgressBar.setObjectName(u"DBProgressBar")
        DBProgressBar.resize(394, 149)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DBProgressBar.sizePolicy().hasHeightForWidth())
        DBProgressBar.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(DBProgressBar)
        self.gridLayout.setObjectName(u"gridLayout")
        self.info_lbl = QLabel(DBProgressBar)
        self.info_lbl.setObjectName(u"info_lbl")
        self.info_lbl.setWordWrap(True)

        self.gridLayout.addWidget(self.info_lbl, 0, 0, 1, 3)

        self.progress_pgbr = QProgressBar(DBProgressBar)
        self.progress_pgbr.setObjectName(u"progress_pgbr")
        self.progress_pgbr.setValue(24)

        self.gridLayout.addWidget(self.progress_pgbr, 1, 0, 1, 3)

        self.horizontalSpacer = QSpacerItem(142, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 2, 0, 1, 1)

        self.abort_btn = QPushButton(DBProgressBar)
        self.abort_btn.setObjectName(u"abort_btn")

        self.gridLayout.addWidget(self.abort_btn, 2, 1, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(141, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 2, 2, 1, 1)


        self.retranslateUi(DBProgressBar)

        QMetaObject.connectSlotsByName(DBProgressBar)
    # setupUi

    def retranslateUi(self, DBProgressBar):
        DBProgressBar.setWindowTitle(QCoreApplication.translate("DBProgressBar", u"Form", None))
        self.info_lbl.setText(QCoreApplication.translate("DBProgressBar", u"TextLabel", None))
        self.abort_btn.setText(QCoreApplication.translate("DBProgressBar", u"Abort", None))
    # retranslateUi

