# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'info_taxon.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_InfoTaxon(object):
    def setupUi(self, InfoTaxon):
        if not InfoTaxon.objectName():
            InfoTaxon.setObjectName(u"InfoTaxon")
        InfoTaxon.resize(159, 85)
        self.gridLayout = QGridLayout(InfoTaxon)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setVerticalSpacing(2)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.label_13 = QLabel(InfoTaxon)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout.addWidget(self.label_13, 1, 0, 1, 1)

        self.label_12 = QLabel(InfoTaxon)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout.addWidget(self.label_12, 0, 0, 1, 1)

        self.info_sciname_lbl = QLabel(InfoTaxon)
        self.info_sciname_lbl.setObjectName(u"info_sciname_lbl")
        self.info_sciname_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_sciname_lbl, 0, 1, 1, 1)

        self.label_18 = QLabel(InfoTaxon)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout.addWidget(self.label_18, 3, 0, 1, 1)

        self.label_14 = QLabel(InfoTaxon)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout.addWidget(self.label_14, 2, 0, 1, 1)

        self.info_strain_lbl = QLabel(InfoTaxon)
        self.info_strain_lbl.setObjectName(u"info_strain_lbl")
        self.info_strain_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_strain_lbl, 1, 1, 1, 1)

        self.info_taxid_lbl = QLabel(InfoTaxon)
        self.info_taxid_lbl.setObjectName(u"info_taxid_lbl")
        self.info_taxid_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_taxid_lbl, 3, 1, 1, 1)

        self.info_lineage_lbl = QLabel(InfoTaxon)
        self.info_lineage_lbl.setObjectName(u"info_lineage_lbl")
        self.info_lineage_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_lineage_lbl, 2, 1, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.info_genbank_btn = QPushButton(InfoTaxon)
        self.info_genbank_btn.setObjectName(u"info_genbank_btn")

        self.horizontalLayout.addWidget(self.info_genbank_btn)


        self.gridLayout.addLayout(self.horizontalLayout, 4, 0, 1, 2)


        self.retranslateUi(InfoTaxon)

        QMetaObject.connectSlotsByName(InfoTaxon)
    # setupUi

    def retranslateUi(self, InfoTaxon):
        InfoTaxon.setWindowTitle(QCoreApplication.translate("InfoTaxon", u"Form", None))
        self.label_13.setText(QCoreApplication.translate("InfoTaxon", u"Strain:", None))
        self.label_12.setText(QCoreApplication.translate("InfoTaxon", u"Scientific name:", None))
        self.info_sciname_lbl.setText(QCoreApplication.translate("InfoTaxon", u"info_sciname_lbl", None))
        self.label_18.setText(QCoreApplication.translate("InfoTaxon", u"Taxonomic ID:", None))
        self.label_14.setText(QCoreApplication.translate("InfoTaxon", u"Lineage:", None))
        self.info_strain_lbl.setText(QCoreApplication.translate("InfoTaxon", u"info_strain_lbl", None))
        self.info_taxid_lbl.setText(QCoreApplication.translate("InfoTaxon", u"info_taxid_lbl", None))
        self.info_lineage_lbl.setText(QCoreApplication.translate("InfoTaxon", u"info_lineage_lbl", None))
        self.info_genbank_btn.setText(QCoreApplication.translate("InfoTaxon", u"GenBank", None))
    # retranslateUi

