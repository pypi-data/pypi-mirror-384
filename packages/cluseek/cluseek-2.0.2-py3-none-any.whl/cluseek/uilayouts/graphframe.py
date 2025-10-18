# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'graphframe.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_GraphFrame(object):
    def setupUi(self, GraphFrame):
        if not GraphFrame.objectName():
            GraphFrame.setObjectName(u"GraphFrame")
        GraphFrame.resize(1143, 749)
        self.gridLayout = QGridLayout(GraphFrame)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(2, 2, 2, 2)
        self.control_frame = QFrame(GraphFrame)
        self.control_frame.setObjectName(u"control_frame")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.control_frame.sizePolicy().hasHeightForWidth())
        self.control_frame.setSizePolicy(sizePolicy)
        self.control_frame.setFrameShape(QFrame.Panel)
        self.control_frame.setFrameShadow(QFrame.Raised)
        self.control_frame.setLineWidth(2)
        self.gridLayout_2 = QGridLayout(self.control_frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setHorizontalSpacing(8)
        self.gridLayout_2.setVerticalSpacing(6)
        self.gridLayout_2.setContentsMargins(2, 2, 2, 2)
        self.frame_2 = QFrame(self.control_frame)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.gridLayout_4 = QGridLayout(self.frame_2)
        self.gridLayout_4.setSpacing(2)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.save_graph_btn = QPushButton(self.frame_2)
        self.save_graph_btn.setObjectName(u"save_graph_btn")

        self.gridLayout_4.addWidget(self.save_graph_btn, 1, 0, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer_4, 2, 0, 1, 1)


        self.gridLayout_2.addWidget(self.frame_2, 1, 6, 2, 1)

        self.widget = QWidget(self.control_frame)
        self.widget.setObjectName(u"widget")
        self.verticalLayout = QVBoxLayout(self.widget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_variable_evalue = QRadioButton(self.widget)
        self.btn_variable_evalue.setObjectName(u"btn_variable_evalue")
        self.btn_variable_evalue.setChecked(True)

        self.verticalLayout.addWidget(self.btn_variable_evalue)

        self.btn_variable_identity = QRadioButton(self.widget)
        self.btn_variable_identity.setObjectName(u"btn_variable_identity")

        self.verticalLayout.addWidget(self.btn_variable_identity)

        self.btn_variable_bitscore = QRadioButton(self.widget)
        self.btn_variable_bitscore.setObjectName(u"btn_variable_bitscore")

        self.verticalLayout.addWidget(self.btn_variable_bitscore)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.gridLayout_2.addWidget(self.widget, 1, 0, 2, 1)

        self.widget_3 = QWidget(self.control_frame)
        self.widget_3.setObjectName(u"widget_3")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.widget_3.sizePolicy().hasHeightForWidth())
        self.widget_3.setSizePolicy(sizePolicy1)
        self.gridLayout_3 = QGridLayout(self.widget_3)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setHorizontalSpacing(2)
        self.gridLayout_3.setVerticalSpacing(6)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.le_max = QLineEdit(self.widget_3)
        self.le_max.setObjectName(u"le_max")

        self.gridLayout_3.addWidget(self.le_max, 2, 1, 1, 1)

        self.lbl_min = QLabel(self.widget_3)
        self.lbl_min.setObjectName(u"lbl_min")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lbl_min.sizePolicy().hasHeightForWidth())
        self.lbl_min.setSizePolicy(sizePolicy2)
        self.lbl_min.setMinimumSize(QSize(31, 21))
        self.lbl_min.setMaximumSize(QSize(31, 21))

        self.gridLayout_3.addWidget(self.lbl_min, 1, 0, 1, 1)

        self.lbl_max = QLabel(self.widget_3)
        self.lbl_max.setObjectName(u"lbl_max")
        sizePolicy2.setHeightForWidth(self.lbl_max.sizePolicy().hasHeightForWidth())
        self.lbl_max.setSizePolicy(sizePolicy2)
        self.lbl_max.setMinimumSize(QSize(31, 21))
        self.lbl_max.setMaximumSize(QSize(31, 21))

        self.gridLayout_3.addWidget(self.lbl_max, 2, 0, 1, 1)

        self.btn_wiperule = QPushButton(self.widget_3)
        self.btn_wiperule.setObjectName(u"btn_wiperule")

        self.gridLayout_3.addWidget(self.btn_wiperule, 3, 1, 1, 1)

        self.le_min = QLineEdit(self.widget_3)
        self.le_min.setObjectName(u"le_min")

        self.gridLayout_3.addWidget(self.le_min, 1, 1, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer_3, 4, 1, 1, 1)


        self.gridLayout_2.addWidget(self.widget_3, 1, 4, 2, 1)

        self.widget_2 = QWidget(self.control_frame)
        self.widget_2.setObjectName(u"widget_2")
        self.verticalLayout_2 = QVBoxLayout(self.widget_2)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.btn_loglin_lin = QRadioButton(self.widget_2)
        self.btn_loglin_lin.setObjectName(u"btn_loglin_lin")
        self.btn_loglin_lin.setChecked(True)

        self.verticalLayout_2.addWidget(self.btn_loglin_lin)

        self.btn_loglin_log = QRadioButton(self.widget_2)
        self.btn_loglin_log.setObjectName(u"btn_loglin_log")

        self.verticalLayout_2.addWidget(self.btn_loglin_log)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)


        self.gridLayout_2.addWidget(self.widget_2, 1, 2, 2, 1)

        self.label_6 = QLabel(self.control_frame)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_2.addWidget(self.label_6, 0, 6, 1, 1)

        self.lbl_variable = QLabel(self.control_frame)
        self.lbl_variable.setObjectName(u"lbl_variable")

        self.gridLayout_2.addWidget(self.lbl_variable, 0, 0, 1, 1)

        self.label_7 = QLabel(self.control_frame)
        self.label_7.setObjectName(u"label_7")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy3)

        self.gridLayout_2.addWidget(self.label_7, 0, 2, 1, 1)

        self.label_5 = QLabel(self.control_frame)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_2.addWidget(self.label_5, 0, 8, 1, 1)

        self.markerswitcher_scroller = QScrollArea(self.control_frame)
        self.markerswitcher_scroller.setObjectName(u"markerswitcher_scroller")
        sizePolicy4 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.markerswitcher_scroller.sizePolicy().hasHeightForWidth())
        self.markerswitcher_scroller.setSizePolicy(sizePolicy4)
        self.markerswitcher_scroller.setWidgetResizable(True)
        self.markerswitcher_scrollable = QWidget()
        self.markerswitcher_scrollable.setObjectName(u"markerswitcher_scrollable")
        self.markerswitcher_scrollable.setGeometry(QRect(0, 0, 179, 121))
        self.markerswitcher_scrollable_lay = QVBoxLayout(self.markerswitcher_scrollable)
        self.markerswitcher_scrollable_lay.setSpacing(3)
        self.markerswitcher_scrollable_lay.setObjectName(u"markerswitcher_scrollable_lay")
        self.markerswitcher_scroller.setWidget(self.markerswitcher_scrollable)

        self.gridLayout_2.addWidget(self.markerswitcher_scroller, 1, 8, 2, 1)

        self.lbl_scale = QLabel(self.control_frame)
        self.lbl_scale.setObjectName(u"lbl_scale")

        self.gridLayout_2.addWidget(self.lbl_scale, 0, 4, 1, 1)

        self.line = QFrame(self.control_frame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout_2.addWidget(self.line, 0, 1, 3, 1)

        self.line_2 = QFrame(self.control_frame)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.gridLayout_2.addWidget(self.line_2, 0, 3, 3, 1)

        self.line_3 = QFrame(self.control_frame)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.VLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.gridLayout_2.addWidget(self.line_3, 0, 5, 3, 1)

        self.line_4 = QFrame(self.control_frame)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.VLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.gridLayout_2.addWidget(self.line_4, 0, 7, 3, 1)


        self.gridLayout.addWidget(self.control_frame, 2, 1, 1, 5)

        self.graphcontainer = QWidget(GraphFrame)
        self.graphcontainer.setObjectName(u"graphcontainer")
        sizePolicy4.setHeightForWidth(self.graphcontainer.sizePolicy().hasHeightForWidth())
        self.graphcontainer.setSizePolicy(sizePolicy4)
        self.lay_graphcontainer = QVBoxLayout(self.graphcontainer)
        self.lay_graphcontainer.setSpacing(0)
        self.lay_graphcontainer.setObjectName(u"lay_graphcontainer")
        self.lay_graphcontainer.setContentsMargins(0, 0, 0, -1)

        self.gridLayout.addWidget(self.graphcontainer, 3, 0, 1, 7)

        self.info_histogram_container = QWidget(GraphFrame)
        self.info_histogram_container.setObjectName(u"info_histogram_container")
        self.horizontalLayout_2 = QHBoxLayout(self.info_histogram_container)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.info_histogram_container)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.horizontalLayout_2.addWidget(self.label)

        self.label_2 = QLabel(self.info_histogram_container)
        self.label_2.setObjectName(u"label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setWordWrap(True)

        self.horizontalLayout_2.addWidget(self.label_2)

        self.label_3 = QLabel(self.info_histogram_container)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setWordWrap(True)

        self.horizontalLayout_2.addWidget(self.label_3)


        self.gridLayout.addWidget(self.info_histogram_container, 1, 0, 1, 7)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_4 = QLabel(GraphFrame)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_4.addWidget(self.label_4)

        self.info_histogram_btn = QToolButton(GraphFrame)
        self.info_histogram_btn.setObjectName(u"info_histogram_btn")

        self.horizontalLayout_4.addWidget(self.info_histogram_btn)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_6)


        self.gridLayout.addLayout(self.horizontalLayout_4, 0, 0, 1, 7)


        self.retranslateUi(GraphFrame)

        QMetaObject.connectSlotsByName(GraphFrame)
    # setupUi

    def retranslateUi(self, GraphFrame):
        GraphFrame.setWindowTitle(QCoreApplication.translate("GraphFrame", u"Form", None))
        self.save_graph_btn.setText(QCoreApplication.translate("GraphFrame", u"Save graph as image", None))
        self.btn_variable_evalue.setText(QCoreApplication.translate("GraphFrame", u"E-value", None))
        self.btn_variable_identity.setText(QCoreApplication.translate("GraphFrame", u"% Identity", None))
        self.btn_variable_bitscore.setText(QCoreApplication.translate("GraphFrame", u"Bit score", None))
        self.lbl_min.setText(QCoreApplication.translate("GraphFrame", u"Min:", None))
        self.lbl_max.setText(QCoreApplication.translate("GraphFrame", u"Max:", None))
        self.btn_wiperule.setText(QCoreApplication.translate("GraphFrame", u"Clear", None))
        self.btn_loglin_lin.setText(QCoreApplication.translate("GraphFrame", u"Linear", None))
        self.btn_loglin_log.setText(QCoreApplication.translate("GraphFrame", u"Logarithmic", None))
        self.label_6.setText(QCoreApplication.translate("GraphFrame", u"<html><head/><body><p><span style=\" font-weight:600;\">Export:</span></p></body></html>", None))
        self.lbl_variable.setText(QCoreApplication.translate("GraphFrame", u"<html><head/><body><p><span style=\" font-weight:600;\">Similarity metric:</span></p></body></html>", None))
        self.label_7.setText(QCoreApplication.translate("GraphFrame", u"<html><head/><body><p><span style=\" font-weight:600;\">Y Axis (homolog count) scaling</span></p></body></html>", None))
        self.label_5.setText(QCoreApplication.translate("GraphFrame", u"<html><head/><body><p><span style=\" font-weight:600;\">Marker shown:</span></p></body></html>", None))
        self.lbl_scale.setText(QCoreApplication.translate("GraphFrame", u"<html><head/><body><p><span style=\" font-weight:600;\">Selected data range:</span></p></body></html>", None))
        self.label.setText(QCoreApplication.translate("GraphFrame", u"<html><head/><body><p><span style=\" font-style:italic; color:#4b4b4b;\">This is a histogram showing all the homologs of a given marker protein found by protein BLAST after searching all of NCBI's database. The X axis shows a homology metric, and the Y axis shows how many proteins were similar to your marker at that level. </span><span style=\" font-weight:600; font-style:italic; color:#4b4b4b;\">You must run at least one colocalization for the colocalization results to be reflected in the histogram.</span></p></body></html>", None))
        self.label_2.setText(QCoreApplication.translate("GraphFrame", u"<html><head/><body><p><span style=\" font-weight:600; font-style:italic; color:#4b4b4b;\">If you wish to colocalize only a specific subset of homologs</span><span style=\" font-style:italic; color:#4b4b4b;\">, use your mouse to select a range of values on the graph by left clicking and dragging, or enter the values into the &quot;</span><span style=\" font-weight:600; font-style:italic; color:#4b4b4b;\">Selected data range</span><span style=\" font-style:italic; color:#4b4b4b;\">&quot; fields. The next time you press &quot;</span><span style=\" font-weight:600; font-style:italic; color:#4b4b4b;\">Colocalize!&quot;</span><span style=\" font-style:italic; color:#4b4b4b;\"> CluSeek will only colocalize the homologs within the selected range of similarity. Separate limits can be set for each similarity metric.</span><span style=\" font-weight:600; font-style:italic; color:#4b4b4b;\"> This is useful for example if you wish to exclude close homologs of your marker proteins from the search.</span></p></body></html>", None))
        self.label_3.setText(QCoreApplication.translate("GraphFrame", u"<html><head/><body><p><span style=\" font-weight:600; font-style:italic; color:#4b4b4b;\">The number of colocalized homologs may not correspond to the number of clusters found, </span><span style=\" font-style:italic; color:#4b4b4b;\">as the same unique protein sequence -- even with the same accession code -- can be found in multiple clusters, sometimes even across different organisms. You can verify this by looking at the accession codes in the colocalization table.</span></p></body></html>", None))
        self.label_4.setText(QCoreApplication.translate("GraphFrame", u"<html><head/><body><p><span style=\" font-weight:600;\">BLASTP histogram</span></p></body></html>", None))
        self.info_histogram_btn.setText(QCoreApplication.translate("GraphFrame", u"?", None))
    # retranslateUi

