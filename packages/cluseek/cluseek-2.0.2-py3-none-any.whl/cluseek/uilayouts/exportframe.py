# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'exportframe.ui'
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
        Form.resize(793, 944)
        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(70, 150, 81, 16))
        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(60, 530, 161, 16))
        self.label_3 = QLabel(Form)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(60, 30, 47, 13))
        self.radioButton = QRadioButton(Form)
        self.radioButton.setObjectName(u"radioButton")
        self.radioButton.setGeometry(QRect(90, 60, 141, 16))
        self.radioButton_2 = QRadioButton(Form)
        self.radioButton_2.setObjectName(u"radioButton_2")
        self.radioButton_2.setGeometry(QRect(250, 60, 101, 17))
        self.label_4 = QLabel(Form)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(140, 620, 61, 16))
        self.lineEdit = QLineEdit(Form)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setGeometry(QRect(200, 620, 113, 20))
        self.radioButton_3 = QRadioButton(Form)
        self.radioButton_3.setObjectName(u"radioButton_3")
        self.radioButton_3.setGeometry(QRect(110, 590, 181, 17))
        self.radioButton_4 = QRadioButton(Form)
        self.radioButton_4.setObjectName(u"radioButton_4")
        self.radioButton_4.setGeometry(QRect(110, 550, 151, 17))
        self.radioButton_5 = QRadioButton(Form)
        self.radioButton_5.setObjectName(u"radioButton_5")
        self.radioButton_5.setGeometry(QRect(110, 570, 171, 17))
        self.line = QFrame(Form)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(70, 120, 561, 16))
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.line_2 = QFrame(Form)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setGeometry(QRect(60, 500, 561, 16))
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)
        self.lineEdit_3 = QLineEdit(Form)
        self.lineEdit_3.setObjectName(u"lineEdit_3")
        self.lineEdit_3.setGeometry(QRect(210, 270, 113, 20))
        self.label_12 = QLabel(Form)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setGeometry(QRect(70, 180, 161, 16))
        self.radioButton_11 = QRadioButton(Form)
        self.radioButton_11.setObjectName(u"radioButton_11")
        self.radioButton_11.setGeometry(QRect(120, 200, 151, 17))
        self.radioButton_12 = QRadioButton(Form)
        self.radioButton_12.setObjectName(u"radioButton_12")
        self.radioButton_12.setGeometry(QRect(120, 240, 181, 17))
        self.label_15 = QLabel(Form)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setGeometry(QRect(150, 270, 61, 16))
        self.radioButton_13 = QRadioButton(Form)
        self.radioButton_13.setObjectName(u"radioButton_13")
        self.radioButton_13.setGeometry(QRect(120, 220, 171, 17))

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form", u"Organism Info", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"CDS/Protein/Protein Group Info", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"General", None))
        self.radioButton.setText(QCoreApplication.translate("Form", u"Align (human-readable)", None))
        self.radioButton_2.setText(QCoreApplication.translate("Form", u"No Alignment", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Separator:", None))
        self.lineEdit.setText(QCoreApplication.translate("Form", u", ", None))
#if QT_CONFIG(tooltip)
        self.radioButton_3.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_3.setText(QCoreApplication.translate("Form", u"Merge all values  into single cell", None))
#if QT_CONFIG(tooltip)
        self.radioButton_4.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_4.setText(QCoreApplication.translate("Form", u"Values unpacked into rows", None))
        self.radioButton_5.setText(QCoreApplication.translate("Form", u"Values unpacked into columns", None))
        self.lineEdit_3.setText(QCoreApplication.translate("Form", u", ", None))
        self.label_12.setText(QCoreApplication.translate("Form", u"CDS/Protein/Protein Group Info", None))
#if QT_CONFIG(tooltip)
        self.radioButton_11.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_11.setText(QCoreApplication.translate("Form", u"Values unpacked into rows", None))
#if QT_CONFIG(tooltip)
        self.radioButton_12.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_12.setText(QCoreApplication.translate("Form", u"Merge all values  into single cell", None))
        self.label_15.setText(QCoreApplication.translate("Form", u"Separator:", None))
        self.radioButton_13.setText(QCoreApplication.translate("Form", u"Values unpacked into columns", None))
    # retranslateUi

