# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'constraintsframe.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ConstraintsFrame(object):
    def setupUi(self, ConstraintsFrame):
        if not ConstraintsFrame.objectName():
            ConstraintsFrame.setObjectName(u"ConstraintsFrame")
        ConstraintsFrame.resize(1024, 822)
        ConstraintsFrame.setMinimumSize(QSize(0, 0))
        self.constraintsframe_lay = QGridLayout(ConstraintsFrame)
        self.constraintsframe_lay.setSpacing(6)
        self.constraintsframe_lay.setObjectName(u"constraintsframe_lay")
        self.constraintsframe_lay.setContentsMargins(3, -1, 3, 5)
        self.accset_container = QWidget(ConstraintsFrame)
        self.accset_container.setObjectName(u"accset_container")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.accset_container.sizePolicy().hasHeightForWidth())
        self.accset_container.setSizePolicy(sizePolicy)
        self.accset_container.setMinimumSize(QSize(290, 0))
        self.accset_container.setMaximumSize(QSize(340, 16777215))
        self.gridLayout = QGridLayout(self.accset_container)
        self.gridLayout.setSpacing(3)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(1, 1, 1, 1)
        self.verticalSpacer_4 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.gridLayout.addItem(self.verticalSpacer_4, 9, 0, 1, 1)

        self.label_5 = QLabel(self.accset_container)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 10, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.gridLayout.addItem(self.verticalSpacer_2, 2, 0, 1, 1)

        self.btn_showneighbors = QPushButton(self.accset_container)
        self.btn_showneighbors.setObjectName(u"btn_showneighbors")
        self.btn_showneighbors.setEnabled(False)
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_showneighbors.sizePolicy().hasHeightForWidth())
        self.btn_showneighbors.setSizePolicy(sizePolicy1)
        self.btn_showneighbors.setMinimumSize(QSize(0, 0))
        self.btn_showneighbors.setMaximumSize(QSize(2545555, 2545555))

        self.gridLayout.addWidget(self.btn_showneighbors, 11, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 12, 0, 1, 1)

        self.frame_2 = QFrame(self.accset_container)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setMinimumSize(QSize(0, 0))
        self.frame_2.setAutoFillBackground(False)
        self.frame_2.setFrameShape(QFrame.Panel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.frame_2.setLineWidth(2)
        self.gridLayout_3 = QGridLayout(self.frame_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(2, 2, 2, 2)
        self.horizontalSpacer = QSpacerItem(119, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer, 0, 0, 1, 1)

        self.btn_applyrules = QPushButton(self.frame_2)
        self.btn_applyrules.setObjectName(u"btn_applyrules")
        self.btn_applyrules.setMaximumSize(QSize(80, 30))
        self.btn_applyrules.setStyleSheet(u"")

        self.gridLayout_3.addWidget(self.btn_applyrules, 0, 1, 1, 1)

        self.horizontalSpacer_4 = QSpacerItem(118, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_4, 0, 2, 1, 1)

        self.btn_show_histogram = QPushButton(self.frame_2)
        self.btn_show_histogram.setObjectName(u"btn_show_histogram")
        self.btn_show_histogram.setEnabled(False)

        self.gridLayout_3.addWidget(self.btn_show_histogram, 2, 1, 1, 2)

        self.out_infolabel = QLabel(self.frame_2)
        self.out_infolabel.setObjectName(u"out_infolabel")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.out_infolabel.sizePolicy().hasHeightForWidth())
        self.out_infolabel.setSizePolicy(sizePolicy2)
        self.out_infolabel.setWordWrap(True)

        self.gridLayout_3.addWidget(self.out_infolabel, 1, 0, 1, 3)

        self.btn_viewresults = QPushButton(self.frame_2)
        self.btn_viewresults.setObjectName(u"btn_viewresults")
        self.btn_viewresults.setEnabled(False)

        self.gridLayout_3.addWidget(self.btn_viewresults, 3, 1, 1, 2)


        self.gridLayout.addWidget(self.frame_2, 8, 0, 1, 1)

        self.frame = QFrame(self.accset_container)
        self.frame.setObjectName(u"frame")
        self.frame.setMinimumSize(QSize(0, 10))
        self.frame.setFrameShape(QFrame.Panel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setLineWidth(2)
        self.frame.setMidLineWidth(0)
        self.gridLayout_4 = QGridLayout(self.frame)
        self.gridLayout_4.setSpacing(2)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(2, 2, 2, 2)
        self.derepfilterhelp_lbl = QLabel(self.frame)
        self.derepfilterhelp_lbl.setObjectName(u"derepfilterhelp_lbl")
        self.derepfilterhelp_lbl.setWordWrap(True)

        self.gridLayout_4.addWidget(self.derepfilterhelp_lbl, 4, 0, 1, 4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.derepfilter_combo = QComboBox(self.frame)
        self.derepfilter_combo.addItem("")
        self.derepfilter_combo.addItem("")
        self.derepfilter_combo.addItem("")
        self.derepfilter_combo.addItem("")
        self.derepfilter_combo.setObjectName(u"derepfilter_combo")
        self.derepfilter_combo.setMinimumSize(QSize(230, 0))

        self.horizontalLayout_3.addWidget(self.derepfilter_combo)

        self.derepfilterhelp_btn = QToolButton(self.frame)
        self.derepfilterhelp_btn.setObjectName(u"derepfilterhelp_btn")

        self.horizontalLayout_3.addWidget(self.derepfilterhelp_btn)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)


        self.gridLayout_4.addLayout(self.horizontalLayout_3, 3, 0, 1, 4)

        self.includewgshelp_lbl = QLabel(self.frame)
        self.includewgshelp_lbl.setObjectName(u"includewgshelp_lbl")
        sizePolicy.setHeightForWidth(self.includewgshelp_lbl.sizePolicy().hasHeightForWidth())
        self.includewgshelp_lbl.setSizePolicy(sizePolicy)
        self.includewgshelp_lbl.setWordWrap(True)

        self.gridLayout_4.addWidget(self.includewgshelp_lbl, 6, 0, 1, 4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.includewgs_chk = QCheckBox(self.frame)
        self.includewgs_chk.setObjectName(u"includewgs_chk")
        self.includewgs_chk.setChecked(True)

        self.horizontalLayout.addWidget(self.includewgs_chk)

        self.includewgshelp_btn = QToolButton(self.frame)
        self.includewgshelp_btn.setObjectName(u"includewgshelp_btn")

        self.horizontalLayout.addWidget(self.includewgshelp_btn)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.gridLayout_4.addLayout(self.horizontalLayout, 5, 0, 1, 4)

        self.ignoreunknowntxhelp_lbl = QLabel(self.frame)
        self.ignoreunknowntxhelp_lbl.setObjectName(u"ignoreunknowntxhelp_lbl")
        self.ignoreunknowntxhelp_lbl.setWordWrap(True)

        self.gridLayout_4.addWidget(self.ignoreunknowntxhelp_lbl, 8, 0, 1, 4)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.ignoreunknowntx_chk = QCheckBox(self.frame)
        self.ignoreunknowntx_chk.setObjectName(u"ignoreunknowntx_chk")

        self.horizontalLayout_4.addWidget(self.ignoreunknowntx_chk)

        self.ignoreunknowntxhelp_btn = QToolButton(self.frame)
        self.ignoreunknowntxhelp_btn.setObjectName(u"ignoreunknowntxhelp_btn")

        self.horizontalLayout_4.addWidget(self.ignoreunknowntxhelp_btn)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_6)


        self.gridLayout_4.addLayout(self.horizontalLayout_4, 7, 0, 1, 4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.txt_maxspacing = QLabel(self.frame)
        self.txt_maxspacing.setObjectName(u"txt_maxspacing")
        sizePolicy.setHeightForWidth(self.txt_maxspacing.sizePolicy().hasHeightForWidth())
        self.txt_maxspacing.setSizePolicy(sizePolicy)
        self.txt_maxspacing.setWordWrap(False)

        self.horizontalLayout_2.addWidget(self.txt_maxspacing)

        self.spin_maxdist = QSpinBox(self.frame)
        self.spin_maxdist.setObjectName(u"spin_maxdist")
        self.spin_maxdist.setMaximum(999999999)
        self.spin_maxdist.setSingleStep(1000)

        self.horizontalLayout_2.addWidget(self.spin_maxdist)

        self.maxdist_help_btn = QToolButton(self.frame)
        self.maxdist_help_btn.setObjectName(u"maxdist_help_btn")

        self.horizontalLayout_2.addWidget(self.maxdist_help_btn)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_5)


        self.gridLayout_4.addLayout(self.horizontalLayout_2, 1, 0, 1, 4)

        self.maxdist_help_lbl = QLabel(self.frame)
        self.maxdist_help_lbl.setObjectName(u"maxdist_help_lbl")
        self.maxdist_help_lbl.setWordWrap(True)

        self.gridLayout_4.addWidget(self.maxdist_help_lbl, 2, 0, 1, 4)


        self.gridLayout.addWidget(self.frame, 5, 0, 1, 1)

        self.frame_3 = QFrame(self.accset_container)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setMinimumSize(QSize(0, 0))
        self.frame_3.setFrameShape(QFrame.Panel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.frame_3.setLineWidth(2)
        self.gridLayout_5 = QGridLayout(self.frame_3)
        self.gridLayout_5.setSpacing(2)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(2, 2, 2, 2)
        self.scrl_accsets = QScrollArea(self.frame_3)
        self.scrl_accsets.setObjectName(u"scrl_accsets")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.scrl_accsets.sizePolicy().hasHeightForWidth())
        self.scrl_accsets.setSizePolicy(sizePolicy3)
        self.scrl_accsets.setMinimumSize(QSize(260, 0))
        self.scrl_accsets.setMaximumSize(QSize(16777215, 16777215))
        self.scrl_accsets.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrl_accsets.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.scrl_accsets.setWidgetResizable(True)
        self.accsets = QWidget()
        self.accsets.setObjectName(u"accsets")
        self.accsets.setGeometry(QRect(0, 0, 328, 69))
        self.lay_accsets = QFormLayout(self.accsets)
        self.lay_accsets.setObjectName(u"lay_accsets")
        self.lay_accsets.setHorizontalSpacing(1)
        self.lay_accsets.setVerticalSpacing(1)
        self.lay_accsets.setContentsMargins(3, 3, 3, 3)
        self.scrl_accsets.setWidget(self.accsets)

        self.gridLayout_5.addWidget(self.scrl_accsets, 0, 0, 1, 1)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.minscore_infolabel = QLabel(self.frame_3)
        self.minscore_infolabel.setObjectName(u"minscore_infolabel")

        self.gridLayout_2.addWidget(self.minscore_infolabel, 4, 0, 1, 1)

        self.minscore_spin = QSpinBox(self.frame_3)
        self.minscore_spin.setObjectName(u"minscore_spin")

        self.gridLayout_2.addWidget(self.minscore_spin, 4, 1, 1, 1)

        self.line = QFrame(self.frame_3)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout_2.addWidget(self.line, 2, 0, 1, 2)

        self.easyscore_chk = QCheckBox(self.frame_3)
        self.easyscore_chk.setObjectName(u"easyscore_chk")
        self.easyscore_chk.setChecked(True)

        self.gridLayout_2.addWidget(self.easyscore_chk, 3, 0, 1, 2)


        self.gridLayout_5.addLayout(self.gridLayout_2, 1, 0, 1, 1)


        self.gridLayout.addWidget(self.frame_3, 1, 0, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.gridLayout.addItem(self.verticalSpacer_3, 6, 0, 1, 1)

        self.label_4 = QLabel(self.accset_container)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 7, 0, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")

        self.gridLayout.addLayout(self.horizontalLayout_6, 4, 0, 1, 1)

        self.label_2 = QLabel(self.accset_container)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)

        self.label = QLabel(self.accset_container)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)


        self.constraintsframe_lay.addWidget(self.accset_container, 0, 0, 2, 1)

        self.line_2 = QFrame(ConstraintsFrame)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShadow(QFrame.Sunken)
        self.line_2.setLineWidth(2)
        self.line_2.setMidLineWidth(0)
        self.line_2.setFrameShape(QFrame.VLine)

        self.constraintsframe_lay.addWidget(self.line_2, 0, 1, 2, 1)

        self.tabplaceholder_lbl = QLabel(ConstraintsFrame)
        self.tabplaceholder_lbl.setObjectName(u"tabplaceholder_lbl")
        self.tabplaceholder_lbl.setAlignment(Qt.AlignCenter)
        self.tabplaceholder_lbl.setWordWrap(True)

        self.constraintsframe_lay.addWidget(self.tabplaceholder_lbl, 0, 2, 2, 1)


        self.retranslateUi(ConstraintsFrame)

        self.derepfilter_combo.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(ConstraintsFrame)
    # setupUi

    def retranslateUi(self, ConstraintsFrame):
        ConstraintsFrame.setWindowTitle(QCoreApplication.translate("ConstraintsFrame", u"Form", None))
        self.label_5.setText(QCoreApplication.translate("ConstraintsFrame", u"<html><head/><body><p><span style=\" font-size:9pt; font-weight:600;\">4. View and analyze gene clusters:</span></p></body></html>", None))
        self.btn_showneighbors.setText(QCoreApplication.translate("ConstraintsFrame", u"DISPLAY CLUSTER VIEW", None))
        self.btn_applyrules.setText(QCoreApplication.translate("ConstraintsFrame", u"COLOCALIZE", None))
        self.btn_show_histogram.setText(QCoreApplication.translate("ConstraintsFrame", u"Show BLASTP marker histogram", None))
        self.out_infolabel.setText(QCoreApplication.translate("ConstraintsFrame", u"No results yet! Select your marker proteins and press \"Colocalize!\"", None))
        self.btn_viewresults.setText(QCoreApplication.translate("ConstraintsFrame", u"View colocalization table", None))
        self.derepfilterhelp_lbl.setText(QCoreApplication.translate("ConstraintsFrame", u"<html><head/><body><p><span style=\" font-style:italic;\">Bypasses the &quot;one result per&quot; dereplication setting in cases where cluseek infers that multiple clusters belong to the same sequencing run. Thus, if a genome contains two or more copies of the searched cluster, you will see all of them in the results instead of just one.</span></p></body></html>", None))
        self.derepfilter_combo.setItemText(0, QCoreApplication.translate("ConstraintsFrame", u"Do not dereplicate", None))
        self.derepfilter_combo.setItemText(1, QCoreApplication.translate("ConstraintsFrame", u"Dereplicate to one result per strain", None))
        self.derepfilter_combo.setItemText(2, QCoreApplication.translate("ConstraintsFrame", u"Dereplicate to one result per species", None))
        self.derepfilter_combo.setItemText(3, QCoreApplication.translate("ConstraintsFrame", u"Dereplicate to one result per genus", None))

        self.derepfilterhelp_btn.setText(QCoreApplication.translate("ConstraintsFrame", u"?", None))
        self.includewgshelp_lbl.setText(QCoreApplication.translate("ConstraintsFrame", u"<html><head/><body><p><span style=\" font-style:italic;\">Bypasses the &quot;one result per&quot; dereplication setting in cases where cluseek infers that multiple clusters belong to the same sequencing run. Thus, if a genome contains two or more copies of the searched cluster, you will see all of them in the results instead of just one.</span></p></body></html>", None))
        self.includewgs_chk.setText(QCoreApplication.translate("ConstraintsFrame", u"Show all clusters in the same genome", None))
        self.includewgshelp_btn.setText(QCoreApplication.translate("ConstraintsFrame", u"?", None))
        self.ignoreunknowntxhelp_lbl.setText(QCoreApplication.translate("ConstraintsFrame", u"<html><head/><body><p><span style=\" font-style:italic;\">While dereplicating by taxonomy, ignore species with incomplete taxonomic information. For example, if dereplicating to one result per species, and only the genus of a sequence is known for a given result, that result will be ignored.</span></p></body></html>", None))
        self.ignoreunknowntx_chk.setText(QCoreApplication.translate("ConstraintsFrame", u"Ignore taxa with ambiguous lineage", None))
        self.ignoreunknowntxhelp_btn.setText(QCoreApplication.translate("ConstraintsFrame", u"?", None))
        self.txt_maxspacing.setText(QCoreApplication.translate("ConstraintsFrame", u"Maximum gene cluster size:", None))
#if QT_CONFIG(tooltip)
        self.spin_maxdist.setToolTip(QCoreApplication.translate("ConstraintsFrame", u"<html><head/><body><p>The maximum distance between individual queries required to find a genetic cluster.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.spin_maxdist.setSuffix(QCoreApplication.translate("ConstraintsFrame", u" bp", None))
        self.maxdist_help_btn.setText(QCoreApplication.translate("ConstraintsFrame", u"?", None))
        self.maxdist_help_lbl.setText(QCoreApplication.translate("ConstraintsFrame", u"<html><head/><body><p>Here defined as the maximum distance between the outermost markers. The default value corresponds to typical gene clusters.</p></body></html>", None))
        self.minscore_infolabel.setText(QCoreApplication.translate("ConstraintsFrame", u"Minimum Score:", None))
#if QT_CONFIG(tooltip)
        self.minscore_spin.setToolTip(QCoreApplication.translate("ConstraintsFrame", u"<html><head/><body><p>Only regions whose total score is at least equal to this value will be included in the results.</p><p>Each marker protein is only counted once, meaning that the maximum attainable score is the sum of all the positive scores of all the marker proteins.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.easyscore_chk.setText(QCoreApplication.translate("ConstraintsFrame", u"Automatic cluster scoring", None))
        self.label_4.setText(QCoreApplication.translate("ConstraintsFrame", u"<html><head/><body><p><span style=\" font-size:9pt; font-weight:600;\">3. Colocalize markers:</span></p></body></html>", None))
        self.label_2.setText(QCoreApplication.translate("ConstraintsFrame", u"<html><head/><body><p><span style=\" font-size:9pt; font-weight:600;\">2. Set other colocalization parameters:</span></p></body></html>", None))
        self.label.setText(QCoreApplication.translate("ConstraintsFrame", u"<html><head/><body><p><span style=\" font-size:9pt; font-weight:600; color:#000000;\">1. Select which markers to colocalize:</span></p></body></html>", None))
        self.tabplaceholder_lbl.setText(QCoreApplication.translate("ConstraintsFrame", u"<html><head/><body><p align=\"center\"><span style=\" font-weight:600;\">Please colocalize your data to unlock further analysis options.</span></p><p align=\"center\"><br/></p><p align=\"center\"><span style=\" font-style:italic;\">(Even if you have only one marker, this step is necessary.)</span></p></body></html>", None))
    # retranslateUi

