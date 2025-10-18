# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'regioninfo.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_RegionInfo(object):
    def setupUi(self, RegionInfo):
        if not RegionInfo.objectName():
            RegionInfo.setObjectName(u"RegionInfo")
        RegionInfo.resize(420, 330)
        self.gridLayout = QGridLayout(RegionInfo)
        self.gridLayout.setObjectName(u"gridLayout")
        self.genbank_btn = QPushButton(RegionInfo)
        self.genbank_btn.setObjectName(u"genbank_btn")

        self.gridLayout.addWidget(self.genbank_btn, 0, 4, 1, 1)

        self.seqacc_label = QLabel(RegionInfo)
        self.seqacc_label.setObjectName(u"seqacc_label")

        self.gridLayout.addWidget(self.seqacc_label, 0, 0, 1, 2)

        self.seqacc_infolabel = QLabel(RegionInfo)
        self.seqacc_infolabel.setObjectName(u"seqacc_infolabel")
        self.seqacc_infolabel.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.seqacc_infolabel, 0, 2, 1, 1)

        self.horizontalSpacer = QSpacerItem(165, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 3, 1, 1)

        self.regionpos_label = QLabel(RegionInfo)
        self.regionpos_label.setObjectName(u"regionpos_label")

        self.gridLayout.addWidget(self.regionpos_label, 2, 0, 1, 2)

        self.regionpos_infolabel = QLabel(RegionInfo)
        self.regionpos_infolabel.setObjectName(u"regionpos_infolabel")
        self.regionpos_infolabel.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.regionpos_infolabel, 2, 2, 1, 1)

        self.regionlen_infolabel = QLabel(RegionInfo)
        self.regionlen_infolabel.setObjectName(u"regionlen_infolabel")
        self.regionlen_infolabel.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.regionlen_infolabel, 1, 2, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 242, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 4, 1, 1, 1)

        self.regionlen_label = QLabel(RegionInfo)
        self.regionlen_label.setObjectName(u"regionlen_label")

        self.gridLayout.addWidget(self.regionlen_label, 1, 0, 1, 2)


        self.retranslateUi(RegionInfo)

        QMetaObject.connectSlotsByName(RegionInfo)
    # setupUi

    def retranslateUi(self, RegionInfo):
        RegionInfo.setWindowTitle(QCoreApplication.translate("RegionInfo", u"Form", None))
        self.genbank_btn.setText(QCoreApplication.translate("RegionInfo", u"GenBank", None))
        self.seqacc_label.setText(QCoreApplication.translate("RegionInfo", u"Sequence Accession", None))
        self.seqacc_infolabel.setText(QCoreApplication.translate("RegionInfo", u"Error", None))
        self.regionpos_label.setText(QCoreApplication.translate("RegionInfo", u"Putative Cluster Position", None))
        self.regionpos_infolabel.setText(QCoreApplication.translate("RegionInfo", u"Error", None))
        self.regionlen_infolabel.setText(QCoreApplication.translate("RegionInfo", u"Error", None))
        self.regionlen_label.setText(QCoreApplication.translate("RegionInfo", u"Putative Cluster Length", None))
    # retranslateUi

