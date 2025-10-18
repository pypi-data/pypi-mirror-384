# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'colocresultsframe.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ColocResultsFrame(object):
    def setupUi(self, ColocResultsFrame):
        if not ColocResultsFrame.objectName():
            ColocResultsFrame.setObjectName(u"ColocResultsFrame")
        ColocResultsFrame.resize(729, 638)
        self.gridLayout = QGridLayout(ColocResultsFrame)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setVerticalSpacing(2)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(ColocResultsFrame)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.info_btn = QToolButton(ColocResultsFrame)
        self.info_btn.setObjectName(u"info_btn")

        self.horizontalLayout.addWidget(self.info_btn)

        self.line = QFrame(ColocResultsFrame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 2)

        self.coloc_table_basic = QTableWidget(ColocResultsFrame)
        self.coloc_table_basic.setObjectName(u"coloc_table_basic")

        self.gridLayout.addWidget(self.coloc_table_basic, 5, 0, 1, 2)

        self.info_lbl = QLabel(ColocResultsFrame)
        self.info_lbl.setObjectName(u"info_lbl")
        self.info_lbl.setWordWrap(True)

        self.gridLayout.addWidget(self.info_lbl, 3, 0, 1, 2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.export_btn = QPushButton(ColocResultsFrame)
        self.export_btn.setObjectName(u"export_btn")

        self.horizontalLayout_3.addWidget(self.export_btn)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout_3, 4, 0, 1, 1)


        self.retranslateUi(ColocResultsFrame)

        QMetaObject.connectSlotsByName(ColocResultsFrame)
    # setupUi

    def retranslateUi(self, ColocResultsFrame):
        ColocResultsFrame.setWindowTitle(QCoreApplication.translate("ColocResultsFrame", u"Form", None))
        self.label.setText(QCoreApplication.translate("ColocResultsFrame", u"<html><head/><body><p><span style=\" font-weight:600;\">Colocalization results table</span></p></body></html>", None))
        self.info_btn.setText(QCoreApplication.translate("ColocResultsFrame", u"?", None))
        self.info_lbl.setText(QCoreApplication.translate("ColocResultsFrame", u"<html><head/><body><p><span style=\" font-weight:600; font-style:italic; color:#585858;\">These are the results of your colocalization.</span><span style=\" font-style:italic; color:#585858;\"> It is a list of all genetic regions (clusters) found in GenBank in which your marker proteins are all found within a region of a size you specified. Some regions may be larger than the specified size, as CluSeek merges overlapping regions if all mergets parts individually satisfy the search criteria.</span></p><p><span style=\" font-weight:600; font-style:italic; color:#585858;\">The columns are as follows:</span></p><p><span style=\" font-style:italic; color:#585858;\">Score - The number of points a cluster was awarded based on how many markers were present. By default, CluSeek searches for ALL markers, so this column will be uniform.</span></p><p><span style=\" font-style:italic; color:#585858;\">Length - The edge-to-edge length of the cluster, IE the distance from the start of the first coding sequence to the end of "
                        "the last coding sequence.</span></p><p><span style=\" font-style:italic; color:#585858;\">Internal Length - The distance from the </span><span style=\" font-weight:600; font-style:italic; color:#585858;\">end</span><span style=\" font-style:italic; color:#585858;\"> of the </span><span style=\" font-weight:600; font-style:italic; color:#585858;\">first</span><span style=\" font-style:italic; color:#585858;\"> coding sequence to the </span><span style=\" font-weight:600; font-style:italic; color:#585858;\">start</span><span style=\" font-style:italic; color:#585858;\"> of the </span><span style=\" font-weight:600; font-style:italic; color:#585858;\">last</span><span style=\" font-style:italic; color:#585858;\"> coding sequence. When searching for a pair of proteins, this number is the distance between the two coding sequences. If the coding sequences overlap, it will be negative.</span></p><p><span style=\" font-style:italic; color:#585858;\">Taxon - The genus and species from which the sequence was obtained.</"
                        "span></p><p><span style=\" font-style:italic; color:#585858;\">Strain - The strain from which the sequence was obtained.</span></p><p><span style=\" font-style:italic; color:#585858;\">Tax ID - the NCBI Taxonomic ID to which the sequence is attributed in GenBank, usually corresponding to a specific species.</span></p><p><span style=\" font-style:italic; color:#585858;\">Sequence - The accession code for the genetic sequence (contig) in which the cluster was found.</span></p><p><span style=\" font-style:italic; color:#585858;\">The subsequent columns each correspond to one marker and list the accession code(s) of the relevant homolog(s) in the cluster.</span></p></body></html>", None))
        self.export_btn.setText(QCoreApplication.translate("ColocResultsFrame", u"Export this table", None))
    # retranslateUi

