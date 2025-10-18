# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'info_feature.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_InfoFeature(object):
    def setupUi(self, InfoFeature):
        if not InfoFeature.objectName():
            InfoFeature.setObjectName(u"InfoFeature")
        InfoFeature.resize(185, 43)
        self.gridLayout = QGridLayout(InfoFeature)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(6)
        self.gridLayout.setVerticalSpacing(2)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.info_start_lbl = QLabel(InfoFeature)
        self.info_start_lbl.setObjectName(u"info_start_lbl")
        self.info_start_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_start_lbl, 1, 3, 1, 1)

        self.label_9 = QLabel(InfoFeature)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout.addWidget(self.label_9, 2, 0, 1, 1)

        self.label_2 = QLabel(InfoFeature)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 2, 1, 1)

        self.info_type_lbl = QLabel(InfoFeature)
        self.info_type_lbl.setObjectName(u"info_type_lbl")
        self.info_type_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_type_lbl, 0, 1, 1, 1)

        self.label_6 = QLabel(InfoFeature)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 2, 2, 1, 1)

        self.info_stop_lbl = QLabel(InfoFeature)
        self.info_stop_lbl.setObjectName(u"info_stop_lbl")
        self.info_stop_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_stop_lbl, 2, 3, 1, 1)

        self.info_length_lbl = QLabel(InfoFeature)
        self.info_length_lbl.setObjectName(u"info_length_lbl")
        self.info_length_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_length_lbl, 1, 1, 1, 1)

        self.label_5 = QLabel(InfoFeature)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 1, 0, 1, 1)

        self.info_strand_lbl = QLabel(InfoFeature)
        self.info_strand_lbl.setObjectName(u"info_strand_lbl")
        self.info_strand_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_strand_lbl, 2, 1, 1, 1)

        self.label = QLabel(InfoFeature)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)


        self.retranslateUi(InfoFeature)

        QMetaObject.connectSlotsByName(InfoFeature)
    # setupUi

    def retranslateUi(self, InfoFeature):
        InfoFeature.setWindowTitle(QCoreApplication.translate("InfoFeature", u"Form", None))
        self.info_start_lbl.setText(QCoreApplication.translate("InfoFeature", u"info_start", None))
        self.label_9.setText(QCoreApplication.translate("InfoFeature", u"Strand:", None))
        self.label_2.setText(QCoreApplication.translate("InfoFeature", u"Start:", None))
        self.info_type_lbl.setText(QCoreApplication.translate("InfoFeature", u"info_type", None))
        self.label_6.setText(QCoreApplication.translate("InfoFeature", u"Stop:", None))
        self.info_stop_lbl.setText(QCoreApplication.translate("InfoFeature", u"info_stop", None))
        self.info_length_lbl.setText(QCoreApplication.translate("InfoFeature", u"info_length", None))
        self.label_5.setText(QCoreApplication.translate("InfoFeature", u"Length:", None))
        self.info_strand_lbl.setText(QCoreApplication.translate("InfoFeature", u"info_strand", None))
        self.label.setText(QCoreApplication.translate("InfoFeature", u"Type:", None))
    # retranslateUi

