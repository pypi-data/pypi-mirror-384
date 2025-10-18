# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tagwidget.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_TagWidget(object):
    def setupUi(self, TagWidget):
        if not TagWidget.objectName():
            TagWidget.setObjectName(u"TagWidget")
        TagWidget.resize(268, 301)
        self.formLayout = QFormLayout(TagWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.name_lbl = QLabel(TagWidget)
        self.name_lbl.setObjectName(u"name_lbl")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.name_lbl)

        self.name_ledit = QLineEdit(TagWidget)
        self.name_ledit.setObjectName(u"name_ledit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.name_ledit)

        self.ident_lbl = QLabel(TagWidget)
        self.ident_lbl.setObjectName(u"ident_lbl")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.ident_lbl)

        self.ident_ledit = QLineEdit(TagWidget)
        self.ident_ledit.setObjectName(u"ident_ledit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.ident_ledit)

        self.descr_lbl = QLabel(TagWidget)
        self.descr_lbl.setObjectName(u"descr_lbl")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.descr_lbl)

        self.descr_tedit = QTextEdit(TagWidget)
        self.descr_tedit.setObjectName(u"descr_tedit")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.descr_tedit)

        self.label = QLabel(TagWidget)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label)

        self.colorpicker_frame = QFrame(TagWidget)
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


        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.colorpicker_frame)

        self.apply_btn = QPushButton(TagWidget)
        self.apply_btn.setObjectName(u"apply_btn")

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.apply_btn)

        self.checkBox = QCheckBox(TagWidget)
        self.checkBox.setObjectName(u"checkBox")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.checkBox)


        self.retranslateUi(TagWidget)

        QMetaObject.connectSlotsByName(TagWidget)
    # setupUi

    def retranslateUi(self, TagWidget):
        TagWidget.setWindowTitle(QCoreApplication.translate("TagWidget", u"Form", None))
        self.name_lbl.setText(QCoreApplication.translate("TagWidget", u"Name", None))
        self.ident_lbl.setText(QCoreApplication.translate("TagWidget", u"Identifier", None))
        self.descr_lbl.setText(QCoreApplication.translate("TagWidget", u"Description", None))
        self.label.setText(QCoreApplication.translate("TagWidget", u"Color", None))
        self.colorpicker_label.setText(QCoreApplication.translate("TagWidget", u"Set Color", None))
        self.apply_btn.setText(QCoreApplication.translate("TagWidget", u"Apply Changes", None))
        self.checkBox.setText(QCoreApplication.translate("TagWidget", u"Hide", None))
    # retranslateUi

