# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'taginfowidget.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_TagInfoWidget(object):
    def setupUi(self, TagInfoWidget):
        if not TagInfoWidget.objectName():
            TagInfoWidget.setObjectName(u"TagInfoWidget")
        TagInfoWidget.resize(252, 308)
        self.formLayout = QFormLayout(TagInfoWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.name_lbl = QLabel(TagInfoWidget)
        self.name_lbl.setObjectName(u"name_lbl")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.name_lbl)

        self.name_ledit = QLineEdit(TagInfoWidget)
        self.name_ledit.setObjectName(u"name_ledit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.name_ledit)

        self.ident_lbl = QLabel(TagInfoWidget)
        self.ident_lbl.setObjectName(u"ident_lbl")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.ident_lbl)

        self.ident_ledit = QLineEdit(TagInfoWidget)
        self.ident_ledit.setObjectName(u"ident_ledit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.ident_ledit)

        self.hidden_chk = QCheckBox(TagInfoWidget)
        self.hidden_chk.setObjectName(u"hidden_chk")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.hidden_chk)

        self.descr_lbl = QLabel(TagInfoWidget)
        self.descr_lbl.setObjectName(u"descr_lbl")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.descr_lbl)

        self.descr_tedit = QTextEdit(TagInfoWidget)
        self.descr_tedit.setObjectName(u"descr_tedit")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.descr_tedit)

        self.label = QLabel(TagInfoWidget)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label)

        self.colorpicker_text_frame = QFrame(TagInfoWidget)
        self.colorpicker_text_frame.setObjectName(u"colorpicker_text_frame")
        self.colorpicker_text_frame.setFrameShape(QFrame.Panel)
        self.colorpicker_text_frame.setFrameShadow(QFrame.Raised)
        self.colorpicker_text_frame.setLineWidth(1)
        self.colorpicker_text_frame.setMidLineWidth(0)
        self.gridLayout = QGridLayout(self.colorpicker_text_frame)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.colorpicker_text = QWidget(self.colorpicker_text_frame)
        self.colorpicker_text.setObjectName(u"colorpicker_text")
        self.colorpicker_text.setMinimumSize(QSize(0, 17))
        self.horizontalLayout = QHBoxLayout(self.colorpicker_text)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)

        self.gridLayout.addWidget(self.colorpicker_text, 0, 0, 1, 1)


        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.colorpicker_text_frame)

        self.colorpicker_background_frame = QFrame(TagInfoWidget)
        self.colorpicker_background_frame.setObjectName(u"colorpicker_background_frame")
        self.colorpicker_background_frame.setFrameShape(QFrame.Panel)
        self.colorpicker_background_frame.setFrameShadow(QFrame.Raised)
        self.colorpicker_background_frame.setLineWidth(1)
        self.colorpicker_background_frame.setMidLineWidth(0)
        self.gridLayout_2 = QGridLayout(self.colorpicker_background_frame)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.colorpicker_background = QWidget(self.colorpicker_background_frame)
        self.colorpicker_background.setObjectName(u"colorpicker_background")
        self.colorpicker_background.setMinimumSize(QSize(0, 17))
        self.horizontalLayout_2 = QHBoxLayout(self.colorpicker_background)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)

        self.gridLayout_2.addWidget(self.colorpicker_background, 0, 0, 1, 1)


        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.colorpicker_background_frame)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.cancel_btn = QPushButton(TagInfoWidget)
        self.cancel_btn.setObjectName(u"cancel_btn")

        self.horizontalLayout_5.addWidget(self.cancel_btn)

        self.delete_btn = QPushButton(TagInfoWidget)
        self.delete_btn.setObjectName(u"delete_btn")

        self.horizontalLayout_5.addWidget(self.delete_btn)

        self.apply_btn = QPushButton(TagInfoWidget)
        self.apply_btn.setObjectName(u"apply_btn")

        self.horizontalLayout_5.addWidget(self.apply_btn)


        self.formLayout.setLayout(6, QFormLayout.FieldRole, self.horizontalLayout_5)


        self.retranslateUi(TagInfoWidget)

        QMetaObject.connectSlotsByName(TagInfoWidget)
    # setupUi

    def retranslateUi(self, TagInfoWidget):
        TagInfoWidget.setWindowTitle(QCoreApplication.translate("TagInfoWidget", u"Form", None))
        self.name_lbl.setText(QCoreApplication.translate("TagInfoWidget", u"Name", None))
        self.name_ledit.setText("")
        self.ident_lbl.setText(QCoreApplication.translate("TagInfoWidget", u"Identifier", None))
        self.ident_ledit.setText("")
        self.hidden_chk.setText(QCoreApplication.translate("TagInfoWidget", u"Hidden", None))
        self.descr_lbl.setText(QCoreApplication.translate("TagInfoWidget", u"Description", None))
        self.label.setText(QCoreApplication.translate("TagInfoWidget", u"Color", None))
        self.cancel_btn.setText(QCoreApplication.translate("TagInfoWidget", u"Cancel", None))
        self.delete_btn.setText(QCoreApplication.translate("TagInfoWidget", u"Delete", None))
        self.apply_btn.setText(QCoreApplication.translate("TagInfoWidget", u"Apply", None))
    # retranslateUi

