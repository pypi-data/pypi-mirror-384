# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'neiexport.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_NeiExport(object):
    def setupUi(self, NeiExport):
        if not NeiExport.objectName():
            NeiExport.setObjectName(u"NeiExport")
        NeiExport.resize(1025, 740)
        self.gridLayout_7 = QGridLayout(NeiExport)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.frame = QFrame(NeiExport)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Panel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.gridLayout_4 = QGridLayout(self.frame)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.line_2 = QFrame(self.frame)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.gridLayout_4.addWidget(self.line_2, 1, 0, 1, 3)

        self.format_combo = QComboBox(self.frame)
        self.format_combo.setObjectName(u"format_combo")

        self.gridLayout_4.addWidget(self.format_combo, 0, 1, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(257, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_3, 0, 2, 1, 1)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.gridLayout_4.addWidget(self.label, 0, 0, 1, 1)

        self.format_stack = QStackedWidget(self.frame)
        self.format_stack.setObjectName(u"format_stack")
        self.gbsettings_frame = QWidget()
        self.gbsettings_frame.setObjectName(u"gbsettings_frame")
        self.gridLayout = QGridLayout(self.gbsettings_frame)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(9, 9, 9, 9)
        self.label_10 = QLabel(self.gbsettings_frame)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setWordWrap(True)

        self.gridLayout.addWidget(self.label_10, 0, 0, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_3, 1, 0, 1, 1)

        self.format_stack.addWidget(self.gbsettings_frame)
        self.pngsettings_frame = QWidget()
        self.pngsettings_frame.setObjectName(u"pngsettings_frame")
        self.gridLayout_2 = QGridLayout(self.pngsettings_frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_9 = QLabel(self.pngsettings_frame)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout_2.addWidget(self.label_9, 1, 1, 1, 1)

        self.png_qualslider = QSlider(self.pngsettings_frame)
        self.png_qualslider.setObjectName(u"png_qualslider")
        self.png_qualslider.setMaximum(100)
        self.png_qualslider.setValue(70)
        self.png_qualslider.setOrientation(Qt.Horizontal)

        self.gridLayout_2.addWidget(self.png_qualslider, 2, 1, 1, 3)

        self.label_7 = QLabel(self.pngsettings_frame)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_2.addWidget(self.label_7, 2, 4, 1, 1)

        self.label_5 = QLabel(self.pngsettings_frame)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_2.addWidget(self.label_5, 2, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 439, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 7, 0, 1, 3)

        self.label_6 = QLabel(self.pngsettings_frame)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setWordWrap(True)

        self.gridLayout_2.addWidget(self.label_6, 3, 0, 1, 5)

        self.label_8 = QLabel(self.pngsettings_frame)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout_2.addWidget(self.label_8, 1, 0, 1, 1)

        self.label_13 = QLabel(self.pngsettings_frame)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout_2.addWidget(self.label_13, 0, 0, 1, 5)

        self.line_3 = QFrame(self.pngsettings_frame)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.gridLayout_2.addWidget(self.line_3, 4, 0, 1, 5)

        self.label_4 = QLabel(self.pngsettings_frame)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_2.addWidget(self.label_4, 5, 0, 1, 1)

        self.png_transparent = QCheckBox(self.pngsettings_frame)
        self.png_transparent.setObjectName(u"png_transparent")

        self.gridLayout_2.addWidget(self.png_transparent, 6, 0, 1, 5)

        self.format_stack.addWidget(self.pngsettings_frame)
        self.svgsettings_frame = QWidget()
        self.svgsettings_frame.setObjectName(u"svgsettings_frame")
        self.gridLayout_3 = QGridLayout(self.svgsettings_frame)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_26 = QLabel(self.svgsettings_frame)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setAlignment(Qt.AlignHCenter|Qt.AlignTop)

        self.gridLayout_3.addWidget(self.label_26, 0, 0, 1, 1)

        self.format_stack.addWidget(self.svgsettings_frame)
        self.excelsettings_frame = QWidget()
        self.excelsettings_frame.setObjectName(u"excelsettings_frame")
        self.gridLayout_5 = QGridLayout(self.excelsettings_frame)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.label_15 = QLabel(self.excelsettings_frame)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_5.addWidget(self.label_15, 5, 0, 1, 2)

        self.label_14 = QLabel(self.excelsettings_frame)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_5.addWidget(self.label_14, 0, 0, 1, 1)

        self.line = QFrame(self.excelsettings_frame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout_5.addWidget(self.line, 4, 0, 1, 2)

        self.cellcontents_lay = QVBoxLayout()
        self.cellcontents_lay.setObjectName(u"cellcontents_lay")

        self.gridLayout_5.addLayout(self.cellcontents_lay, 7, 0, 1, 2)

        self.xlsx_separator = QLineEdit(self.excelsettings_frame)
        self.xlsx_separator.setObjectName(u"xlsx_separator")

        self.gridLayout_5.addWidget(self.xlsx_separator, 10, 1, 1, 1)

        self.commentcontents_lay = QVBoxLayout()
        self.commentcontents_lay.setObjectName(u"commentcontents_lay")

        self.gridLayout_5.addLayout(self.commentcontents_lay, 9, 0, 1, 2)

        self.label_16 = QLabel(self.excelsettings_frame)
        self.label_16.setObjectName(u"label_16")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_16.sizePolicy().hasHeightForWidth())
        self.label_16.setSizePolicy(sizePolicy)

        self.gridLayout_5.addWidget(self.label_16, 6, 0, 1, 1)

        self.label_17 = QLabel(self.excelsettings_frame)
        self.label_17.setObjectName(u"label_17")

        self.gridLayout_5.addWidget(self.label_17, 10, 0, 1, 1)

        self.xlsx_transpose = QCheckBox(self.excelsettings_frame)
        self.xlsx_transpose.setObjectName(u"xlsx_transpose")
        self.xlsx_transpose.setChecked(True)

        self.gridLayout_5.addWidget(self.xlsx_transpose, 2, 0, 1, 2)

        self.label_18 = QLabel(self.excelsettings_frame)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_5.addWidget(self.label_18, 8, 0, 1, 2)

        self.xlsx_align = QCheckBox(self.excelsettings_frame)
        self.xlsx_align.setObjectName(u"xlsx_align")
        self.xlsx_align.setChecked(True)

        self.gridLayout_5.addWidget(self.xlsx_align, 1, 0, 1, 2)

        self.xlsx_condensetags = QCheckBox(self.excelsettings_frame)
        self.xlsx_condensetags.setObjectName(u"xlsx_condensetags")

        self.gridLayout_5.addWidget(self.xlsx_condensetags, 3, 0, 1, 2)

        self.format_stack.addWidget(self.excelsettings_frame)
        self.fastasettings_frame = QWidget()
        self.fastasettings_frame.setObjectName(u"fastasettings_frame")
        self.gridLayout_12 = QGridLayout(self.fastasettings_frame)
        self.gridLayout_12.setObjectName(u"gridLayout_12")
        self.label_11 = QLabel(self.fastasettings_frame)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setAlignment(Qt.AlignHCenter|Qt.AlignTop)

        self.gridLayout_12.addWidget(self.label_11, 0, 0, 1, 1)

        self.format_stack.addWidget(self.fastasettings_frame)
        self.gmlsettings_frame = QWidget()
        self.gmlsettings_frame.setObjectName(u"gmlsettings_frame")
        self.gridLayout_13 = QGridLayout(self.gmlsettings_frame)
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.gml_cutoff_slider = QSlider(self.gmlsettings_frame)
        self.gml_cutoff_slider.setObjectName(u"gml_cutoff_slider")
        self.gml_cutoff_slider.setMaximum(100)
        self.gml_cutoff_slider.setValue(15)
        self.gml_cutoff_slider.setOrientation(Qt.Horizontal)
        self.gml_cutoff_slider.setTickPosition(QSlider.TicksBelow)
        self.gml_cutoff_slider.setTickInterval(10)

        self.gridLayout_13.addWidget(self.gml_cutoff_slider, 2, 1, 1, 1)

        self.label_12 = QLabel(self.gmlsettings_frame)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout_13.addWidget(self.label_12, 2, 0, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_13.addItem(self.verticalSpacer_4, 4, 1, 1, 1)

        self.label_24 = QLabel(self.gmlsettings_frame)
        self.label_24.setObjectName(u"label_24")
        self.label_24.setWordWrap(True)

        self.gridLayout_13.addWidget(self.label_24, 0, 0, 1, 3)

        self.label_23 = QLabel(self.gmlsettings_frame)
        self.label_23.setObjectName(u"label_23")

        self.gridLayout_13.addWidget(self.label_23, 2, 2, 1, 1)

        self.label_25 = QLabel(self.gmlsettings_frame)
        self.label_25.setObjectName(u"label_25")

        self.gridLayout_13.addWidget(self.label_25, 1, 0, 1, 1)

        self.gml_metric_combo = QComboBox(self.gmlsettings_frame)
        self.gml_metric_combo.addItem("")
        self.gml_metric_combo.setObjectName(u"gml_metric_combo")
        self.gml_metric_combo.setEnabled(False)

        self.gridLayout_13.addWidget(self.gml_metric_combo, 1, 1, 1, 1)

        self.format_stack.addWidget(self.gmlsettings_frame)
        self.gmlprotsettings_frame = QWidget()
        self.gmlprotsettings_frame.setObjectName(u"gmlprotsettings_frame")
        self.gridLayout_14 = QGridLayout(self.gmlprotsettings_frame)
        self.gridLayout_14.setObjectName(u"gridLayout_14")
        self.gmlprot_relatedproteins_chk = QCheckBox(self.gmlprotsettings_frame)
        self.gmlprot_relatedproteins_chk.setObjectName(u"gmlprot_relatedproteins_chk")

        self.gridLayout_14.addWidget(self.gmlprot_relatedproteins_chk, 1, 0, 1, 1)

        self.label_27 = QLabel(self.gmlprotsettings_frame)
        self.label_27.setObjectName(u"label_27")
        sizePolicy.setHeightForWidth(self.label_27.sizePolicy().hasHeightForWidth())
        self.label_27.setSizePolicy(sizePolicy)
        self.label_27.setWordWrap(True)

        self.gridLayout_14.addWidget(self.label_27, 2, 0, 1, 1)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_14.addItem(self.verticalSpacer_5, 3, 0, 1, 1)

        self.label_28 = QLabel(self.gmlprotsettings_frame)
        self.label_28.setObjectName(u"label_28")
        self.label_28.setWordWrap(True)

        self.gridLayout_14.addWidget(self.label_28, 0, 0, 1, 1)

        self.format_stack.addWidget(self.gmlprotsettings_frame)

        self.gridLayout_4.addWidget(self.format_stack, 2, 0, 1, 3)


        self.gridLayout_7.addWidget(self.frame, 1, 2, 1, 2)

        self.save_btn = QPushButton(NeiExport)
        self.save_btn.setObjectName(u"save_btn")

        self.gridLayout_7.addWidget(self.save_btn, 2, 3, 1, 1)

        self.cancel_btn = QPushButton(NeiExport)
        self.cancel_btn.setObjectName(u"cancel_btn")

        self.gridLayout_7.addWidget(self.cancel_btn, 2, 0, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(458, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_7.addItem(self.horizontalSpacer_2, 2, 1, 1, 2)

        self.filesaved_lbl = QLabel(NeiExport)
        self.filesaved_lbl.setObjectName(u"filesaved_lbl")
        self.filesaved_lbl.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_7.addWidget(self.filesaved_lbl, 3, 0, 1, 4)

        self.exportingfrom_lbl = QLabel(NeiExport)
        self.exportingfrom_lbl.setObjectName(u"exportingfrom_lbl")

        self.gridLayout_7.addWidget(self.exportingfrom_lbl, 0, 0, 1, 4)

        self.frame_2 = QFrame(NeiExport)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Panel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.gridLayout_6 = QGridLayout(self.frame_2)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.horizontalSpacer_6 = QSpacerItem(198, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_6.addItem(self.horizontalSpacer_6, 0, 2, 1, 1)

        self.export_combo = QComboBox(self.frame_2)
        self.export_combo.setObjectName(u"export_combo")

        self.gridLayout_6.addWidget(self.export_combo, 0, 1, 1, 1)

        self.label_3 = QLabel(self.frame_2)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_6.addWidget(self.label_3, 0, 0, 1, 1)

        self.export_stack = QStackedWidget(self.frame_2)
        self.export_stack.setObjectName(u"export_stack")
        sizePolicy.setHeightForWidth(self.export_stack.sizePolicy().hasHeightForWidth())
        self.export_stack.setSizePolicy(sizePolicy)
        self.exportclusters_frame = QWidget()
        self.exportclusters_frame.setObjectName(u"exportclusters_frame")
        self.gridLayout_10 = QGridLayout(self.exportclusters_frame)
        self.gridLayout_10.setSpacing(3)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.gridLayout_10.setContentsMargins(0, 0, 0, 0)
        self.widget_2 = QWidget(self.exportclusters_frame)
        self.widget_2.setObjectName(u"widget_2")
        self.gridLayout_8 = QGridLayout(self.widget_2)
        self.gridLayout_8.setSpacing(3)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_19 = QLabel(self.widget_2)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout_8.addWidget(self.label_19, 0, 0, 1, 2)

        self.clusters_checked_radio = QRadioButton(self.widget_2)
        self.clusters_checked_radio.setObjectName(u"clusters_checked_radio")

        self.gridLayout_8.addWidget(self.clusters_checked_radio, 2, 1, 1, 1)

        self.clusters_all_radio = QRadioButton(self.widget_2)
        self.clusters_all_radio.setObjectName(u"clusters_all_radio")
        self.clusters_all_radio.setChecked(True)

        self.gridLayout_8.addWidget(self.clusters_all_radio, 1, 1, 1, 1)

        self.horizontalSpacer_4 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.gridLayout_8.addItem(self.horizontalSpacer_4, 1, 0, 1, 1)


        self.gridLayout_10.addWidget(self.widget_2, 0, 0, 1, 1)

        self.widget_4 = QWidget(self.exportclusters_frame)
        self.widget_4.setObjectName(u"widget_4")
        self.gridLayout_9 = QGridLayout(self.widget_4)
        self.gridLayout_9.setSpacing(3)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.gridLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_20 = QLabel(self.widget_4)
        self.label_20.setObjectName(u"label_20")

        self.gridLayout_9.addWidget(self.label_20, 0, 0, 1, 2)

        self.horizontalSpacer_5 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.gridLayout_9.addItem(self.horizontalSpacer_5, 1, 0, 1, 1)

        self.clusters_full_radio = QRadioButton(self.widget_4)
        self.clusters_full_radio.setObjectName(u"clusters_full_radio")
        self.clusters_full_radio.setChecked(True)

        self.gridLayout_9.addWidget(self.clusters_full_radio, 1, 1, 1, 1)

        self.clusters_highlighted_radio = QRadioButton(self.widget_4)
        self.clusters_highlighted_radio.setObjectName(u"clusters_highlighted_radio")

        self.gridLayout_9.addWidget(self.clusters_highlighted_radio, 2, 1, 1, 1)


        self.gridLayout_10.addWidget(self.widget_4, 1, 0, 1, 1)

        self.label_2 = QLabel(self.exportclusters_frame)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setWordWrap(True)

        self.gridLayout_10.addWidget(self.label_2, 2, 0, 1, 1)

        self.export_stack.addWidget(self.exportclusters_frame)
        self.exportproteins_frame = QWidget()
        self.exportproteins_frame.setObjectName(u"exportproteins_frame")
        self.horizontalLayout_4 = QHBoxLayout(self.exportproteins_frame)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.widget_3 = QWidget(self.exportproteins_frame)
        self.widget_3.setObjectName(u"widget_3")
        self.gridLayout_11 = QGridLayout(self.widget_3)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.label_21 = QLabel(self.widget_3)
        self.label_21.setObjectName(u"label_21")

        self.gridLayout_11.addWidget(self.label_21, 0, 0, 1, 2)

        self.horizontalSpacer_7 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.gridLayout_11.addItem(self.horizontalSpacer_7, 1, 0, 1, 1)

        self.proteins_clusters_checked_radio = QCheckBox(self.widget_3)
        self.proteins_clusters_checked_radio.setObjectName(u"proteins_clusters_checked_radio")

        self.gridLayout_11.addWidget(self.proteins_clusters_checked_radio, 1, 1, 1, 1)

        self.proteins_selected_prgroups_radio = QCheckBox(self.widget_3)
        self.proteins_selected_prgroups_radio.setObjectName(u"proteins_selected_prgroups_radio")

        self.gridLayout_11.addWidget(self.proteins_selected_prgroups_radio, 2, 1, 1, 1)

        self.proteins_highlighted_radio = QCheckBox(self.widget_3)
        self.proteins_highlighted_radio.setObjectName(u"proteins_highlighted_radio")

        self.gridLayout_11.addWidget(self.proteins_highlighted_radio, 3, 1, 1, 1)

        self.label_22 = QLabel(self.widget_3)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setWordWrap(True)

        self.gridLayout_11.addWidget(self.label_22, 4, 0, 1, 2)


        self.horizontalLayout_4.addWidget(self.widget_3)

        self.export_stack.addWidget(self.exportproteins_frame)

        self.gridLayout_6.addWidget(self.export_stack, 1, 0, 1, 3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_6.addItem(self.verticalSpacer_2, 2, 0, 1, 1)


        self.gridLayout_7.addWidget(self.frame_2, 1, 0, 1, 2)


        self.retranslateUi(NeiExport)

        self.format_stack.setCurrentIndex(6)
        self.export_stack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(NeiExport)
    # setupUi

    def retranslateUi(self, NeiExport):
        NeiExport.setWindowTitle(QCoreApplication.translate("NeiExport", u"Form", None))
        self.label.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-weight:600;\">Format:</span></p></body></html>", None))
        self.label_10.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-style:italic;\">Note that as a single GenBank file cannot contain multiple sequences.</span></p><p><span style=\" font-weight:600; font-style:italic;\">THEREFORE, CLUSEEK WILL GENERATE MANY FILES WITH NAMES DERIVED FROM THE ONE YOU SPECIFY AFTER CLICKING &quot;Save Output&quot;</span></p></body></html>", None))
        self.label_9.setText(QCoreApplication.translate("NeiExport", u"N/A", None))
        self.label_7.setText(QCoreApplication.translate("NeiExport", u"High Quality", None))
        self.label_5.setText(QCoreApplication.translate("NeiExport", u"Poor Quality", None))
        self.label_6.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-style:italic;\">Warning: Large, high quality images may be hundreds of megabytes in size!</span></p></body></html>", None))
        self.label_8.setText(QCoreApplication.translate("NeiExport", u"Image resolution:", None))
        self.label_13.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-weight:600;\">Resolution and quality</span></p></body></html>", None))
        self.label_4.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-weight:600;\">Other</span></p></body></html>", None))
        self.png_transparent.setText(QCoreApplication.translate("NeiExport", u"Transparent Background", None))
        self.label_26.setText(QCoreApplication.translate("NeiExport", u"No settings available for the svg format export", None))
        self.label_15.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-weight:600;\">CDS/Protein/Protein group Info</span></p></body></html>", None))
        self.label_14.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-weight:600;\">General</span></p></body></html>", None))
        self.xlsx_separator.setText(QCoreApplication.translate("NeiExport", u",", None))
        self.label_16.setText(QCoreApplication.translate("NeiExport", u"Cell contents:", None))
        self.label_17.setText(QCoreApplication.translate("NeiExport", u"Value separator: ", None))
        self.xlsx_transpose.setText(QCoreApplication.translate("NeiExport", u"Rotate table 90\u00b0", None))
        self.label_18.setText(QCoreApplication.translate("NeiExport", u"Comment contents:", None))
        self.xlsx_align.setText(QCoreApplication.translate("NeiExport", u"Maintain alignment (will disregard manually shifted clusters)", None))
        self.xlsx_condensetags.setText(QCoreApplication.translate("NeiExport", u"Condense tags into single cell (separated by separator)", None))
        self.label_11.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-style:italic;\">No applicable FASTA settings.</span></p></body></html>", None))
        self.label_12.setText(QCoreApplication.translate("NeiExport", u"Cutoff threshold: 0.0", None))
        self.label_24.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-style:italic;\">This export option outputs a</span><span style=\" font-weight:600; font-style:italic;\"> similarity-based network graph</span><span style=\" font-style:italic;\"> of selected gene clusters compatible with software like Cytoscape.</span></p><p><span style=\" font-style:italic;\">The pairwise similarity metric used is the Jaccard index, which calculates </span><span style=\" font-weight:600; font-style:italic;\">the numberof unique protein groups two gene clusters share</span><span style=\" font-style:italic;\"> divided by the total number of unique protein groups in both.</span></p><p><span style=\" font-style:italic;\">If you select &quot;Only highlighted region&quot; on the left, the similarity will be calculated only in the highlighted region.</span></p></body></html>", None))
        self.label_23.setText(QCoreApplication.translate("NeiExport", u"1.0", None))
        self.label_25.setText(QCoreApplication.translate("NeiExport", u"Similarity metric", None))
        self.gml_metric_combo.setItemText(0, QCoreApplication.translate("NeiExport", u"Jaccard index of protein groups", None))

        self.gmlprot_relatedproteins_chk.setText(QCoreApplication.translate("NeiExport", u"Include related protein groups", None))
        self.label_27.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-style:italic;\">Note that only proteins and protein groups that fit your selection criteria will be shown. For example, if you are exporting only proteins from specific protein groups, this option will do nothing.</span></p></body></html>", None))
        self.label_28.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p>This will export a network graph of protein groups represented in the selected subset, linked together based on local sequence homology.</p></body></html>", None))
        self.save_btn.setText(QCoreApplication.translate("NeiExport", u"Save Output", None))
        self.cancel_btn.setText(QCoreApplication.translate("NeiExport", u"Close", None))
        self.filesaved_lbl.setText("")
        self.exportingfrom_lbl.setText(QCoreApplication.translate("NeiExport", u"Now exporting from ...", None))
        self.label_3.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-weight:600;\">Contents to export:</span></p></body></html>", None))
        self.label_19.setText(QCoreApplication.translate("NeiExport", u"Which clusters to export", None))
        self.clusters_checked_radio.setText(QCoreApplication.translate("NeiExport", u"Only selected", None))
        self.clusters_all_radio.setText(QCoreApplication.translate("NeiExport", u"All", None))
        self.label_20.setText(QCoreApplication.translate("NeiExport", u"How much of each cluster to export:", None))
        self.clusters_full_radio.setText(QCoreApplication.translate("NeiExport", u"Full length", None))
        self.clusters_highlighted_radio.setText(QCoreApplication.translate("NeiExport", u"Only highlighted region", None))
        self.label_2.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-style:italic;\">Note: You can use left click and drag to highlight a region in the main gene cluster view.</span></p></body></html>", None))
        self.label_21.setText(QCoreApplication.translate("NeiExport", u"Export proteins that are...", None))
        self.proteins_clusters_checked_radio.setText(QCoreApplication.translate("NeiExport", u"Within selected clusters", None))
        self.proteins_selected_prgroups_radio.setText(QCoreApplication.translate("NeiExport", u"Within selected protein groups", None))
        self.proteins_highlighted_radio.setText(QCoreApplication.translate("NeiExport", u"Within highlighted region", None))
        self.label_22.setText(QCoreApplication.translate("NeiExport", u"<html><head/><body><p><span style=\" font-style:italic;\">Note: leaving all boxes unchecked exports ALL proteins within the cluster view</span></p></body></html>", None))
    # retranslateUi

