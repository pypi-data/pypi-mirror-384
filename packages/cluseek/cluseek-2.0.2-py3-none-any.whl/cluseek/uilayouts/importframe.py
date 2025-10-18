# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'importframe.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ImportFrame(object):
    def setupUi(self, ImportFrame):
        if not ImportFrame.objectName():
            ImportFrame.setObjectName(u"ImportFrame")
        ImportFrame.resize(971, 462)
        self.gridLayout = QGridLayout(ImportFrame)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.btn_back = QPushButton(ImportFrame)
        self.btn_back.setObjectName(u"btn_back")

        self.horizontalLayout.addWidget(self.btn_back)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.blastconfig_btn = QPushButton(ImportFrame)
        self.blastconfig_btn.setObjectName(u"blastconfig_btn")

        self.horizontalLayout.addWidget(self.blastconfig_btn)

        self.btn_loadFiles = QPushButton(ImportFrame)
        self.btn_loadFiles.setObjectName(u"btn_loadFiles")

        self.horizontalLayout.addWidget(self.btn_loadFiles)


        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 4)

        self.importFileStack_scrl = QScrollArea(ImportFrame)
        self.importFileStack_scrl.setObjectName(u"importFileStack_scrl")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.importFileStack_scrl.sizePolicy().hasHeightForWidth())
        self.importFileStack_scrl.setSizePolicy(sizePolicy)
        self.importFileStack_scrl.setMinimumSize(QSize(300, 180))
        self.importFileStack_scrl.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.importFileStack_scrl.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.importFileStack_scrl.setWidgetResizable(True)
        self.importFileStack = QWidget()
        self.importFileStack.setObjectName(u"importFileStack")
        self.importFileStack.setGeometry(QRect(0, 0, 951, 303))
        self.importFileStack.setMinimumSize(QSize(0, 0))
        self.lay_importFileStack = QVBoxLayout(self.importFileStack)
        self.lay_importFileStack.setSpacing(0)
        self.lay_importFileStack.setObjectName(u"lay_importFileStack")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(9, 2, -1, 2)
        self.btn_addFile = QPushButton(self.importFileStack)
        self.btn_addFile.setObjectName(u"btn_addFile")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_addFile.sizePolicy().hasHeightForWidth())
        self.btn_addFile.setSizePolicy(sizePolicy1)
        self.btn_addFile.setMinimumSize(QSize(20, 20))
        self.btn_addFile.setMaximumSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.btn_addFile)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.lay_importFileStack.addLayout(self.horizontalLayout_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.lay_importFileStack.addItem(self.verticalSpacer)

        self.importFileStack_scrl.setWidget(self.importFileStack)

        self.gridLayout.addWidget(self.importFileStack_scrl, 0, 0, 1, 4)

        self.label = QLabel(ImportFrame)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.gridLayout.addWidget(self.label, 3, 0, 1, 4)


        self.retranslateUi(ImportFrame)

        QMetaObject.connectSlotsByName(ImportFrame)
    # setupUi

    def retranslateUi(self, ImportFrame):
        ImportFrame.setWindowTitle(QCoreApplication.translate("ImportFrame", u"Form", None))
        self.btn_back.setText(QCoreApplication.translate("ImportFrame", u"Back", None))
        self.blastconfig_btn.setText(QCoreApplication.translate("ImportFrame", u"Remote BLAST Configuration", None))
        self.btn_loadFiles.setText(QCoreApplication.translate("ImportFrame", u"Start!", None))
        self.btn_addFile.setText(QCoreApplication.translate("ImportFrame", u"+", None))
        self.label.setText(QCoreApplication.translate("ImportFrame", u"<html><head/><body><p><span style=\" font-weight:600;\">PLEASE DO NOT SUBMIT MORE THAN 50 PROTEIN SEQUENCES FOR BLASTP SEARCH -- </span>Such large searches put needless strain on NCBI servers and are unlikely to complete. The recommended amount is below 10 markers. XML files with previously completed searches do not count towards this limit, as the search had already been completed.</p><p><span style=\" font-weight:600;\">This also means that you only need to consider remote BLASTP configuration when using FASTA sequences or accession codes as inputs.</span></p><p><span style=\" font-style:italic; color:#4b4b4b;\">Searches submitted through the</span><span style=\" font-weight:600; font-style:italic; color:#4b4b4b;\"> NCBI website</span><span style=\" font-style:italic; color:#4b4b4b;\"> have priority over searches submitted from CluSeek. However, it is advised to check the search settings. The default settings in CluSeek are close but not identical to the defaults in the BLAST interface. In particular, the nu"
                        "mber of results returned should be</span><span style=\" font-weight:600; font-style:italic; color:#4b4b4b;\"> set to the highest possible amount (5000 as of writing)</span><span style=\" font-style:italic; color:#4b4b4b;\">.</span></p></body></html>", None))
    # retranslateUi

