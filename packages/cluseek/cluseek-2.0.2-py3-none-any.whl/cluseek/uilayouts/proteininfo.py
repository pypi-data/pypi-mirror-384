# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'proteininfo.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ProteinInfo(object):
    def setupUi(self, ProteinInfo):
        if not ProteinInfo.objectName():
            ProteinInfo.setObjectName(u"ProteinInfo")
        ProteinInfo.resize(274, 278)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ProteinInfo.sizePolicy().hasHeightForWidth())
        ProteinInfo.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(ProteinInfo)
        self.gridLayout.setObjectName(u"gridLayout")
        self.txb_AAsequence = QTextBrowser(ProteinInfo)
        self.txb_AAsequence.setObjectName(u"txb_AAsequence")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.txb_AAsequence.sizePolicy().hasHeightForWidth())
        self.txb_AAsequence.setSizePolicy(sizePolicy1)
        self.txb_AAsequence.setMinimumSize(QSize(48, 128))

        self.gridLayout.addWidget(self.txb_AAsequence, 3, 0, 1, 4)

        self.btn_genbank = QPushButton(ProteinInfo)
        self.btn_genbank.setObjectName(u"btn_genbank")
        self.btn_genbank.setMinimumSize(QSize(64, 0))
        self.btn_genbank.setMaximumSize(QSize(80, 16777215))

        self.gridLayout.addWidget(self.btn_genbank, 1, 3, 1, 1)

        self.lbl_name = QLabel(ProteinInfo)
        self.lbl_name.setObjectName(u"lbl_name")
        self.lbl_name.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.lbl_name, 1, 1, 1, 1)

        self.lbl_accession_info = QLabel(ProteinInfo)
        self.lbl_accession_info.setObjectName(u"lbl_accession_info")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lbl_accession_info.sizePolicy().hasHeightForWidth())
        self.lbl_accession_info.setSizePolicy(sizePolicy2)

        self.gridLayout.addWidget(self.lbl_accession_info, 0, 0, 1, 1)

        self.lbl_annotation_info = QLabel(ProteinInfo)
        self.lbl_annotation_info.setObjectName(u"lbl_annotation_info")

        self.gridLayout.addWidget(self.lbl_annotation_info, 2, 0, 1, 1)

        self.lbl_annotation = QLabel(ProteinInfo)
        self.lbl_annotation.setObjectName(u"lbl_annotation")
        self.lbl_annotation.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.lbl_annotation, 2, 1, 1, 1)

        self.lbl_accession = QLabel(ProteinInfo)
        self.lbl_accession.setObjectName(u"lbl_accession")
        self.lbl_accession.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.lbl_accession, 0, 1, 1, 1)

        self.lbl_name_info = QLabel(ProteinInfo)
        self.lbl_name_info.setObjectName(u"lbl_name_info")

        self.gridLayout.addWidget(self.lbl_name_info, 1, 0, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 1, 2, 1, 1)


        self.retranslateUi(ProteinInfo)

        QMetaObject.connectSlotsByName(ProteinInfo)
    # setupUi

    def retranslateUi(self, ProteinInfo):
        ProteinInfo.setWindowTitle(QCoreApplication.translate("ProteinInfo", u"Form", None))
        self.txb_AAsequence.setHtml(QCoreApplication.translate("ProteinInfo", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.btn_genbank.setText(QCoreApplication.translate("ProteinInfo", u"GenBank", None))
        self.lbl_name.setText(QCoreApplication.translate("ProteinInfo", u"Error", None))
        self.lbl_accession_info.setText(QCoreApplication.translate("ProteinInfo", u"Accession:", None))
        self.lbl_annotation_info.setText(QCoreApplication.translate("ProteinInfo", u"Annotation:", None))
        self.lbl_annotation.setText(QCoreApplication.translate("ProteinInfo", u"Error", None))
        self.lbl_accession.setText(QCoreApplication.translate("ProteinInfo", u"Error", None))
        self.lbl_name_info.setText(QCoreApplication.translate("ProteinInfo", u"Name:", None))
    # retranslateUi

