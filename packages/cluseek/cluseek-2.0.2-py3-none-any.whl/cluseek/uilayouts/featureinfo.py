# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'featureinfo.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_FeatureInfo(object):
    def setupUi(self, FeatureInfo):
        if not FeatureInfo.objectName():
            FeatureInfo.setObjectName(u"FeatureInfo")
        FeatureInfo.resize(400, 300)
        self.formLayout = QFormLayout(FeatureInfo)
        self.formLayout.setObjectName(u"formLayout")
        self.lbl_featuretype_info = QLabel(FeatureInfo)
        self.lbl_featuretype_info.setObjectName(u"lbl_featuretype_info")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.lbl_featuretype_info)

        self.lbl_featuretype = QLabel(FeatureInfo)
        self.lbl_featuretype.setObjectName(u"lbl_featuretype")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.lbl_featuretype)

        self.lbl_location_info = QLabel(FeatureInfo)
        self.lbl_location_info.setObjectName(u"lbl_location_info")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.lbl_location_info)

        self.lbl_location = QLabel(FeatureInfo)
        self.lbl_location.setObjectName(u"lbl_location")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.lbl_location)


        self.retranslateUi(FeatureInfo)

        QMetaObject.connectSlotsByName(FeatureInfo)
    # setupUi

    def retranslateUi(self, FeatureInfo):
        FeatureInfo.setWindowTitle(QCoreApplication.translate("FeatureInfo", u"Form", None))
        self.lbl_featuretype_info.setText(QCoreApplication.translate("FeatureInfo", u"Feature Type:", None))
        self.lbl_featuretype.setText(QCoreApplication.translate("FeatureInfo", u"Error", None))
        self.lbl_location_info.setText(QCoreApplication.translate("FeatureInfo", u"Location:", None))
        self.lbl_location.setText(QCoreApplication.translate("FeatureInfo", u"Error", None))
    # retranslateUi

