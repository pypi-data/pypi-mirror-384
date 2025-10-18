# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'excelexportframe.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ExcelExportFrame(object):
    def setupUi(self, ExcelExportFrame):
        if not ExcelExportFrame.objectName():
            ExcelExportFrame.setObjectName(u"ExcelExportFrame")
        ExcelExportFrame.resize(340, 261)
        self.gridLayout = QGridLayout(ExcelExportFrame)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_3 = QLabel(ExcelExportFrame)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)

        self.align_chk = QCheckBox(ExcelExportFrame)
        self.align_chk.setObjectName(u"align_chk")
        self.align_chk.setChecked(True)

        self.gridLayout.addWidget(self.align_chk, 1, 0, 1, 4)

        self.horizontalSpacer_2 = QSpacerItem(72, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 1, 4, 1, 1)

        self.horizontalSpacer = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 1, 5, 1, 1)

        self.transpose_table_chk = QCheckBox(ExcelExportFrame)
        self.transpose_table_chk.setObjectName(u"transpose_table_chk")

        self.gridLayout.addWidget(self.transpose_table_chk, 2, 0, 1, 3)

        self.horizontalSpacer_4 = QSpacerItem(48, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_4, 2, 3, 1, 1)

        self.line = QFrame(ExcelExportFrame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line, 3, 0, 1, 5)

        self.label_12 = QLabel(ExcelExportFrame)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout.addWidget(self.label_12, 4, 0, 1, 3)

        self.label = QLabel(ExcelExportFrame)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 5, 0, 1, 1)

        self.selector_container_cell = QWidget(ExcelExportFrame)
        self.selector_container_cell.setObjectName(u"selector_container_cell")
        self.selector_container_cell_lay = QVBoxLayout(self.selector_container_cell)
        self.selector_container_cell_lay.setObjectName(u"selector_container_cell_lay")
        self.selector_container_cell_lay.setContentsMargins(0, -1, 0, -1)

        self.gridLayout.addWidget(self.selector_container_cell, 6, 0, 1, 5)

        self.label_15 = QLabel(ExcelExportFrame)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout.addWidget(self.label_15, 7, 0, 1, 2)

        self.cell_value_separator_ledit = QLineEdit(ExcelExportFrame)
        self.cell_value_separator_ledit.setObjectName(u"cell_value_separator_ledit")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cell_value_separator_ledit.sizePolicy().hasHeightForWidth())
        self.cell_value_separator_ledit.setSizePolicy(sizePolicy)
        self.cell_value_separator_ledit.setMinimumSize(QSize(31, 0))
        self.cell_value_separator_ledit.setMaximumSize(QSize(31, 16777215))

        self.gridLayout.addWidget(self.cell_value_separator_ledit, 7, 2, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(129, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 7, 3, 1, 2)

        self.label_2 = QLabel(ExcelExportFrame)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 8, 0, 1, 2)

        self.selector_container_comment = QWidget(ExcelExportFrame)
        self.selector_container_comment.setObjectName(u"selector_container_comment")
        self.selector_container_comment_lay = QVBoxLayout(self.selector_container_comment)
        self.selector_container_comment_lay.setObjectName(u"selector_container_comment_lay")
        self.selector_container_comment_lay.setContentsMargins(0, -1, 0, -1)

        self.gridLayout.addWidget(self.selector_container_comment, 9, 0, 1, 5)

        self.io_cancel_btn = QPushButton(ExcelExportFrame)
        self.io_cancel_btn.setObjectName(u"io_cancel_btn")

        self.gridLayout.addWidget(self.io_cancel_btn, 10, 0, 1, 1)

        self.horizontalSpacer_5 = QSpacerItem(57, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_5, 10, 1, 1, 1)

        self.horizontalSpacer_6 = QSpacerItem(48, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_6, 10, 3, 1, 1)

        self.io_save_btn = QPushButton(ExcelExportFrame)
        self.io_save_btn.setObjectName(u"io_save_btn")

        self.gridLayout.addWidget(self.io_save_btn, 10, 4, 1, 1)


        self.retranslateUi(ExcelExportFrame)

        QMetaObject.connectSlotsByName(ExcelExportFrame)
    # setupUi

    def retranslateUi(self, ExcelExportFrame):
        ExcelExportFrame.setWindowTitle(QCoreApplication.translate("ExcelExportFrame", u"Form", None))
        self.label_3.setText(QCoreApplication.translate("ExcelExportFrame", u"<html><head/><body><p><span style=\" font-weight:600;\">General</span></p></body></html>", None))
        self.align_chk.setText(QCoreApplication.translate("ExcelExportFrame", u"Retain alignment set in neighborhood view", None))
        self.transpose_table_chk.setText(QCoreApplication.translate("ExcelExportFrame", u"Transpose neighborhood table", None))
        self.label_12.setText(QCoreApplication.translate("ExcelExportFrame", u"<html><head/><body><p><span style=\" font-weight:600;\">CDS/Protein/Protein group Info</span></p></body></html>", None))
        self.label.setText(QCoreApplication.translate("ExcelExportFrame", u"Cell contents:", None))
        self.label_15.setText(QCoreApplication.translate("ExcelExportFrame", u"Cell value separator:", None))
        self.cell_value_separator_ledit.setText(QCoreApplication.translate("ExcelExportFrame", u", ", None))
        self.label_2.setText(QCoreApplication.translate("ExcelExportFrame", u"Cell comment contents:", None))
        self.io_cancel_btn.setText(QCoreApplication.translate("ExcelExportFrame", u"Cancel", None))
        self.io_save_btn.setText(QCoreApplication.translate("ExcelExportFrame", u"Save", None))
    # retranslateUi

