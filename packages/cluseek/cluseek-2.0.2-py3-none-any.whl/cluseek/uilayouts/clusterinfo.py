# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'clusterinfo.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ClusterInfo(object):
    def setupUi(self, ClusterInfo):
        if not ClusterInfo.objectName():
            ClusterInfo.setObjectName(u"ClusterInfo")
        ClusterInfo.resize(271, 420)
        self.gridLayout = QGridLayout(ClusterInfo)
        self.gridLayout.setObjectName(u"gridLayout")
        self.ledit_rename = QLineEdit(ClusterInfo)
        self.ledit_rename.setObjectName(u"ledit_rename")

        self.gridLayout.addWidget(self.ledit_rename, 1, 1, 1, 1)

        self.lbl_color = QLabel(ClusterInfo)
        self.lbl_color.setObjectName(u"lbl_color")

        self.gridLayout.addWidget(self.lbl_color, 2, 0, 1, 1)

        self.label_2 = QLabel(ClusterInfo)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.label_2, 2, 1, 1, 1)

        self.txb_annotations = QTextBrowser(ClusterInfo)
        self.txb_annotations.setObjectName(u"txb_annotations")
        self.txb_annotations.setMinimumSize(QSize(0, 128))
        self.txb_annotations.setMaximumSize(QSize(16777215, 128))

        self.gridLayout.addWidget(self.txb_annotations, 11, 0, 1, 4)

        self.txb_members = QTextBrowser(ClusterInfo)
        self.txb_members.setObjectName(u"txb_members")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txb_members.sizePolicy().hasHeightForWidth())
        self.txb_members.setSizePolicy(sizePolicy)
        self.txb_members.setMinimumSize(QSize(48, 48))
        self.txb_members.setMaximumSize(QSize(16777215, 48))
        self.txb_members.setLineWrapMode(QTextEdit.WidgetWidth)

        self.gridLayout.addWidget(self.txb_members, 6, 0, 1, 4)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 3, 2, 1, 3)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 12, 0, 1, 1)

        self.btn_rename = QPushButton(ClusterInfo)
        self.btn_rename.setObjectName(u"btn_rename")

        self.gridLayout.addWidget(self.btn_rename, 1, 2, 1, 1)

        self.lbl_pidentity = QLabel(ClusterInfo)
        self.lbl_pidentity.setObjectName(u"lbl_pidentity")
        self.lbl_pidentity.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.lbl_pidentity, 4, 1, 1, 1)

        self.lbl_pidentity_info = QLabel(ClusterInfo)
        self.lbl_pidentity_info.setObjectName(u"lbl_pidentity_info")

        self.gridLayout.addWidget(self.lbl_pidentity_info, 4, 0, 1, 1)

        self.lbl_clusterid = QLabel(ClusterInfo)
        self.lbl_clusterid.setObjectName(u"lbl_clusterid")
        self.lbl_clusterid.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.lbl_clusterid, 0, 1, 1, 1)

        self.lbl_nproteins_info = QLabel(ClusterInfo)
        self.lbl_nproteins_info.setObjectName(u"lbl_nproteins_info")

        self.gridLayout.addWidget(self.lbl_nproteins_info, 3, 0, 1, 1)

        self.lbl_clusterid_info = QLabel(ClusterInfo)
        self.lbl_clusterid_info.setObjectName(u"lbl_clusterid_info")

        self.gridLayout.addWidget(self.lbl_clusterid_info, 0, 0, 1, 1)

        self.lbl_members_info = QLabel(ClusterInfo)
        self.lbl_members_info.setObjectName(u"lbl_members_info")

        self.gridLayout.addWidget(self.lbl_members_info, 5, 0, 1, 1)

        self.lbl_nproteins = QLabel(ClusterInfo)
        self.lbl_nproteins.setObjectName(u"lbl_nproteins")
        self.lbl_nproteins.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.lbl_nproteins, 3, 1, 1, 1)

        self.lbl_rename = QLabel(ClusterInfo)
        self.lbl_rename.setObjectName(u"lbl_rename")

        self.gridLayout.addWidget(self.lbl_rename, 1, 0, 1, 1)

        self.lbl_annotations_info = QLabel(ClusterInfo)
        self.lbl_annotations_info.setObjectName(u"lbl_annotations_info")

        self.gridLayout.addWidget(self.lbl_annotations_info, 9, 0, 1, 4)

        self.ledit_userannotation = QLineEdit(ClusterInfo)
        self.ledit_userannotation.setObjectName(u"ledit_userannotation")

        self.gridLayout.addWidget(self.ledit_userannotation, 8, 0, 1, 3)

        self.lbl_userannotation = QLabel(ClusterInfo)
        self.lbl_userannotation.setObjectName(u"lbl_userannotation")

        self.gridLayout.addWidget(self.lbl_userannotation, 7, 0, 1, 1)

        self.btn_applyuserannotation = QPushButton(ClusterInfo)
        self.btn_applyuserannotation.setObjectName(u"btn_applyuserannotation")

        self.gridLayout.addWidget(self.btn_applyuserannotation, 7, 2, 1, 1)


        self.retranslateUi(ClusterInfo)

        QMetaObject.connectSlotsByName(ClusterInfo)
    # setupUi

    def retranslateUi(self, ClusterInfo):
        ClusterInfo.setWindowTitle(QCoreApplication.translate("ClusterInfo", u"Form", None))
        self.lbl_color.setText(QCoreApplication.translate("ClusterInfo", u"Color:", None))
        self.label_2.setText(QCoreApplication.translate("ClusterInfo", u"WIP", None))
        self.txb_members.setHtml(QCoreApplication.translate("ClusterInfo", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.btn_rename.setText(QCoreApplication.translate("ClusterInfo", u"Apply", None))
        self.lbl_pidentity.setText(QCoreApplication.translate("ClusterInfo", u"Error", None))
        self.lbl_pidentity_info.setText(QCoreApplication.translate("ClusterInfo", u"clustered to identity:", None))
        self.lbl_clusterid.setText(QCoreApplication.translate("ClusterInfo", u"Error", None))
        self.lbl_nproteins_info.setText(QCoreApplication.translate("ClusterInfo", u"n proteins:", None))
        self.lbl_clusterid_info.setText(QCoreApplication.translate("ClusterInfo", u"Protein Cluster ID:", None))
        self.lbl_members_info.setText(QCoreApplication.translate("ClusterInfo", u"Member Proteins:", None))
        self.lbl_nproteins.setText(QCoreApplication.translate("ClusterInfo", u"Error", None))
        self.lbl_rename.setText(QCoreApplication.translate("ClusterInfo", u"Alternative Name:", None))
        self.lbl_annotations_info.setText(QCoreApplication.translate("ClusterInfo", u"Annotations of Member Proteins in GenBank", None))
        self.lbl_userannotation.setText(QCoreApplication.translate("ClusterInfo", u"User Annotation:", None))
        self.btn_applyuserannotation.setText(QCoreApplication.translate("ClusterInfo", u"Apply", None))
    # retranslateUi

