# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'info_protein.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_InfoProtein(object):
    def setupUi(self, InfoProtein):
        if not InfoProtein.objectName():
            InfoProtein.setObjectName(u"InfoProtein")
        InfoProtein.resize(168, 183)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(InfoProtein.sizePolicy().hasHeightForWidth())
        InfoProtein.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(InfoProtein)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setVerticalSpacing(2)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.lbl_name_info = QLabel(InfoProtein)
        self.lbl_name_info.setObjectName(u"lbl_name_info")

        self.gridLayout.addWidget(self.lbl_name_info, 1, 0, 1, 1)

        self.info_accession_lbl = QLabel(InfoProtein)
        self.info_accession_lbl.setObjectName(u"info_accession_lbl")
        self.info_accession_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_accession_lbl, 0, 1, 1, 1)

        self.info_length_aa = QLabel(InfoProtein)
        self.info_length_aa.setObjectName(u"info_length_aa")

        self.gridLayout.addWidget(self.info_length_aa, 2, 2, 1, 1)

        self.btn_genbank = QPushButton(InfoProtein)
        self.btn_genbank.setObjectName(u"btn_genbank")
        self.btn_genbank.setMinimumSize(QSize(64, 0))
        self.btn_genbank.setMaximumSize(QSize(80, 16777215))

        self.gridLayout.addWidget(self.btn_genbank, 1, 2, 1, 1)

        self.info_name_lbl = QLabel(InfoProtein)
        self.info_name_lbl.setObjectName(u"info_name_lbl")
        self.info_name_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_name_lbl, 1, 1, 1, 1)

        self.lbl_accession_info = QLabel(InfoProtein)
        self.lbl_accession_info.setObjectName(u"lbl_accession_info")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lbl_accession_info.sizePolicy().hasHeightForWidth())
        self.lbl_accession_info.setSizePolicy(sizePolicy1)

        self.gridLayout.addWidget(self.lbl_accession_info, 0, 0, 1, 1)

        self.lbl_annotation_info = QLabel(InfoProtein)
        self.lbl_annotation_info.setObjectName(u"lbl_annotation_info")

        self.gridLayout.addWidget(self.lbl_annotation_info, 2, 0, 1, 1)

        self.info_AAsequence = QTextBrowser(InfoProtein)
        self.info_AAsequence.setObjectName(u"info_AAsequence")
        sizePolicy2 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.info_AAsequence.sizePolicy().hasHeightForWidth())
        self.info_AAsequence.setSizePolicy(sizePolicy2)
        self.info_AAsequence.setMinimumSize(QSize(48, 128))
        self.info_AAsequence.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.gridLayout.addWidget(self.info_AAsequence, 3, 0, 1, 3)

        self.info_annotation_lbl = QLabel(InfoProtein)
        self.info_annotation_lbl.setObjectName(u"info_annotation_lbl")
        self.info_annotation_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.info_annotation_lbl, 2, 1, 1, 1)


        self.retranslateUi(InfoProtein)

        QMetaObject.connectSlotsByName(InfoProtein)
    # setupUi

    def retranslateUi(self, InfoProtein):
        InfoProtein.setWindowTitle(QCoreApplication.translate("InfoProtein", u"Form", None))
        self.lbl_name_info.setText(QCoreApplication.translate("InfoProtein", u"Name:", None))
        self.info_accession_lbl.setText(QCoreApplication.translate("InfoProtein", u"Error", None))
        self.info_length_aa.setText(QCoreApplication.translate("InfoProtein", u"info_length_aa", None))
        self.btn_genbank.setText(QCoreApplication.translate("InfoProtein", u"GenBank", None))
        self.info_name_lbl.setText(QCoreApplication.translate("InfoProtein", u"Error", None))
        self.lbl_accession_info.setText(QCoreApplication.translate("InfoProtein", u"Accession:", None))
        self.lbl_annotation_info.setText(QCoreApplication.translate("InfoProtein", u"Annotation:", None))
        self.info_AAsequence.setHtml(QCoreApplication.translate("InfoProtein", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.info_annotation_lbl.setText(QCoreApplication.translate("InfoProtein", u"Error", None))
    # retranslateUi

