# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'filewidget.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_FileWidget(object):
    def setupUi(self, FileWidget):
        if not FileWidget.objectName():
            FileWidget.setObjectName(u"FileWidget")
        FileWidget.resize(484, 37)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(FileWidget.sizePolicy().hasHeightForWidth())
        FileWidget.setSizePolicy(sizePolicy)
        FileWidget.setMinimumSize(QSize(300, 37))
        FileWidget.setMaximumSize(QSize(16777215, 16777215))
        FileWidget.setAutoFillBackground(True)
        self.gridLayout = QGridLayout(FileWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.btn_browse = QPushButton(FileWidget)
        self.btn_browse.setObjectName(u"btn_browse")
        self.btn_browse.setMinimumSize(QSize(0, 20))
        self.btn_browse.setMaximumSize(QSize(20, 22))

        self.gridLayout.addWidget(self.btn_browse, 0, 4, 1, 1)

        self.querytype_combo = QComboBox(FileWidget)
        self.querytype_combo.addItem("")
        self.querytype_combo.addItem("")
        self.querytype_combo.addItem("")
        self.querytype_combo.setObjectName(u"querytype_combo")
        self.querytype_combo.setMinimumSize(QSize(0, 20))

        self.gridLayout.addWidget(self.querytype_combo, 0, 1, 1, 1)

        self.btn_delete = QPushButton(FileWidget)
        self.btn_delete.setObjectName(u"btn_delete")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_delete.sizePolicy().hasHeightForWidth())
        self.btn_delete.setSizePolicy(sizePolicy1)
        self.btn_delete.setMinimumSize(QSize(0, 20))
        self.btn_delete.setMaximumSize(QSize(20, 22))

        self.gridLayout.addWidget(self.btn_delete, 0, 0, 1, 1)

        self.error_lbl = QLabel(FileWidget)
        self.error_lbl.setObjectName(u"error_lbl")
        self.error_lbl.setMinimumSize(QSize(0, 20))
        self.error_lbl.setMaximumSize(QSize(16777215, 16777215))
        self.error_lbl.setWordWrap(True)

        self.gridLayout.addWidget(self.error_lbl, 1, 1, 1, 2)

        self.query_text = QTextEdit(FileWidget)
        self.query_text.setObjectName(u"query_text")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.query_text.sizePolicy().hasHeightForWidth())
        self.query_text.setSizePolicy(sizePolicy2)
        self.query_text.setMinimumSize(QSize(0, 20))
        self.query_text.setMaximumSize(QSize(16777215, 20))
        self.query_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.gridLayout.addWidget(self.query_text, 0, 2, 1, 1)


        self.retranslateUi(FileWidget)

        self.querytype_combo.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(FileWidget)
    # setupUi

    def retranslateUi(self, FileWidget):
        FileWidget.setWindowTitle(QCoreApplication.translate("FileWidget", u"Form", None))
        self.btn_browse.setText(QCoreApplication.translate("FileWidget", u"...", None))
        self.querytype_combo.setItemText(0, QCoreApplication.translate("FileWidget", u"BLASTP XML", None))
        self.querytype_combo.setItemText(1, QCoreApplication.translate("FileWidget", u"NCBI protein accession", None))
        self.querytype_combo.setItemText(2, QCoreApplication.translate("FileWidget", u"Amino acid FASTA", None))

        self.querytype_combo.setCurrentText(QCoreApplication.translate("FileWidget", u"Amino acid FASTA", None))
        self.btn_delete.setText(QCoreApplication.translate("FileWidget", u"x", None))
        self.error_lbl.setText(QCoreApplication.translate("FileWidget", u"<html><head/><body><p><br/></p></body></html>", None))
    # retranslateUi

