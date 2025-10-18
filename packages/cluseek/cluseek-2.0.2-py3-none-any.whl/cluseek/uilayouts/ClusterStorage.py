# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ClusterStorage.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ClusterStorage(object):
    def setupUi(self, ClusterStorage):
        if not ClusterStorage.objectName():
            ClusterStorage.setObjectName(u"ClusterStorage")
        ClusterStorage.resize(390, 265)
        self.gridLayout = QGridLayout(ClusterStorage)
        self.gridLayout.setSpacing(3)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(2, 2, 2, 2)
        self.name_ledit = QLineEdit(ClusterStorage)
        self.name_ledit.setObjectName(u"name_ledit")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.name_ledit.sizePolicy().hasHeightForWidth())
        self.name_ledit.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.name_ledit, 0, 1, 1, 1)

        self.delete_btn = QPushButton(ClusterStorage)
        self.delete_btn.setObjectName(u"delete_btn")
        self.delete_btn.setMaximumSize(QSize(23, 23))

        self.gridLayout.addWidget(self.delete_btn, 0, 2, 1, 1)

        self.placeholder_wdgt = QFrame(ClusterStorage)
        self.placeholder_wdgt.setObjectName(u"placeholder_wdgt")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.placeholder_wdgt.sizePolicy().hasHeightForWidth())
        self.placeholder_wdgt.setSizePolicy(sizePolicy1)
        self.placeholder_wdgt.setFrameShape(QFrame.StyledPanel)
        self.placeholder_wdgt.setFrameShadow(QFrame.Raised)

        self.gridLayout.addWidget(self.placeholder_wdgt, 1, 0, 1, 3)

        self.select_wdgt = QFrame(ClusterStorage)
        self.select_wdgt.setObjectName(u"select_wdgt")
        self.select_wdgt.setFrameShape(QFrame.Panel)
        self.select_wdgt.setFrameShadow(QFrame.Raised)
        self.select_wdgt.setLineWidth(2)
        self.horizontalLayout = QHBoxLayout(self.select_wdgt)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.select_lbl = QLabel(self.select_wdgt)
        self.select_lbl.setObjectName(u"select_lbl")

        self.horizontalLayout.addWidget(self.select_lbl)


        self.gridLayout.addWidget(self.select_wdgt, 0, 0, 1, 1)


        self.retranslateUi(ClusterStorage)

        QMetaObject.connectSlotsByName(ClusterStorage)
    # setupUi

    def retranslateUi(self, ClusterStorage):
        ClusterStorage.setWindowTitle(QCoreApplication.translate("ClusterStorage", u"Form", None))
        self.delete_btn.setText(QCoreApplication.translate("ClusterStorage", u"X", None))
        self.select_lbl.setText(QCoreApplication.translate("ClusterStorage", u"<html><head/><body><p><span style=\" font-weight:600;\">Select</span></p></body></html>", None))
    # retranslateUi

