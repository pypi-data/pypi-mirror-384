# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'taxoninfo.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_TaxonInfo(object):
    def setupUi(self, TaxonInfo):
        if not TaxonInfo.objectName():
            TaxonInfo.setObjectName(u"TaxonInfo")
        TaxonInfo.resize(295, 221)
        self.gridLayout = QGridLayout(TaxonInfo)
        self.gridLayout.setObjectName(u"gridLayout")
        self.taxid_label = QLabel(TaxonInfo)
        self.taxid_label.setObjectName(u"taxid_label")

        self.gridLayout.addWidget(self.taxid_label, 0, 0, 1, 1)

        self.taxid_infolabel = QLabel(TaxonInfo)
        self.taxid_infolabel.setObjectName(u"taxid_infolabel")
        self.taxid_infolabel.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.taxid_infolabel, 0, 1, 1, 1)

        self.sciname_label = QLabel(TaxonInfo)
        self.sciname_label.setObjectName(u"sciname_label")

        self.gridLayout.addWidget(self.sciname_label, 1, 0, 1, 1)

        self.sciname_infolabel = QLabel(TaxonInfo)
        self.sciname_infolabel.setObjectName(u"sciname_infolabel")
        self.sciname_infolabel.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.sciname_infolabel, 1, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(85, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 1, 2, 1, 1)

        self.genbank_btn = QPushButton(TaxonInfo)
        self.genbank_btn.setObjectName(u"genbank_btn")

        self.gridLayout.addWidget(self.genbank_btn, 1, 3, 1, 1)

        self.strain_label = QLabel(TaxonInfo)
        self.strain_label.setObjectName(u"strain_label")

        self.gridLayout.addWidget(self.strain_label, 2, 0, 1, 1)

        self.strain_infolabel = QLabel(TaxonInfo)
        self.strain_infolabel.setObjectName(u"strain_infolabel")
        self.strain_infolabel.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.strain_infolabel, 2, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 133, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 3, 0, 1, 1)


        self.retranslateUi(TaxonInfo)

        QMetaObject.connectSlotsByName(TaxonInfo)
    # setupUi

    def retranslateUi(self, TaxonInfo):
        TaxonInfo.setWindowTitle(QCoreApplication.translate("TaxonInfo", u"Form", None))
        self.taxid_label.setText(QCoreApplication.translate("TaxonInfo", u"Taxid", None))
        self.taxid_infolabel.setText(QCoreApplication.translate("TaxonInfo", u"Error", None))
        self.sciname_label.setText(QCoreApplication.translate("TaxonInfo", u"Scientific Name", None))
        self.sciname_infolabel.setText(QCoreApplication.translate("TaxonInfo", u"Error", None))
        self.genbank_btn.setText(QCoreApplication.translate("TaxonInfo", u"GenBank", None))
        self.strain_label.setText(QCoreApplication.translate("TaxonInfo", u"Strain", None))
        self.strain_infolabel.setText(QCoreApplication.translate("TaxonInfo", u"Error", None))
    # retranslateUi

