# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'accsetblock.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_AccsetBlock(object):
    def setupUi(self, AccsetBlock):
        if not AccsetBlock.objectName():
            AccsetBlock.setObjectName(u"AccsetBlock")
        AccsetBlock.resize(315, 22)
        palette = QPalette()
        brush = QBrush(QColor(252, 252, 252, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Base, brush)
        brush1 = QBrush(QColor(207, 207, 207, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Window, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        AccsetBlock.setPalette(palette)
        self.lay_accsetblock = QHBoxLayout(AccsetBlock)
        self.lay_accsetblock.setSpacing(4)
        self.lay_accsetblock.setObjectName(u"lay_accsetblock")
        self.lay_accsetblock.setContentsMargins(1, 1, 1, 1)
        self.ch_include = QCheckBox(AccsetBlock)
        self.ch_include.setObjectName(u"ch_include")

        self.lay_accsetblock.addWidget(self.ch_include)

        self.score_spin = QSpinBox(AccsetBlock)
        self.score_spin.setObjectName(u"score_spin")
        self.score_spin.setMinimumSize(QSize(0, 0))
        self.score_spin.setMaximumSize(QSize(59, 16777215))
        self.score_spin.setMinimum(-99999)
        self.score_spin.setMaximum(99999)
        self.score_spin.setValue(0)

        self.lay_accsetblock.addWidget(self.score_spin)

        self.in_alias = QLineEdit(AccsetBlock)
        self.in_alias.setObjectName(u"in_alias")
        self.in_alias.setMinimumSize(QSize(50, 20))
        self.in_alias.setMaximumSize(QSize(16777215, 30))

        self.lay_accsetblock.addWidget(self.in_alias)


        self.retranslateUi(AccsetBlock)

        QMetaObject.connectSlotsByName(AccsetBlock)
    # setupUi

    def retranslateUi(self, AccsetBlock):
        AccsetBlock.setWindowTitle(QCoreApplication.translate("AccsetBlock", u"Form", None))
        self.ch_include.setText(QCoreApplication.translate("AccsetBlock", u"protein accession", None))
#if QT_CONFIG(tooltip)
        self.score_spin.setToolTip(QCoreApplication.translate("AccsetBlock", u"<html><head/><body><p>Set the score weight for this marker protein. If a potential gene cluster encodes at least one protein homologous to the marker protein, this score value is added. (Multiple proteins homologous to the same marker protein have no effect on the score value. However, one protein homologous to two or more different marker proteins may be counted twice.)</p><p>A region must contain homologues whose total score exceeds the minimum score value to be included in the results.</p><p>Negative score values may be assigned.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.in_alias.setText(QCoreApplication.translate("AccsetBlock", u"alias", None))
    # retranslateUi

