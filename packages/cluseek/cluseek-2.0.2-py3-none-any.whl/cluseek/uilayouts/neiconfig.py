# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'neiconfig.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_NeiConfig(object):
    def setupUi(self, NeiConfig):
        if not NeiConfig.objectName():
            NeiConfig.setObjectName(u"NeiConfig")
        NeiConfig.resize(432, 555)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(NeiConfig.sizePolicy().hasHeightForWidth())
        NeiConfig.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(NeiConfig)
        self.gridLayout.setObjectName(u"gridLayout")
        self.widget = QWidget(NeiConfig)
        self.widget.setObjectName(u"widget")
        self.verticalLayout = QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 0, 0, 0)
        self.cds_repr_radio = QRadioButton(self.widget)
        self.cds_repr_radio.setObjectName(u"cds_repr_radio")

        self.verticalLayout.addWidget(self.cds_repr_radio)

        self.cds_fixed_radio = QRadioButton(self.widget)
        self.cds_fixed_radio.setObjectName(u"cds_fixed_radio")

        self.verticalLayout.addWidget(self.cds_fixed_radio)


        self.gridLayout.addWidget(self.widget, 5, 1, 1, 1)

        self.widget_2 = QWidget(NeiConfig)
        self.widget_2.setObjectName(u"widget_2")
        self.verticalLayout_2 = QVBoxLayout(self.widget_2)
        self.verticalLayout_2.setSpacing(3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(20, 1, 1, 1)
        self.pglabels_all_radio = QRadioButton(self.widget_2)
        self.pglabels_all_radio.setObjectName(u"pglabels_all_radio")

        self.verticalLayout_2.addWidget(self.pglabels_all_radio)

        self.pglabels_custom_radio = QRadioButton(self.widget_2)
        self.pglabels_custom_radio.setObjectName(u"pglabels_custom_radio")

        self.verticalLayout_2.addWidget(self.pglabels_custom_radio)

        self.pglabels_none_radio = QRadioButton(self.widget_2)
        self.pglabels_none_radio.setObjectName(u"pglabels_none_radio")

        self.verticalLayout_2.addWidget(self.pglabels_none_radio)


        self.gridLayout.addWidget(self.widget_2, 18, 1, 1, 1)

        self.line_3 = QFrame(NeiConfig)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_3, 16, 1, 1, 1)

        self.label = QLabel(NeiConfig)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 3, 0, 1, 2)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.io_cancel_btn = QPushButton(NeiConfig)
        self.io_cancel_btn.setObjectName(u"io_cancel_btn")

        self.horizontalLayout_6.addWidget(self.io_cancel_btn)

        self.horizontalSpacer_5 = QSpacerItem(20, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_5)

        self.io_apply_btn = QPushButton(NeiConfig)
        self.io_apply_btn.setObjectName(u"io_apply_btn")

        self.horizontalLayout_6.addWidget(self.io_apply_btn)


        self.gridLayout.addLayout(self.horizontalLayout_6, 25, 0, 1, 2)

        self.label_9 = QLabel(NeiConfig)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout.addWidget(self.label_9, 21, 0, 1, 2)

        self.headers_taxon_chk = QCheckBox(NeiConfig)
        self.headers_taxon_chk.setObjectName(u"headers_taxon_chk")

        self.gridLayout.addWidget(self.headers_taxon_chk, 22, 1, 1, 1)

        self.label_2 = QLabel(NeiConfig)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 2)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_6, 18, 0, 1, 1)

        self.label_13 = QLabel(NeiConfig)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout.addWidget(self.label_13, 17, 1, 1, 1)

        self.label_12 = QLabel(NeiConfig)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout.addWidget(self.label_12, 4, 1, 1, 1)

        self.headers_region_chk = QCheckBox(NeiConfig)
        self.headers_region_chk.setObjectName(u"headers_region_chk")

        self.gridLayout.addWidget(self.headers_region_chk, 23, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 26, 0, 1, 2)

        self.headers_tags_chk = QCheckBox(NeiConfig)
        self.headers_tags_chk.setObjectName(u"headers_tags_chk")

        self.gridLayout.addWidget(self.headers_tags_chk, 24, 1, 1, 1)

        self.line = QFrame(NeiConfig)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line, 7, 1, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(4)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_8 = QLabel(NeiConfig)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_4.addWidget(self.label_8)

        self.cds_bpscaling_spin = QSpinBox(NeiConfig)
        self.cds_bpscaling_spin.setObjectName(u"cds_bpscaling_spin")
        self.cds_bpscaling_spin.setMaximum(9999)

        self.horizontalLayout_4.addWidget(self.cds_bpscaling_spin)

        self.label_3 = QLabel(NeiConfig)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_4.addWidget(self.label_3)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)


        self.gridLayout.addLayout(self.horizontalLayout_4, 13, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(45, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 5, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_4 = QLabel(NeiConfig)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout.addWidget(self.label_4)

        self.cds_width_spin = QSpinBox(NeiConfig)
        self.cds_width_spin.setObjectName(u"cds_width_spin")
        self.cds_width_spin.setMaximum(1000)

        self.horizontalLayout.addWidget(self.cds_width_spin)

        self.label_6 = QLabel(NeiConfig)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout.addWidget(self.label_6)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout, 11, 1, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(4)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_5 = QLabel(NeiConfig)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_3.addWidget(self.label_5)

        self.cds_height_spin = QSpinBox(NeiConfig)
        self.cds_height_spin.setObjectName(u"cds_height_spin")
        self.cds_height_spin.setMaximum(1000)

        self.horizontalLayout_3.addWidget(self.cds_height_spin)

        self.label_7 = QLabel(NeiConfig)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_3.addWidget(self.label_7)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.gridLayout.addLayout(self.horizontalLayout_3, 12, 1, 1, 1)

        self.widget_3 = QWidget(NeiConfig)
        self.widget_3.setObjectName(u"widget_3")
        sizePolicy.setHeightForWidth(self.widget_3.sizePolicy().hasHeightForWidth())
        self.widget_3.setSizePolicy(sizePolicy)
        self.widget_3.setMinimumSize(QSize(0, 10))
        self.verticalLayout_3 = QVBoxLayout(self.widget_3)
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(20, 1, 1, 1)
        self.arrowshape_notched_radio = QRadioButton(self.widget_3)
        self.arrowshape_notched_radio.setObjectName(u"arrowshape_notched_radio")

        self.verticalLayout_3.addWidget(self.arrowshape_notched_radio)

        self.arrowshape_standard_radio = QRadioButton(self.widget_3)
        self.arrowshape_standard_radio.setObjectName(u"arrowshape_standard_radio")

        self.verticalLayout_3.addWidget(self.arrowshape_standard_radio)

        self.arrowshape_compact_radio = QRadioButton(self.widget_3)
        self.arrowshape_compact_radio.setObjectName(u"arrowshape_compact_radio")

        self.verticalLayout_3.addWidget(self.arrowshape_compact_radio)

        self.label_11 = QLabel(self.widget_3)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.label_11)


        self.gridLayout.addWidget(self.widget_3, 9, 1, 1, 1)

        self.label_10 = QLabel(NeiConfig)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout.addWidget(self.label_10, 8, 1, 1, 1)


        self.retranslateUi(NeiConfig)

        QMetaObject.connectSlotsByName(NeiConfig)
    # setupUi

    def retranslateUi(self, NeiConfig):
        NeiConfig.setWindowTitle(QCoreApplication.translate("NeiConfig", u"Form", None))
        self.cds_repr_radio.setText(QCoreApplication.translate("NeiConfig", u"Representative (scales with sequence length/position in sequence)", None))
        self.cds_fixed_radio.setText(QCoreApplication.translate("NeiConfig", u"Simplified (fixed sizes, positions)", None))
        self.pglabels_all_radio.setText(QCoreApplication.translate("NeiConfig", u"Show all protein group labels", None))
        self.pglabels_custom_radio.setText(QCoreApplication.translate("NeiConfig", u"Show only custom protein group labels", None))
        self.pglabels_none_radio.setText(QCoreApplication.translate("NeiConfig", u"Do not show any protein group labels", None))
        self.label.setText(QCoreApplication.translate("NeiConfig", u"<html><head/><body><p><span style=\" font-weight:600;\">Coding sequence representation</span></p></body></html>", None))
        self.io_cancel_btn.setText(QCoreApplication.translate("NeiConfig", u"Cancel", None))
        self.io_apply_btn.setText(QCoreApplication.translate("NeiConfig", u"Apply", None))
        self.label_9.setText(QCoreApplication.translate("NeiConfig", u"<html><head/><body><p><span style=\" font-weight:600;\">Gene cluster headers</span></p></body></html>", None))
        self.headers_taxon_chk.setText(QCoreApplication.translate("NeiConfig", u"Display organism name", None))
        self.label_2.setText(QCoreApplication.translate("NeiConfig", u"<html><head/><body><p><span style=\" font-size:12pt; font-weight:600;\">Cluster view configuration</span></p></body></html>", None))
        self.label_13.setText(QCoreApplication.translate("NeiConfig", u"Protein group labels:", None))
        self.label_12.setText(QCoreApplication.translate("NeiConfig", u"Scale:", None))
        self.headers_region_chk.setText(QCoreApplication.translate("NeiConfig", u"Display region/sequence accession code", None))
        self.headers_tags_chk.setText(QCoreApplication.translate("NeiConfig", u"Display user-assigned tags", None))
        self.label_8.setText(QCoreApplication.translate("NeiConfig", u"Sequence size scaling:", None))
        self.label_3.setText(QCoreApplication.translate("NeiConfig", u"base pairs per pixel", None))
        self.label_4.setText(QCoreApplication.translate("NeiConfig", u"Default width:", None))
        self.label_6.setText(QCoreApplication.translate("NeiConfig", u"pixels (ignored in representative mode)", None))
        self.label_5.setText(QCoreApplication.translate("NeiConfig", u"Default height:", None))
        self.label_7.setText(QCoreApplication.translate("NeiConfig", u"pixels", None))
        self.arrowshape_notched_radio.setText(QCoreApplication.translate("NeiConfig", u"Notched", None))
        self.arrowshape_standard_radio.setText(QCoreApplication.translate("NeiConfig", u"Standard", None))
        self.arrowshape_compact_radio.setText(QCoreApplication.translate("NeiConfig", u"Compact", None))
        self.label_11.setText(QCoreApplication.translate("NeiConfig", u"<html><head/><body><p><span style=\" font-style:italic;\">Compact arrows are intended to maximize the number of sequences on screen while retaining readability. For best results, decrease the default arrow height when using them.</span></p></body></html>", None))
        self.label_10.setText(QCoreApplication.translate("NeiConfig", u"<html><head/><body><p>Protein arrow shape:</p></body></html>", None))
    # retranslateUi

