# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ClusterNetworkViewer2.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ClusterNetworkViewer2(object):
    def setupUi(self, ClusterNetworkViewer2):
        if not ClusterNetworkViewer2.objectName():
            ClusterNetworkViewer2.setObjectName(u"ClusterNetworkViewer2")
        ClusterNetworkViewer2.resize(1100, 662)
        self.gridLayout_8 = QGridLayout(ClusterNetworkViewer2)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.ui_frame = QWidget(ClusterNetworkViewer2)
        self.ui_frame.setObjectName(u"ui_frame")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ui_frame.sizePolicy().hasHeightForWidth())
        self.ui_frame.setSizePolicy(sizePolicy)
        self.gridLayout_7 = QGridLayout(self.ui_frame)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setHorizontalSpacing(6)
        self.gridLayout_7.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(self.ui_frame)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Panel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setLineWidth(1)
        self.frame.setMidLineWidth(1)
        self.gridLayout_3 = QGridLayout(self.frame)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.apply_size_changes_btn = QPushButton(self.frame)
        self.apply_size_changes_btn.setObjectName(u"apply_size_changes_btn")

        self.gridLayout_3.addWidget(self.apply_size_changes_btn, 4, 0, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(284, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_3, 4, 1, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.size_scaling_chk = QCheckBox(self.frame)
        self.size_scaling_chk.setObjectName(u"size_scaling_chk")

        self.horizontalLayout.addWidget(self.size_scaling_chk)

        self.size_scaling_dspin = QDoubleSpinBox(self.frame)
        self.size_scaling_dspin.setObjectName(u"size_scaling_dspin")
        self.size_scaling_dspin.setMinimum(-99999.000000000000000)
        self.size_scaling_dspin.setMaximum(10000.000000000000000)
        self.size_scaling_dspin.setValue(150.000000000000000)

        self.horizontalLayout.addWidget(self.size_scaling_dspin)

        self.label_4 = QLabel(self.frame)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout.addWidget(self.label_4)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.gridLayout_3.addLayout(self.horizontalLayout, 2, 0, 1, 2)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 2)

        self.widget_2 = QWidget(self.frame)
        self.widget_2.setObjectName(u"widget_2")
        self.gridLayout = QGridLayout(self.widget_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.widget_2)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.symbol_width_spin = QSpinBox(self.widget_2)
        self.symbol_width_spin.setObjectName(u"symbol_width_spin")
        self.symbol_width_spin.setMaximum(200)

        self.gridLayout.addWidget(self.symbol_width_spin, 0, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(230, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 2, 2, 1)

        self.label_2 = QLabel(self.widget_2)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.symbol_height_spin = QSpinBox(self.widget_2)
        self.symbol_height_spin.setObjectName(u"symbol_height_spin")
        self.symbol_height_spin.setMaximum(200)

        self.gridLayout.addWidget(self.symbol_height_spin, 1, 1, 1, 1)


        self.gridLayout_3.addWidget(self.widget_2, 1, 0, 1, 2)

        self.exact_frequency_counts_chk = QCheckBox(self.frame)
        self.exact_frequency_counts_chk.setObjectName(u"exact_frequency_counts_chk")

        self.gridLayout_3.addWidget(self.exact_frequency_counts_chk, 3, 0, 1, 2)


        self.gridLayout_7.addWidget(self.frame, 0, 0, 1, 1)

        self.frame_3 = QFrame(self.ui_frame)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.Panel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.gridLayout_5 = QGridLayout(self.frame_3)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.label_6 = QLabel(self.frame_3)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_5.addWidget(self.label_6, 0, 0, 1, 1)

        self.show_subset_standard_radio = QRadioButton(self.frame_3)
        self.show_subset_standard_radio.setObjectName(u"show_subset_standard_radio")
        self.show_subset_standard_radio.setChecked(True)

        self.gridLayout_5.addWidget(self.show_subset_standard_radio, 1, 0, 1, 1)

        self.show_subset_other_radio = QRadioButton(self.frame_3)
        self.show_subset_other_radio.setObjectName(u"show_subset_other_radio")
        self.show_subset_other_radio.setEnabled(False)

        self.gridLayout_5.addWidget(self.show_subset_other_radio, 3, 0, 1, 1)

        self.show_subset_localgroup_radio = QRadioButton(self.frame_3)
        self.show_subset_localgroup_radio.setObjectName(u"show_subset_localgroup_radio")

        self.gridLayout_5.addWidget(self.show_subset_localgroup_radio, 2, 0, 1, 1)

        self.label_9 = QLabel(self.frame_3)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setWordWrap(True)

        self.gridLayout_5.addWidget(self.label_9, 4, 0, 1, 1)


        self.gridLayout_7.addWidget(self.frame_3, 0, 2, 1, 1)

        self.frame_4 = QFrame(self.ui_frame)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.Panel)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.gridLayout_6 = QGridLayout(self.frame_4)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.zoom_out_btn = QPushButton(self.frame_4)
        self.zoom_out_btn.setObjectName(u"zoom_out_btn")

        self.gridLayout_6.addWidget(self.zoom_out_btn, 1, 1, 1, 1)

        self.zoom_in_btn = QPushButton(self.frame_4)
        self.zoom_in_btn.setObjectName(u"zoom_in_btn")

        self.gridLayout_6.addWidget(self.zoom_in_btn, 1, 0, 1, 1)

        self.label_7 = QLabel(self.frame_4)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_6.addWidget(self.label_7, 0, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.rearrange_btn = QPushButton(self.frame_4)
        self.rearrange_btn.setObjectName(u"rearrange_btn")

        self.horizontalLayout_2.addWidget(self.rearrange_btn)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)


        self.gridLayout_6.addLayout(self.horizontalLayout_2, 2, 0, 1, 2)


        self.gridLayout_7.addWidget(self.frame_4, 0, 4, 1, 1)

        self.frame_2 = QFrame(self.ui_frame)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Panel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.gridLayout_4 = QGridLayout(self.frame_2)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_5 = QLabel(self.frame_2)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_4.addWidget(self.label_5, 0, 0, 1, 1)

        self.groups_super_radio = QRadioButton(self.frame_2)
        self.groups_super_radio.setObjectName(u"groups_super_radio")
        self.groups_super_radio.setChecked(False)

        self.gridLayout_4.addWidget(self.groups_super_radio, 1, 0, 1, 1)

        self.groups_sub_radio = QRadioButton(self.frame_2)
        self.groups_sub_radio.setObjectName(u"groups_sub_radio")
        self.groups_sub_radio.setChecked(True)

        self.gridLayout_4.addWidget(self.groups_sub_radio, 2, 0, 1, 1)


        self.gridLayout_7.addWidget(self.frame_2, 0, 1, 1, 1)

        self.widget = QWidget(self.ui_frame)
        self.widget.setObjectName(u"widget")
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.horizontalLayout_3 = QHBoxLayout(self.widget)
        self.horizontalLayout_3.setSpacing(3)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.info_btn = QToolButton(self.widget)
        self.info_btn.setObjectName(u"info_btn")

        self.horizontalLayout_3.addWidget(self.info_btn)

        self.info_lbl = QLabel(self.widget)
        self.info_lbl.setObjectName(u"info_lbl")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.info_lbl.sizePolicy().hasHeightForWidth())
        self.info_lbl.setSizePolicy(sizePolicy1)
        self.info_lbl.setMinimumSize(QSize(0, 0))
        self.info_lbl.setMaximumSize(QSize(16777215, 16777215))
        self.info_lbl.setWordWrap(True)

        self.horizontalLayout_3.addWidget(self.info_lbl)


        self.gridLayout_7.addWidget(self.widget, 1, 0, 1, 5)

        self.horizontalSpacer_5 = QSpacerItem(249, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_7.addItem(self.horizontalSpacer_5, 0, 3, 1, 1)


        self.gridLayout_8.addWidget(self.ui_frame, 1, 0, 1, 1)

        self.canvas_scroller = QScrollArea(ClusterNetworkViewer2)
        self.canvas_scroller.setObjectName(u"canvas_scroller")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.canvas_scroller.sizePolicy().hasHeightForWidth())
        self.canvas_scroller.setSizePolicy(sizePolicy2)
        self.canvas_scroller.setWidgetResizable(True)
        self.canvas_scrollable = QWidget()
        self.canvas_scrollable.setObjectName(u"canvas_scrollable")
        self.canvas_scrollable.setGeometry(QRect(0, 0, 1080, 363))
        self.gridLayout_2 = QGridLayout(self.canvas_scrollable)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.canvas = QWidget(self.canvas_scrollable)
        self.canvas.setObjectName(u"canvas")

        self.gridLayout_2.addWidget(self.canvas, 0, 0, 1, 1)

        self.canvas_scroller.setWidget(self.canvas_scrollable)

        self.gridLayout_8.addWidget(self.canvas_scroller, 0, 0, 1, 1)


        self.retranslateUi(ClusterNetworkViewer2)

        QMetaObject.connectSlotsByName(ClusterNetworkViewer2)
    # setupUi

    def retranslateUi(self, ClusterNetworkViewer2):
        ClusterNetworkViewer2.setWindowTitle(QCoreApplication.translate("ClusterNetworkViewer2", u"Form", None))
        self.apply_size_changes_btn.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Apply Settings", None))
        self.size_scaling_chk.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Scale symbols based on frequency in dataset (", None))
        self.label_4.setText(QCoreApplication.translate("ClusterNetworkViewer2", u" )", None))
        self.label_3.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"<html><head/><body><p><span style=\" font-weight:600;\">Size settings</span></p></body></html>", None))
        self.label.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Symbol width", None))
        self.symbol_width_spin.setSuffix(QCoreApplication.translate("ClusterNetworkViewer2", u" px", None))
        self.label_2.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Symbol height", None))
        self.symbol_height_spin.setSuffix(QCoreApplication.translate("ClusterNetworkViewer2", u" px", None))
        self.exact_frequency_counts_chk.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Show exact frequency counts", None))
        self.label_6.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"<html><head/><body><p><span style=\" font-weight:600;\">Displayed data</span></p></body></html>", None))
        self.show_subset_standard_radio.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Show only group", None))
        self.show_subset_other_radio.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Other", None))
        self.show_subset_localgroup_radio.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Show local alignment network of group", None))
        self.label_9.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"<html><head/><body><p><span style=\" font-style:italic;\">The local alignment network includes not just your selected group, but also all related groups. If a group has no related groups, this option will do nothing.</span></p></body></html>", None))
        self.zoom_out_btn.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Zoom (-)", None))
        self.zoom_in_btn.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Zoom (+)", None))
        self.label_7.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"<html><head/><body><p><span style=\" font-weight:600;\">Control</span></p></body></html>", None))
        self.rearrange_btn.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Rearrange (randomly)", None))
        self.label_5.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"<html><head/><body><p><span style=\" font-weight:600;\">Labels</span></p></body></html>", None))
        self.groups_super_radio.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Labels denote group", None))
        self.groups_sub_radio.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"Labels denote subgroup", None))
        self.info_btn.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"?", None))
        self.info_lbl.setText(QCoreApplication.translate("ClusterNetworkViewer2", u"<html><head/><body><p><span style=\" font-style:italic;\">In this window, you can examine the composition of the protein </span><span style=\" font-weight:600; font-style:italic;\">groups</span><span style=\" font-style:italic;\"> you interact with elsewhere in CluSeek for a more fine-grained understanding of their composition. This is a network graph where each </span><span style=\" font-weight:600; font-style:italic;\">node</span><span style=\" font-style:italic;\"> is a </span><span style=\" font-weight:600; font-style:italic;\">sub-group</span><span style=\" font-style:italic;\"> comprised of one or more highly sequentially homogenous proteins (obtained via the DIAMOND cluster algorithm), and each </span><span style=\" font-weight:600; font-style:italic;\">edge</span><span style=\" font-style:italic;\"> represents a </span><span style=\" font-weight:600; font-style:italic;\">local (partial) similarity</span><span style=\" font-style:italic;\"> between two sub-groups (obtained via the DIAMOND blastp algorit"
                        "hm).</span></p><p><span style=\" font-style:italic;\">CluSeek has already grouped these </span><span style=\" font-weight:600; font-style:italic;\">sub-groups</span><span style=\" font-style:italic;\"> into </span><span style=\" font-weight:600; font-style:italic;\">groups</span><span style=\" font-style:italic;\"> using a community detection algorithm (NetworkX), however you can review and alter the grouping manually. You can view the composition of related groups via the appropriate setting in the </span><span style=\" font-weight:600; font-style:italic;\">Displayed data</span><span style=\" font-style:italic;\"> category, and you can create </span><span style=\" font-weight:600; font-style:italic;\">custom groups </span><span style=\" font-style:italic;\">by selecting one or more sub-groups, right clicking one of them and selecting the </span><span style=\" font-weight:600; font-style:italic;\">&quot;Group selected&quot;</span><span style=\" font-style:italic;\"> option. (This functionality works analogousl"
                        "y for merging entire groups, not just sub-groups.)</span></p><p><span style=\" font-style:italic;\">Note that due to local similarity being used, if </span><span style=\" font-weight:600; font-style:italic;\">A</span><span style=\" font-style:italic;\"> has a homology with </span><span style=\" font-weight:600; font-style:italic;\">B</span><span style=\" font-style:italic;\"> and </span><span style=\" font-weight:600; font-style:italic;\">B</span><span style=\" font-style:italic;\"> has a homology to </span><span style=\" font-weight:600; font-style:italic;\">C</span><span style=\" font-style:italic;\">, this does not necessarily mean that </span><span style=\" font-weight:600; font-style:italic;\">A</span><span style=\" font-style:italic;\"> has a homology to </span><span style=\" font-weight:600; font-style:italic;\">C</span><span style=\" font-style:italic;\">.</span></p></body></html>", None))
    # retranslateUi

