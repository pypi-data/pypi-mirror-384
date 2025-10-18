# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'blastconfig.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_BlastConfig(object):
    def setupUi(self, BlastConfig):
        if not BlastConfig.objectName():
            BlastConfig.setObjectName(u"BlastConfig")
        BlastConfig.resize(499, 559)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(BlastConfig.sizePolicy().hasHeightForWidth())
        BlastConfig.setSizePolicy(sizePolicy)
        BlastConfig.setMinimumSize(QSize(0, 0))
        self.gridLayout = QGridLayout(BlastConfig)
        self.gridLayout.setObjectName(u"gridLayout")
        self.searchset_lbl = QLabel(BlastConfig)
        self.searchset_lbl.setObjectName(u"searchset_lbl")

        self.gridLayout.addWidget(self.searchset_lbl, 0, 0, 1, 1)

        self.database_lbl = QLabel(BlastConfig)
        self.database_lbl.setObjectName(u"database_lbl")

        self.gridLayout.addWidget(self.database_lbl, 1, 0, 1, 1)

        self.database_combo = QComboBox(BlastConfig)
        self.database_combo.addItem("")
        self.database_combo.addItem("")
        self.database_combo.addItem("")
        self.database_combo.addItem("")
        self.database_combo.addItem("")
        self.database_combo.addItem("")
        self.database_combo.addItem("")
        self.database_combo.addItem("")
        self.database_combo.addItem("")
        self.database_combo.setObjectName(u"database_combo")

        self.gridLayout.addWidget(self.database_combo, 1, 2, 1, 4)

        self.entrez_lbl = QLabel(BlastConfig)
        self.entrez_lbl.setObjectName(u"entrez_lbl")

        self.gridLayout.addWidget(self.entrez_lbl, 2, 0, 1, 1)

        self.entrez_lbl2 = QLabel(BlastConfig)
        self.entrez_lbl2.setObjectName(u"entrez_lbl2")
        sizePolicy.setHeightForWidth(self.entrez_lbl2.sizePolicy().hasHeightForWidth())
        self.entrez_lbl2.setSizePolicy(sizePolicy)
        self.entrez_lbl2.setWordWrap(True)
        self.entrez_lbl2.setOpenExternalLinks(True)

        self.gridLayout.addWidget(self.entrez_lbl2, 3, 0, 1, 6)

        self.line_2 = QFrame(BlastConfig)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_2, 4, 0, 1, 6)

        self.scoring_params_lbl = QLabel(BlastConfig)
        self.scoring_params_lbl.setObjectName(u"scoring_params_lbl")

        self.gridLayout.addWidget(self.scoring_params_lbl, 5, 0, 1, 2)

        self.matrix_lbl = QLabel(BlastConfig)
        self.matrix_lbl.setObjectName(u"matrix_lbl")

        self.gridLayout.addWidget(self.matrix_lbl, 6, 0, 1, 1)

        self.gapcost_lbl = QLabel(BlastConfig)
        self.gapcost_lbl.setObjectName(u"gapcost_lbl")

        self.gridLayout.addWidget(self.gapcost_lbl, 7, 0, 1, 1)

        self.compadj_lbl = QLabel(BlastConfig)
        self.compadj_lbl.setObjectName(u"compadj_lbl")

        self.gridLayout.addWidget(self.compadj_lbl, 8, 0, 1, 2)

        self.compadj_combo = QComboBox(BlastConfig)
        self.compadj_combo.addItem("")
        self.compadj_combo.addItem("")
        self.compadj_combo.addItem("")
        self.compadj_combo.addItem("")
        self.compadj_combo.setObjectName(u"compadj_combo")

        self.gridLayout.addWidget(self.compadj_combo, 8, 2, 1, 4)

        self.line = QFrame(BlastConfig)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line, 9, 0, 1, 6)

        self.general_params_lbl = QLabel(BlastConfig)
        self.general_params_lbl.setObjectName(u"general_params_lbl")

        self.gridLayout.addWidget(self.general_params_lbl, 10, 0, 1, 2)

        self.maxhits_lbl = QLabel(BlastConfig)
        self.maxhits_lbl.setObjectName(u"maxhits_lbl")
        self.maxhits_lbl.setWordWrap(True)

        self.gridLayout.addWidget(self.maxhits_lbl, 11, 0, 1, 1)

        self.maxhits_spin = QSpinBox(BlastConfig)
        self.maxhits_spin.setObjectName(u"maxhits_spin")
        self.maxhits_spin.setMinimum(1)
        self.maxhits_spin.setMaximum(20000)
        self.maxhits_spin.setValue(1337)

        self.gridLayout.addWidget(self.maxhits_spin, 11, 2, 1, 2)

        self.label = QLabel(BlastConfig)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.gridLayout.addWidget(self.label, 11, 4, 1, 2)

        self.wordsize_lbl = QLabel(BlastConfig)
        self.wordsize_lbl.setObjectName(u"wordsize_lbl")

        self.gridLayout.addWidget(self.wordsize_lbl, 12, 0, 1, 1)

        self.wordsize_combo = QComboBox(BlastConfig)
        self.wordsize_combo.addItem("")
        self.wordsize_combo.addItem("")
        self.wordsize_combo.addItem("")
        self.wordsize_combo.setObjectName(u"wordsize_combo")

        self.gridLayout.addWidget(self.wordsize_combo, 12, 2, 1, 1)

        self.expect_lbl = QLabel(BlastConfig)
        self.expect_lbl.setObjectName(u"expect_lbl")

        self.gridLayout.addWidget(self.expect_lbl, 13, 0, 1, 1)

        self.expect_spin = QSpinBox(BlastConfig)
        self.expect_spin.setObjectName(u"expect_spin")
        self.expect_spin.setMinimum(-999)
        self.expect_spin.setMaximum(100)
        self.expect_spin.setValue(-10)

        self.gridLayout.addWidget(self.expect_spin, 13, 2, 1, 2)

        self.line_4 = QFrame(BlastConfig)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.HLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_4, 14, 0, 1, 6)

        self.filters_and_masking = QLabel(BlastConfig)
        self.filters_and_masking.setObjectName(u"filters_and_masking")

        self.gridLayout.addWidget(self.filters_and_masking, 15, 0, 1, 2)

        self.filter_lbl = QLabel(BlastConfig)
        self.filter_lbl.setObjectName(u"filter_lbl")

        self.gridLayout.addWidget(self.filter_lbl, 16, 0, 1, 1)

        self.filter_chk = QCheckBox(BlastConfig)
        self.filter_chk.setObjectName(u"filter_chk")

        self.gridLayout.addWidget(self.filter_chk, 16, 2, 1, 2)

        self.mask_lbl = QLabel(BlastConfig)
        self.mask_lbl.setObjectName(u"mask_lbl")

        self.gridLayout.addWidget(self.mask_lbl, 17, 0, 1, 1)

        self.mask_chk = QCheckBox(BlastConfig)
        self.mask_chk.setObjectName(u"mask_chk")

        self.gridLayout.addWidget(self.mask_chk, 17, 2, 1, 2)

        self.cancel_btn = QPushButton(BlastConfig)
        self.cancel_btn.setObjectName(u"cancel_btn")

        self.gridLayout.addWidget(self.cancel_btn, 18, 0, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(38, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 18, 1, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(29, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 18, 2, 1, 1)

        self.applydefaults_btn = QPushButton(BlastConfig)
        self.applydefaults_btn.setObjectName(u"applydefaults_btn")

        self.gridLayout.addWidget(self.applydefaults_btn, 18, 3, 1, 1)

        self.horizontalSpacer = QSpacerItem(188, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 18, 4, 1, 1)

        self.apply_btn = QPushButton(BlastConfig)
        self.apply_btn.setObjectName(u"apply_btn")
        self.apply_btn.setMaximumSize(QSize(80, 16777215))

        self.gridLayout.addWidget(self.apply_btn, 18, 5, 1, 1)

        self.entrez_ledit = QLineEdit(BlastConfig)
        self.entrez_ledit.setObjectName(u"entrez_ledit")

        self.gridLayout.addWidget(self.entrez_ledit, 2, 2, 1, 4)

        self.matrix_combo = QComboBox(BlastConfig)
        self.matrix_combo.addItem("")
        self.matrix_combo.addItem("")
        self.matrix_combo.addItem("")
        self.matrix_combo.addItem("")
        self.matrix_combo.addItem("")
        self.matrix_combo.addItem("")
        self.matrix_combo.addItem("")
        self.matrix_combo.addItem("")
        self.matrix_combo.setObjectName(u"matrix_combo")

        self.gridLayout.addWidget(self.matrix_combo, 6, 2, 1, 4)

        self.gapcost_combo = QComboBox(BlastConfig)
        self.gapcost_combo.addItem("")
        self.gapcost_combo.addItem("")
        self.gapcost_combo.addItem("")
        self.gapcost_combo.addItem("")
        self.gapcost_combo.addItem("")
        self.gapcost_combo.addItem("")
        self.gapcost_combo.addItem("")
        self.gapcost_combo.addItem("")
        self.gapcost_combo.addItem("")
        self.gapcost_combo.addItem("")
        self.gapcost_combo.addItem("")
        self.gapcost_combo.setObjectName(u"gapcost_combo")

        self.gridLayout.addWidget(self.gapcost_combo, 7, 2, 1, 4)


        self.retranslateUi(BlastConfig)

        self.compadj_combo.setCurrentIndex(2)
        self.wordsize_combo.setCurrentIndex(2)
        self.matrix_combo.setCurrentIndex(5)
        self.gapcost_combo.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(BlastConfig)
    # setupUi

    def retranslateUi(self, BlastConfig):
        BlastConfig.setWindowTitle(QCoreApplication.translate("BlastConfig", u"Form", None))
        self.searchset_lbl.setText(QCoreApplication.translate("BlastConfig", u"<html><head/><body><p><span style=\" font-weight:600;\">Search Set:</span></p></body></html>", None))
        self.database_lbl.setText(QCoreApplication.translate("BlastConfig", u"Database", None))
        self.database_combo.setItemText(0, QCoreApplication.translate("BlastConfig", u"Non-redundant proteins equences (nr)", None))
        self.database_combo.setItemText(1, QCoreApplication.translate("BlastConfig", u"RefSeq Select proteins (refseq_select)", None))
        self.database_combo.setItemText(2, QCoreApplication.translate("BlastConfig", u"Reference proteins (refseq_protein)", None))
        self.database_combo.setItemText(3, QCoreApplication.translate("BlastConfig", u"Model Organisms (landmark)", None))
        self.database_combo.setItemText(4, QCoreApplication.translate("BlastConfig", u"UniProtKB/Swiss-Prot (swissprot)", None))
        self.database_combo.setItemText(5, QCoreApplication.translate("BlastConfig", u"Patented protein sequences (pataa)", None))
        self.database_combo.setItemText(6, QCoreApplication.translate("BlastConfig", u"Protein Data Bank proteins (pdb)", None))
        self.database_combo.setItemText(7, QCoreApplication.translate("BlastConfig", u"Metagenomic proteins (env_nr)", None))
        self.database_combo.setItemText(8, QCoreApplication.translate("BlastConfig", u"Transcriptome Shotgun Assembly proteins (tsa_nr)", None))

        self.entrez_lbl.setText(QCoreApplication.translate("BlastConfig", u"Entrez Query*", None))
        self.entrez_lbl2.setText(QCoreApplication.translate("BlastConfig", u"<html><head/><body><p>* - Optional. Use to restrict search to specified taxa. See <a href=\"https://www.ncbi.nlm.nih.gov/books/NBK3837/#_EntrezHelp_Entrez_Searching_Options_\"><span style=\" text-decoration: underline; color:#0000ff;\">ncbi.nlm.nih.gov</span></a> for details.</p><p><span style=\" font-style:italic; color:#4b4b4b;\">Briefly, each taxon to which you wish to limit your query must be followed up by [Organism] to tell NCBI which category of keyword it is. To limit to multiple separate taxa, the terms must be joined together by the operator OR. For example &quot;Streptomycetales[Organism] OR Ascomycota[Organism]&quot; will yield results for species belonging to Streptomycetales or Ascomycota.</span></p></body></html>", None))
        self.scoring_params_lbl.setText(QCoreApplication.translate("BlastConfig", u"<html><head/><body><p><span style=\" font-weight:600;\">Scoring Parameters:</span></p></body></html>", None))
        self.matrix_lbl.setText(QCoreApplication.translate("BlastConfig", u"Matrix", None))
        self.gapcost_lbl.setText(QCoreApplication.translate("BlastConfig", u"Gap Costs", None))
        self.compadj_lbl.setText(QCoreApplication.translate("BlastConfig", u"Compositional adjustments", None))
        self.compadj_combo.setItemText(0, QCoreApplication.translate("BlastConfig", u"No adjustment", None))
        self.compadj_combo.setItemText(1, QCoreApplication.translate("BlastConfig", u"Composition-based statistics", None))
        self.compadj_combo.setItemText(2, QCoreApplication.translate("BlastConfig", u"Conditional compositional score matrix adjustment", None))
        self.compadj_combo.setItemText(3, QCoreApplication.translate("BlastConfig", u"Universal compositional score matrix adjustment", None))

        self.compadj_combo.setCurrentText(QCoreApplication.translate("BlastConfig", u"Conditional compositional score matrix adjustment", None))
        self.general_params_lbl.setText(QCoreApplication.translate("BlastConfig", u"<html><head/><body><p><span style=\" font-weight:600;\">General Parameters:</span></p></body></html>", None))
        self.maxhits_lbl.setText(QCoreApplication.translate("BlastConfig", u"<html><head/><body><p>Max target sequences </p></body></html>", None))
        self.label.setText(QCoreApplication.translate("BlastConfig", u"<html><head/><body><p><span style=\" font-style:italic;\">Instead of increasing this above 5000, please consider using an Entrez query to limit your search to a specific taxonomic group.</span></p></body></html>", None))
        self.wordsize_lbl.setText(QCoreApplication.translate("BlastConfig", u"Word Size", None))
        self.wordsize_combo.setItemText(0, QCoreApplication.translate("BlastConfig", u"2", None))
        self.wordsize_combo.setItemText(1, QCoreApplication.translate("BlastConfig", u"3", None))
        self.wordsize_combo.setItemText(2, QCoreApplication.translate("BlastConfig", u"6", None))

        self.wordsize_combo.setCurrentText(QCoreApplication.translate("BlastConfig", u"6", None))
        self.expect_lbl.setText(QCoreApplication.translate("BlastConfig", u"Expect threshold", None))
        self.expect_spin.setSuffix("")
        self.expect_spin.setPrefix(QCoreApplication.translate("BlastConfig", u"10^", None))
        self.filters_and_masking.setText(QCoreApplication.translate("BlastConfig", u"<html><head/><body><p><span style=\" font-weight:600;\">Filters and Masking</span></p></body></html>", None))
        self.filter_lbl.setText(QCoreApplication.translate("BlastConfig", u"Filter", None))
        self.filter_chk.setText(QCoreApplication.translate("BlastConfig", u"Low complexity regions", None))
        self.mask_lbl.setText(QCoreApplication.translate("BlastConfig", u"Mask", None))
        self.mask_chk.setText(QCoreApplication.translate("BlastConfig", u"Mask for lookup table only", None))
        self.cancel_btn.setText(QCoreApplication.translate("BlastConfig", u"Cancel", None))
        self.applydefaults_btn.setText(QCoreApplication.translate("BlastConfig", u"Enter Default Values", None))
        self.apply_btn.setText(QCoreApplication.translate("BlastConfig", u"Apply", None))
        self.entrez_ledit.setPlaceholderText(QCoreApplication.translate("BlastConfig", u"Streptomycetales[Organism] OR Ascomycota[Organism] OR ...", None))
        self.matrix_combo.setItemText(0, QCoreApplication.translate("BlastConfig", u"PAM250", None))
        self.matrix_combo.setItemText(1, QCoreApplication.translate("BlastConfig", u"PAM70", None))
        self.matrix_combo.setItemText(2, QCoreApplication.translate("BlastConfig", u"PAM30", None))
        self.matrix_combo.setItemText(3, QCoreApplication.translate("BlastConfig", u"BLOSUM90", None))
        self.matrix_combo.setItemText(4, QCoreApplication.translate("BlastConfig", u"BLOSUM80", None))
        self.matrix_combo.setItemText(5, QCoreApplication.translate("BlastConfig", u"BLOSUM62", None))
        self.matrix_combo.setItemText(6, QCoreApplication.translate("BlastConfig", u"BLOSUM50", None))
        self.matrix_combo.setItemText(7, QCoreApplication.translate("BlastConfig", u"BLOSUM45", None))

        self.matrix_combo.setCurrentText(QCoreApplication.translate("BlastConfig", u"BLOSUM62", None))
        self.gapcost_combo.setItemText(0, QCoreApplication.translate("BlastConfig", u"Existence: 13 Extension: 1", None))
        self.gapcost_combo.setItemText(1, QCoreApplication.translate("BlastConfig", u"Existence: 12 Extension: 1", None))
        self.gapcost_combo.setItemText(2, QCoreApplication.translate("BlastConfig", u"Existence: 11 Extension: 1", None))
        self.gapcost_combo.setItemText(3, QCoreApplication.translate("BlastConfig", u"Existence: 10 Extension: 1", None))
        self.gapcost_combo.setItemText(4, QCoreApplication.translate("BlastConfig", u"Existence: 9 Extension: 1", None))
        self.gapcost_combo.setItemText(5, QCoreApplication.translate("BlastConfig", u"Exsitence: 11 Extension: 2", None))
        self.gapcost_combo.setItemText(6, QCoreApplication.translate("BlastConfig", u"Exsitence: 10 Extension: 2", None))
        self.gapcost_combo.setItemText(7, QCoreApplication.translate("BlastConfig", u"Exsitence: 9 Extension: 2", None))
        self.gapcost_combo.setItemText(8, QCoreApplication.translate("BlastConfig", u"Exsitence: 8 Extension: 2", None))
        self.gapcost_combo.setItemText(9, QCoreApplication.translate("BlastConfig", u"Exsitence: 7 Extension: 2", None))
        self.gapcost_combo.setItemText(10, QCoreApplication.translate("BlastConfig", u"Exsitence: 6 Extension: 2", None))

        self.gapcost_combo.setCurrentText(QCoreApplication.translate("BlastConfig", u"Existence: 11 Extension: 1", None))
    # retranslateUi

