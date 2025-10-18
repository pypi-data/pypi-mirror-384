# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'info_cluster.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_InfoCluster(object):
    def setupUi(self, InfoCluster):
        if not InfoCluster.objectName():
            InfoCluster.setObjectName(u"InfoCluster")
        InfoCluster.resize(217, 510)
        InfoCluster.setMinimumSize(QSize(0, 0))
        self.main_layout = QGridLayout(InfoCluster)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setVerticalSpacing(2)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.network_view_container = QWidget(InfoCluster)
        self.network_view_container.setObjectName(u"network_view_container")
        self.network_view_container.setMinimumSize(QSize(210, 210))
        self.network_view_container_lay = QVBoxLayout(self.network_view_container)
        self.network_view_container_lay.setSpacing(0)
        self.network_view_container_lay.setObjectName(u"network_view_container_lay")
        self.network_view_container_lay.setContentsMargins(0, 0, 0, 0)

        self.main_layout.addWidget(self.network_view_container, 4, 0, 1, 2)

        self.info_id_lbl = QLabel(InfoCluster)
        self.info_id_lbl.setObjectName(u"info_id_lbl")
        self.info_id_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.main_layout.addWidget(self.info_id_lbl, 0, 1, 1, 1)

        self.label = QLabel(InfoCluster)
        self.label.setObjectName(u"label")

        self.main_layout.addWidget(self.label, 0, 0, 1, 1)

        self.cluster_widget_placeholder = QLabel(InfoCluster)
        self.cluster_widget_placeholder.setObjectName(u"cluster_widget_placeholder")

        self.main_layout.addWidget(self.cluster_widget_placeholder, 13, 0, 1, 3)

        self.protein_count_lbl = QLabel(InfoCluster)
        self.protein_count_lbl.setObjectName(u"protein_count_lbl")
        self.protein_count_lbl.setWordWrap(False)

        self.main_layout.addWidget(self.protein_count_lbl, 7, 1, 1, 2)

        self.info_member_tebr = QTextBrowser(InfoCluster)
        self.info_member_tebr.setObjectName(u"info_member_tebr")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.info_member_tebr.sizePolicy().hasHeightForWidth())
        self.info_member_tebr.setSizePolicy(sizePolicy)
        self.info_member_tebr.setMinimumSize(QSize(48, 48))
        self.info_member_tebr.setMaximumSize(QSize(16777215, 48))
        self.info_member_tebr.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.info_member_tebr.setLineWrapMode(QTextEdit.WidgetWidth)

        self.main_layout.addWidget(self.info_member_tebr, 8, 0, 1, 3)

        self.label_8 = QLabel(InfoCluster)
        self.label_8.setObjectName(u"label_8")

        self.main_layout.addWidget(self.label_8, 12, 0, 1, 2)

        self.info_annotations_tebr = QTextBrowser(InfoCluster)
        self.info_annotations_tebr.setObjectName(u"info_annotations_tebr")
        self.info_annotations_tebr.setMinimumSize(QSize(0, 96))
        self.info_annotations_tebr.setMaximumSize(QSize(16777215, 160))
        self.info_annotations_tebr.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.main_layout.addWidget(self.info_annotations_tebr, 11, 0, 1, 3)

        self.label_7 = QLabel(InfoCluster)
        self.label_7.setObjectName(u"label_7")

        self.main_layout.addWidget(self.label_7, 2, 0, 1, 1)

        self.label_4 = QLabel(InfoCluster)
        self.label_4.setObjectName(u"label_4")

        self.main_layout.addWidget(self.label_4, 7, 0, 1, 1)

        self.info_name_ledit = QLineEdit(InfoCluster)
        self.info_name_ledit.setObjectName(u"info_name_ledit")

        self.main_layout.addWidget(self.info_name_ledit, 1, 1, 1, 1)

        self.info_clustertype = QLabel(InfoCluster)
        self.info_clustertype.setObjectName(u"info_clustertype")

        self.main_layout.addWidget(self.info_clustertype, 2, 1, 1, 2)

        self.label_2 = QLabel(InfoCluster)
        self.label_2.setObjectName(u"label_2")

        self.main_layout.addWidget(self.label_2, 1, 0, 1, 1)

        self.label_5 = QLabel(InfoCluster)
        self.label_5.setObjectName(u"label_5")

        self.main_layout.addWidget(self.label_5, 10, 0, 1, 2)

        self.label_6 = QLabel(InfoCluster)
        self.label_6.setObjectName(u"label_6")

        self.main_layout.addWidget(self.label_6, 9, 0, 1, 1)

        self.info_proteinlength = QLabel(InfoCluster)
        self.info_proteinlength.setObjectName(u"info_proteinlength")
        self.info_proteinlength.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.main_layout.addWidget(self.info_proteinlength, 9, 1, 1, 1)

        self.pop_out_hierarchy_btn = QPushButton(InfoCluster)
        self.pop_out_hierarchy_btn.setObjectName(u"pop_out_hierarchy_btn")

        self.main_layout.addWidget(self.pop_out_hierarchy_btn, 3, 1, 1, 1)

        self.label_3 = QLabel(InfoCluster)
        self.label_3.setObjectName(u"label_3")

        self.main_layout.addWidget(self.label_3, 3, 0, 1, 1)


        self.retranslateUi(InfoCluster)

        QMetaObject.connectSlotsByName(InfoCluster)
    # setupUi

    def retranslateUi(self, InfoCluster):
        InfoCluster.setWindowTitle(QCoreApplication.translate("InfoCluster", u"Form", None))
        self.info_id_lbl.setText(QCoreApplication.translate("InfoCluster", u"info_id_lbl", None))
        self.label.setText(QCoreApplication.translate("InfoCluster", u"Protein group ID:", None))
        self.cluster_widget_placeholder.setText(QCoreApplication.translate("InfoCluster", u"CLUSTER WIDGET PLACEHOLDER", None))
        self.protein_count_lbl.setText(QCoreApplication.translate("InfoCluster", u"12345 instances", None))
        self.info_member_tebr.setHtml(QCoreApplication.translate("InfoCluster", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.label_8.setText(QCoreApplication.translate("InfoCluster", u"Related protein groups:", None))
        self.label_7.setText(QCoreApplication.translate("InfoCluster", u"Protein group origin", None))
        self.label_4.setText(QCoreApplication.translate("InfoCluster", u"Member proteins:", None))
        self.info_clustertype.setText(QCoreApplication.translate("InfoCluster", u"N/A", None))
        self.label_2.setText(QCoreApplication.translate("InfoCluster", u"Protein group name:", None))
        self.label_5.setText(QCoreApplication.translate("InfoCluster", u"GenBank annotations of member proteins:", None))
        self.label_6.setText(QCoreApplication.translate("InfoCluster", u"Avg protein length:", None))
        self.info_proteinlength.setText(QCoreApplication.translate("InfoCluster", u"info_proteinlength", None))
        self.pop_out_hierarchy_btn.setText(QCoreApplication.translate("InfoCluster", u"Show windowed", None))
        self.label_3.setText(QCoreApplication.translate("InfoCluster", u"Protein group network:", None))
    # retranslateUi

