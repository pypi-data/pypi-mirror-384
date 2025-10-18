# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'neiview_creator.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_NeiviewCreator(object):
    def setupUi(self, NeiviewCreator):
        if not NeiviewCreator.objectName():
            NeiviewCreator.setObjectName(u"NeiviewCreator")
        NeiviewCreator.setEnabled(True)
        NeiviewCreator.resize(755, 829)
        self.verticalLayout = QVBoxLayout(NeiviewCreator)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(NeiviewCreator)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setMinimumSize(QSize(500, 0))
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 753, 778))
        self.gridLayout_4 = QGridLayout(self.scrollAreaWidgetContents_2)
        self.gridLayout_4.setSpacing(2)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.nneighborhoods_label = QLabel(self.scrollAreaWidgetContents_2)
        self.nneighborhoods_label.setObjectName(u"nneighborhoods_label")

        self.horizontalLayout_13.addWidget(self.nneighborhoods_label)

        self.nneighborhoods_displaylabel = QLabel(self.scrollAreaWidgetContents_2)
        self.nneighborhoods_displaylabel.setObjectName(u"nneighborhoods_displaylabel")

        self.horizontalLayout_13.addWidget(self.nneighborhoods_displaylabel)

        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_11)


        self.gridLayout_4.addLayout(self.horizontalLayout_13, 3, 0, 1, 5)

        self.community_detection_helplbl = QLabel(self.scrollAreaWidgetContents_2)
        self.community_detection_helplbl.setObjectName(u"community_detection_helplbl")
        self.community_detection_helplbl.setWordWrap(True)

        self.gridLayout_4.addWidget(self.community_detection_helplbl, 20, 1, 1, 4)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.label_10 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_11.addWidget(self.label_10)

        self.community_detection_helpbtn = QToolButton(self.scrollAreaWidgetContents_2)
        self.community_detection_helpbtn.setObjectName(u"community_detection_helpbtn")

        self.horizontalLayout_11.addWidget(self.community_detection_helpbtn)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_9)


        self.gridLayout_4.addLayout(self.horizontalLayout_11, 19, 1, 1, 4)

        self.label_21 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setWordWrap(True)

        self.gridLayout_4.addWidget(self.label_21, 13, 2, 1, 3)

        self.community_resolution_helplbl = QLabel(self.scrollAreaWidgetContents_2)
        self.community_resolution_helplbl.setObjectName(u"community_resolution_helplbl")
        self.community_resolution_helplbl.setWordWrap(True)

        self.gridLayout_4.addWidget(self.community_resolution_helplbl, 23, 2, 1, 3)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.label_2 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_17.addWidget(self.label_2)

        self.clus_global_identity_spin = QSpinBox(self.scrollAreaWidgetContents_2)
        self.clus_global_identity_spin.setObjectName(u"clus_global_identity_spin")
        self.clus_global_identity_spin.setMinimum(0)
        self.clus_global_identity_spin.setMaximum(100)
        self.clus_global_identity_spin.setValue(0)

        self.horizontalLayout_17.addWidget(self.clus_global_identity_spin)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer)


        self.gridLayout_4.addLayout(self.horizontalLayout_17, 9, 2, 1, 3)

        self.horizontalSpacer_16 = QSpacerItem(20, 3, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_16, 12, 1, 1, 1)

        self.label_12 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setWordWrap(True)

        self.gridLayout_4.addWidget(self.label_12, 0, 0, 1, 5)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.label_11 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setWordWrap(False)

        self.horizontalLayout_16.addWidget(self.label_11)

        self.community_weight_variable_combo = QComboBox(self.scrollAreaWidgetContents_2)
        self.community_weight_variable_combo.setObjectName(u"community_weight_variable_combo")

        self.horizontalLayout_16.addWidget(self.community_weight_variable_combo)

        self.horizontalSpacer_13 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_13)


        self.gridLayout_4.addLayout(self.horizontalLayout_16, 21, 2, 1, 3)

        self.clus_local_pidentity_helplbl = QLabel(self.scrollAreaWidgetContents_2)
        self.clus_local_pidentity_helplbl.setObjectName(u"clus_local_pidentity_helplbl")
        self.clus_local_pidentity_helplbl.setWordWrap(True)

        self.gridLayout_4.addWidget(self.clus_local_pidentity_helplbl, 15, 2, 1, 3)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_8 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_7.addWidget(self.label_8)

        self.local_alignment_helpbtn = QToolButton(self.scrollAreaWidgetContents_2)
        self.local_alignment_helpbtn.setObjectName(u"local_alignment_helpbtn")

        self.horizontalLayout_7.addWidget(self.local_alignment_helpbtn)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_3)


        self.gridLayout_4.addLayout(self.horizontalLayout_7, 10, 1, 1, 4)

        self.widget = QWidget(self.scrollAreaWidgetContents_2)
        self.widget.setObjectName(u"widget")
        self.gridLayout = QGridLayout(self.widget)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setSpacing(6)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.clus_local_evalue_exponent_radio = QRadioButton(self.widget)
        self.clus_local_evalue_exponent_radio.setObjectName(u"clus_local_evalue_exponent_radio")
        self.clus_local_evalue_exponent_radio.setChecked(False)

        self.horizontalLayout_9.addWidget(self.clus_local_evalue_exponent_radio)

        self.clus_local_evalue_exponent_spin = QSpinBox(self.widget)
        self.clus_local_evalue_exponent_spin.setObjectName(u"clus_local_evalue_exponent_spin")
        self.clus_local_evalue_exponent_spin.setMinimum(-999)
        self.clus_local_evalue_exponent_spin.setMaximum(999)
        self.clus_local_evalue_exponent_spin.setValue(-10)

        self.horizontalLayout_9.addWidget(self.clus_local_evalue_exponent_spin)

        self.clus_local_evalue_exponent_helpbtn = QToolButton(self.widget)
        self.clus_local_evalue_exponent_helpbtn.setObjectName(u"clus_local_evalue_exponent_helpbtn")

        self.horizontalLayout_9.addWidget(self.clus_local_evalue_exponent_helpbtn)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_7)


        self.gridLayout.addLayout(self.horizontalLayout_9, 0, 0, 1, 1)

        self.clus_local_evalue_exponent_helplbl = QLabel(self.widget)
        self.clus_local_evalue_exponent_helplbl.setObjectName(u"clus_local_evalue_exponent_helplbl")
        self.clus_local_evalue_exponent_helplbl.setWordWrap(True)

        self.gridLayout.addWidget(self.clus_local_evalue_exponent_helplbl, 1, 0, 1, 1)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.clus_local_bitscore_radio = QRadioButton(self.widget)
        self.clus_local_bitscore_radio.setObjectName(u"clus_local_bitscore_radio")
        self.clus_local_bitscore_radio.setChecked(True)

        self.horizontalLayout_10.addWidget(self.clus_local_bitscore_radio)

        self.clus_local_bitscore_spin = QSpinBox(self.widget)
        self.clus_local_bitscore_spin.setObjectName(u"clus_local_bitscore_spin")
        self.clus_local_bitscore_spin.setMaximum(999)
        self.clus_local_bitscore_spin.setValue(40)

        self.horizontalLayout_10.addWidget(self.clus_local_bitscore_spin)

        self.clus_local_bitscore_helpbtn = QToolButton(self.widget)
        self.clus_local_bitscore_helpbtn.setObjectName(u"clus_local_bitscore_helpbtn")

        self.horizontalLayout_10.addWidget(self.clus_local_bitscore_helpbtn)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_8)


        self.gridLayout.addLayout(self.horizontalLayout_10, 2, 0, 1, 1)

        self.clus_local_bitscore_helplbl = QLabel(self.widget)
        self.clus_local_bitscore_helplbl.setObjectName(u"clus_local_bitscore_helplbl")
        self.clus_local_bitscore_helplbl.setWordWrap(True)

        self.gridLayout.addWidget(self.clus_local_bitscore_helplbl, 3, 0, 1, 1)

        self.clus_local_bitscore_helplbl.raise_()
        self.clus_local_evalue_exponent_helplbl.raise_()

        self.gridLayout_4.addWidget(self.widget, 16, 2, 1, 3)

        self.local_alignment_helplbl = QLabel(self.scrollAreaWidgetContents_2)
        self.local_alignment_helplbl.setObjectName(u"local_alignment_helplbl")
        self.local_alignment_helplbl.setWordWrap(True)

        self.gridLayout_4.addWidget(self.local_alignment_helplbl, 11, 1, 1, 4)

        self.horizontalSpacer_15 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_15, 24, 2, 1, 3)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.label_3 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_15.addWidget(self.label_3)

        self.clus_local_sensitivity_combo = QComboBox(self.scrollAreaWidgetContents_2)
        self.clus_local_sensitivity_combo.setObjectName(u"clus_local_sensitivity_combo")

        self.horizontalLayout_15.addWidget(self.clus_local_sensitivity_combo)

        self.horizontalSpacer_14 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_15.addItem(self.horizontalSpacer_14)


        self.gridLayout_4.addLayout(self.horizontalLayout_15, 18, 2, 1, 3)

        self.horizontalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_2, 11, 0, 1, 1)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_18 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_18.setObjectName(u"label_18")

        self.horizontalLayout_12.addWidget(self.label_18)

        self.community_resolution_spin = QDoubleSpinBox(self.scrollAreaWidgetContents_2)
        self.community_resolution_spin.setObjectName(u"community_resolution_spin")
        self.community_resolution_spin.setValue(1.000000000000000)

        self.horizontalLayout_12.addWidget(self.community_resolution_spin)

        self.community_resolution_helpbtn = QToolButton(self.scrollAreaWidgetContents_2)
        self.community_resolution_helpbtn.setObjectName(u"community_resolution_helpbtn")

        self.horizontalLayout_12.addWidget(self.community_resolution_helpbtn)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_10)


        self.gridLayout_4.addLayout(self.horizontalLayout_12, 22, 2, 1, 3)

        self.global_alignment_helplbl = QLabel(self.scrollAreaWidgetContents_2)
        self.global_alignment_helplbl.setObjectName(u"global_alignment_helplbl")
        self.global_alignment_helplbl.setWordWrap(True)

        self.gridLayout_4.addWidget(self.global_alignment_helplbl, 8, 1, 1, 4)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.clus_local_pidentity_chk = QCheckBox(self.scrollAreaWidgetContents_2)
        self.clus_local_pidentity_chk.setObjectName(u"clus_local_pidentity_chk")

        self.horizontalLayout_8.addWidget(self.clus_local_pidentity_chk)

        self.clus_local_pidentity_spin = QSpinBox(self.scrollAreaWidgetContents_2)
        self.clus_local_pidentity_spin.setObjectName(u"clus_local_pidentity_spin")
        self.clus_local_pidentity_spin.setMinimum(0)
        self.clus_local_pidentity_spin.setMaximum(100)
        self.clus_local_pidentity_spin.setValue(50)

        self.horizontalLayout_8.addWidget(self.clus_local_pidentity_spin)

        self.clus_local_pidentity_helpbtn = QToolButton(self.scrollAreaWidgetContents_2)
        self.clus_local_pidentity_helpbtn.setObjectName(u"clus_local_pidentity_helpbtn")

        self.horizontalLayout_8.addWidget(self.clus_local_pidentity_helpbtn)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_6)


        self.gridLayout_4.addLayout(self.horizontalLayout_8, 14, 2, 1, 3)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.label = QLabel(self.scrollAreaWidgetContents_2)
        self.label.setObjectName(u"label")

        self.horizontalLayout_14.addWidget(self.label)

        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_12)


        self.gridLayout_4.addLayout(self.horizontalLayout_14, 6, 0, 1, 5)

        self.label_6 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_4.addWidget(self.label_6, 12, 2, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer, 24, 0, 1, 1)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_7 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_5.addWidget(self.label_7)

        self.global_alignment_helpbtn = QToolButton(self.scrollAreaWidgetContents_2)
        self.global_alignment_helpbtn.setObjectName(u"global_alignment_helpbtn")

        self.horizontalLayout_5.addWidget(self.global_alignment_helpbtn)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_4)


        self.gridLayout_4.addLayout(self.horizontalLayout_5, 7, 1, 1, 4)

        self.line_3 = QFrame(self.scrollAreaWidgetContents_2)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.gridLayout_4.addWidget(self.line_3, 5, 0, 1, 5)

        self.title_label = QLabel(self.scrollAreaWidgetContents_2)
        self.title_label.setObjectName(u"title_label")

        self.gridLayout_4.addWidget(self.title_label, 2, 0, 1, 2)

        self.label_9 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout_4.addWidget(self.label_9, 17, 2, 1, 2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.border_label = QLabel(self.scrollAreaWidgetContents_2)
        self.border_label.setObjectName(u"border_label")
        self.border_label.setWordWrap(False)

        self.horizontalLayout_3.addWidget(self.border_label)

        self.border_spin = QSpinBox(self.scrollAreaWidgetContents_2)
        self.border_spin.setObjectName(u"border_spin")
        self.border_spin.setMaximum(999999999)
        self.border_spin.setValue(75000)

        self.horizontalLayout_3.addWidget(self.border_spin)

        self.label_4 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_3.addWidget(self.label_4)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_5)


        self.gridLayout_4.addLayout(self.horizontalLayout_3, 4, 0, 1, 5)

        self.line_2 = QFrame(self.scrollAreaWidgetContents_2)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.gridLayout_4.addWidget(self.line_2, 1, 0, 1, 5)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents_2)

        self.verticalLayout.addWidget(self.scrollArea)

        self.widget_2 = QWidget(NeiviewCreator)
        self.widget_2.setObjectName(u"widget_2")
        self.gridLayout_2 = QGridLayout(self.widget_2)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 6, 0, 0)
        self.horizontalSpacer_17 = QSpacerItem(444, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_17, 2, 1, 1, 1)

        self.cancel_btn = QPushButton(self.widget_2)
        self.cancel_btn.setObjectName(u"cancel_btn")

        self.gridLayout_2.addWidget(self.cancel_btn, 2, 0, 1, 1)

        self.label_5 = QLabel(self.widget_2)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setWordWrap(True)

        self.gridLayout_2.addWidget(self.label_5, 1, 0, 1, 3)

        self.create_btn = QPushButton(self.widget_2)
        self.create_btn.setObjectName(u"create_btn")

        self.gridLayout_2.addWidget(self.create_btn, 2, 2, 1, 1)

        self.line = QFrame(self.widget_2)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout_2.addWidget(self.line, 0, 0, 1, 3)


        self.verticalLayout.addWidget(self.widget_2)


        self.retranslateUi(NeiviewCreator)

        QMetaObject.connectSlotsByName(NeiviewCreator)
    # setupUi

    def retranslateUi(self, NeiviewCreator):
        NeiviewCreator.setWindowTitle(QCoreApplication.translate("NeiviewCreator", u"Form", None))
        self.nneighborhoods_label.setText(QCoreApplication.translate("NeiviewCreator", u"Gene clusters to display:", None))
        self.nneighborhoods_displaylabel.setText(QCoreApplication.translate("NeiviewCreator", u"Error", None))
        self.community_detection_helplbl.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-style:italic; color:#424242;\">Community detection is used to identify groups formed via centroidal grouping based on inter-group similarities found using local alignment. The algorithm optimizes for </span><a href=\"https://en.wikipedia.org/wiki/Modularity_(networks)\"><span style=\" text-decoration: underline; color:#0000ff;\">modularity</span></a><span style=\" font-style:italic; color:#424242;\">.</span></p></body></html>", None))
        self.label_10.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">\u2022 Community detection (NetworkX)</span></p></body></html>", None))
        self.community_detection_helpbtn.setText(QCoreApplication.translate("NeiviewCreator", u"?", None))
        self.label_21.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-style:italic; color:#424242;\">Select one or more similarity thresholds to apply when clustering proteins.</span></p></body></html>", None))
        self.community_resolution_helplbl.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-style:italic; color:#393939;\">With higher resolution, modularity will favor the creation of larger, but likely more heterogenous groups. Conversely, lower resolution is more likely to result in smaller, but more homogenous protein groups.</span></p></body></html>", None))
        self.label_2.setText(QCoreApplication.translate("NeiviewCreator", u"Alignment identity threshold", None))
        self.clus_global_identity_spin.setSuffix(QCoreApplication.translate("NeiviewCreator", u"%", None))
        self.label_12.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p>Visualize ALL colocalized gene clusters, including intermediate genes not used as markers. </p><p><span style=\" font-style:italic;\">CluSeek will also include more space to the left and right of the colocalized region (75 000 bp by default). If you are visualizing large numbers of clusters (300 or more), you should consider decreasing this number.</span></p><p><span style=\" font-style:italic;\">Most of the settings below relate to a multi-step clustering algorithm used to identify similar proteins between clusters using sequence similarity. The default settings should suffice for most purposes.</span></p></body></html>", None))
        self.label_11.setText(QCoreApplication.translate("NeiviewCreator", u"Variable to use for weighing community relations", None))
        self.clus_local_pidentity_helplbl.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-style:italic; color:#393939;\">Identity is the percentage of amino acids that are identical between two compared sequences. Higher is better.</span></p></body></html>", None))
        self.label_8.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">\u2022 Local alignment (DIAMOND blastp)</span></p></body></html>", None))
        self.local_alignment_helpbtn.setText(QCoreApplication.translate("NeiviewCreator", u"?", None))
        self.clus_local_evalue_exponent_radio.setText(QCoreApplication.translate("NeiviewCreator", u"Local alignment E-value threshold", None))
        self.clus_local_evalue_exponent_spin.setPrefix(QCoreApplication.translate("NeiviewCreator", u"10^", None))
        self.clus_local_evalue_exponent_helpbtn.setText(QCoreApplication.translate("NeiviewCreator", u"?", None))
        self.clus_local_evalue_exponent_helplbl.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-style:italic; color:#393939;\">E-value is broadly speaking the likelihood of a given match occurring by chance. Thus, the more proteins are being compared, the higher E-value will be, even if the similarity between a given pair of sequences does not change. Lower is better.</span></p></body></html>", None))
        self.clus_local_bitscore_radio.setText(QCoreApplication.translate("NeiviewCreator", u"Local alignment bitscore threshold", None))
        self.clus_local_bitscore_helpbtn.setText(QCoreApplication.translate("NeiviewCreator", u"?", None))
        self.clus_local_bitscore_helplbl.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-style:italic; color:#393939;\">Bitsccore denotes the similarity of two sequences independently of the size of a database. Higher is better.</span></p></body></html>", None))
        self.local_alignment_helplbl.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-style:italic; color:#585858;\">Local alignment is used to find similarities between more distantly related proteins. Lower thresholds will create more interconnected similarity networks which be harder to reliably analyze, while higher thresholds may not find all relevant relationships.</span></p></body></html>", None))
        self.label_3.setText(QCoreApplication.translate("NeiviewCreator", u"Local alignment sensitivty mode", None))
        self.label_18.setText(QCoreApplication.translate("NeiviewCreator", u"Resolution", None))
        self.community_resolution_helpbtn.setText(QCoreApplication.translate("NeiviewCreator", u"?", None))
        self.global_alignment_helplbl.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-style:italic; color:#585858;\">A sequence alignment-based centroidal clustering algorithm. The resulting protein groups are the basic building blocks for higher order grouping of proteins based on local alignment / community detection. Beware that increasing the threshold may massively increase the number of subgroups and thus processing time.</span></p></body></html>", None))
        self.clus_local_pidentity_chk.setText(QCoreApplication.translate("NeiviewCreator", u"Local alignment identity threshold", None))
        self.clus_local_pidentity_spin.setSuffix(QCoreApplication.translate("NeiviewCreator", u"%", None))
        self.clus_local_pidentity_helpbtn.setText(QCoreApplication.translate("NeiviewCreator", u"?", None))
        self.label.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">Protein alignment criteria</span></p></body></html>", None))
        self.label_6.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">Alignment thresholds</span></p></body></html>", None))
        self.label_7.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">\u2022 Centroidal grouping (DIAMOND cluster)</span></p></body></html>", None))
        self.global_alignment_helpbtn.setText(QCoreApplication.translate("NeiviewCreator", u"?", None))
        self.title_label.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">General</span></p></body></html>", None))
        self.label_9.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">Other</span></p></body></html>", None))
        self.border_label.setText(QCoreApplication.translate("NeiviewCreator", u"Flanking region size: View an additional", None))
        self.border_spin.setSuffix(QCoreApplication.translate("NeiviewCreator", u" bp", None))
        self.label_4.setText(QCoreApplication.translate("NeiviewCreator", u"on either side of the outermost markers", None))
        self.cancel_btn.setText(QCoreApplication.translate("NeiviewCreator", u"Cancel", None))
        self.label_5.setText(QCoreApplication.translate("NeiviewCreator", u"<html><head/><body><p><span style=\" font-style:italic;\">CluSeek will download the sequences for all the relevant regions (gene clusters) from NCBI. This may take some time.</span></p></body></html>", None))
        self.create_btn.setText(QCoreApplication.translate("NeiviewCreator", u"Create", None))
    # retranslateUi

