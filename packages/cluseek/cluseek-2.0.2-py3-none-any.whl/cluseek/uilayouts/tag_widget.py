# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tag_widget.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(268, 301)
        self.formLayout = QFormLayout(Form)
        self.formLayout.setObjectName(u"formLayout")
        self.name_lbl = QLabel(Form)
        self.name_lbl.setObjectName(u"name_lbl")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.name_lbl)

        self.name_ledit = QLineEdit(Form)
        self.name_ledit.setObjectName(u"name_ledit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.name_ledit)

        self.ident_lbl = QLabel(Form)
        self.ident_lbl.setObjectName(u"ident_lbl")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.ident_lbl)

        self.ident_ledit = QLineEdit(Form)
        self.ident_ledit.setObjectName(u"ident_ledit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.ident_ledit)

        self.descr_lbl = QLabel(Form)
        self.descr_lbl.setObjectName(u"descr_lbl")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.descr_lbl)

        self.descr_tedit = QTextEdit(Form)
        self.descr_tedit.setObjectName(u"descr_tedit")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.descr_tedit)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label)

        self.colorpicker_frame = QFrame(Form)
        self.colorpicker_frame.setObjectName(u"colorpicker_frame")
        self.colorpicker_frame.setFrameShape(QFrame.Panel)
        self.colorpicker_frame.setFrameShadow(QFrame.Raised)
        self.colorpicker_frame.setLineWidth(1)
        self.colorpicker_frame.setMidLineWidth(0)
        self.gridLayout = QGridLayout(self.colorpicker_frame)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.colorpicker_colorwidget = QWidget(self.colorpicker_frame)
        self.colorpicker_colorwidget.setObjectName(u"colorpicker_colorwidget")
        self.horizontalLayout = QHBoxLayout(self.colorpicker_colorwidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.colorpicker_label = QLabel(self.colorpicker_colorwidget)
        self.colorpicker_label.setObjectName(u"colorpicker_label")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorpicker_label.sizePolicy().hasHeightForWidth())
        self.colorpicker_label.setSizePolicy(sizePolicy)
        self.colorpicker_label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.colorpicker_label)


        self.gridLayout.addWidget(self.colorpicker_colorwidget, 0, 0, 1, 1)


        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.colorpicker_frame)

        self.apply_btn = QPushButton(Form)
        self.apply_btn.setObjectName(u"apply_btn")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.apply_btn)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.name_lbl.setText(QCoreApplication.translate("Form", u"Name", None))
        self.ident_lbl.setText(QCoreApplication.translate("Form", u"Identifier", None))
        self.descr_lbl.setText(QCoreApplication.translate("Form", u"Description", None))
        self.label.setText(QCoreApplication.translate("Form", u"Color", None))
        self.colorpicker_label.setText(QCoreApplication.translate("Form", u"Set Color", None))
        self.apply_btn.setText(QCoreApplication.translate("Form", u"Apply Changes", None))
    # retranslateUi

