# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'selector_widget.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_SelectorWidget(object):
    def setupUi(self, SelectorWidget):
        if not SelectorWidget.objectName():
            SelectorWidget.setObjectName(u"SelectorWidget")
        SelectorWidget.resize(549, 345)
        self.gridLayout = QGridLayout(SelectorWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.ui_listA_label = QLabel(SelectorWidget)
        self.ui_listA_label.setObjectName(u"ui_listA_label")

        self.gridLayout.addWidget(self.ui_listA_label, 0, 0, 1, 1)

        self.ui_listB_label = QLabel(SelectorWidget)
        self.ui_listB_label.setObjectName(u"ui_listB_label")

        self.gridLayout.addWidget(self.ui_listB_label, 0, 2, 1, 1)

        self.verticalSpacer_6 = QSpacerItem(20, 119, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_6, 1, 1, 2, 1)

        self.verticalSpacer_7 = QSpacerItem(20, 101, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_7, 1, 3, 1, 1)

        self.ui_btn_Bup = QPushButton(SelectorWidget)
        self.ui_btn_Bup.setObjectName(u"ui_btn_Bup")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ui_btn_Bup.sizePolicy().hasHeightForWidth())
        self.ui_btn_Bup.setSizePolicy(sizePolicy)
        self.ui_btn_Bup.setMinimumSize(QSize(23, 41))
        self.ui_btn_Bup.setMaximumSize(QSize(23, 41))

        self.gridLayout.addWidget(self.ui_btn_Bup, 2, 3, 2, 1)

        self.ui_btn_AtoB = QPushButton(SelectorWidget)
        self.ui_btn_AtoB.setObjectName(u"ui_btn_AtoB")
        sizePolicy.setHeightForWidth(self.ui_btn_AtoB.sizePolicy().hasHeightForWidth())
        self.ui_btn_AtoB.setSizePolicy(sizePolicy)
        self.ui_btn_AtoB.setMinimumSize(QSize(41, 23))
        self.ui_btn_AtoB.setMaximumSize(QSize(41, 23))

        self.gridLayout.addWidget(self.ui_btn_AtoB, 3, 1, 1, 1)

        self.ui_btn_BtoA = QPushButton(SelectorWidget)
        self.ui_btn_BtoA.setObjectName(u"ui_btn_BtoA")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.ui_btn_BtoA.sizePolicy().hasHeightForWidth())
        self.ui_btn_BtoA.setSizePolicy(sizePolicy1)
        self.ui_btn_BtoA.setMinimumSize(QSize(41, 23))
        self.ui_btn_BtoA.setMaximumSize(QSize(41, 23))

        self.gridLayout.addWidget(self.ui_btn_BtoA, 4, 1, 1, 1)

        self.ui_btn_Bdown = QPushButton(SelectorWidget)
        self.ui_btn_Bdown.setObjectName(u"ui_btn_Bdown")
        sizePolicy.setHeightForWidth(self.ui_btn_Bdown.sizePolicy().hasHeightForWidth())
        self.ui_btn_Bdown.setSizePolicy(sizePolicy)
        self.ui_btn_Bdown.setMinimumSize(QSize(23, 41))
        self.ui_btn_Bdown.setMaximumSize(QSize(23, 41))

        self.gridLayout.addWidget(self.ui_btn_Bdown, 4, 3, 1, 1)

        self.verticalSpacer_5 = QSpacerItem(20, 101, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_5, 5, 1, 1, 1)

        self.verticalSpacer_8 = QSpacerItem(20, 101, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_8, 5, 3, 1, 1)

        self.ui_listA = QListWidget(SelectorWidget)
        self.ui_listA.setObjectName(u"ui_listA")
        self.ui_listA.setSortingEnabled(True)

        self.gridLayout.addWidget(self.ui_listA, 1, 0, 5, 1)

        self.ui_listB = QListWidget(SelectorWidget)
        self.ui_listB.setObjectName(u"ui_listB")

        self.gridLayout.addWidget(self.ui_listB, 1, 2, 5, 1)


        self.retranslateUi(SelectorWidget)

        QMetaObject.connectSlotsByName(SelectorWidget)
    # setupUi

    def retranslateUi(self, SelectorWidget):
        SelectorWidget.setWindowTitle(QCoreApplication.translate("SelectorWidget", u"Form", None))
        self.ui_listA_label.setText(QCoreApplication.translate("SelectorWidget", u"ListA", None))
        self.ui_listB_label.setText(QCoreApplication.translate("SelectorWidget", u"ListB", None))
        self.ui_btn_Bup.setText(QCoreApplication.translate("SelectorWidget", u"\u25b2", None))
        self.ui_btn_AtoB.setText(QCoreApplication.translate("SelectorWidget", u"\u25ba", None))
        self.ui_btn_BtoA.setText(QCoreApplication.translate("SelectorWidget", u"\u25c4", None))
        self.ui_btn_Bdown.setText(QCoreApplication.translate("SelectorWidget", u"\u25bc", None))
    # retranslateUi

