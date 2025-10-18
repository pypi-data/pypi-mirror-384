# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'info_sequence.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_InfoSequence(object):
    def setupUi(self, InfoSequence):
        if not InfoSequence.objectName():
            InfoSequence.setObjectName(u"InfoSequence")
        InfoSequence.resize(198, 40)
        self.gridLayout = QGridLayout(InfoSequence)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setVerticalSpacing(2)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.info_sequence_acc = QLabel(InfoSequence)
        self.info_sequence_acc.setObjectName(u"info_sequence_acc")
        self.info_sequence_acc.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_sequence_acc, 0, 1, 1, 1)

        self.label = QLabel(InfoSequence)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.info_genbank_btn = QPushButton(InfoSequence)
        self.info_genbank_btn.setObjectName(u"info_genbank_btn")

        self.horizontalLayout.addWidget(self.info_genbank_btn)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 2)


        self.retranslateUi(InfoSequence)

        QMetaObject.connectSlotsByName(InfoSequence)
    # setupUi

    def retranslateUi(self, InfoSequence):
        InfoSequence.setWindowTitle(QCoreApplication.translate("InfoSequence", u"Form", None))
        self.info_sequence_acc.setText(QCoreApplication.translate("InfoSequence", u"info_sequence_acc", None))
        self.label.setText(QCoreApplication.translate("InfoSequence", u"Sequence accession:", None))
        self.info_genbank_btn.setText(QCoreApplication.translate("InfoSequence", u"GenBank", None))
    # retranslateUi

