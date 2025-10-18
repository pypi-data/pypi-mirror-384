# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'proteingrouptable.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ProteinGroupTable(object):
    def setupUi(self, ProteinGroupTable):
        if not ProteinGroupTable.objectName():
            ProteinGroupTable.setObjectName(u"ProteinGroupTable")
        ProteinGroupTable.resize(1028, 685)
        self.gridLayout = QGridLayout(ProteinGroupTable)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setVerticalSpacing(4)
        self.widget = QWidget(ProteinGroupTable)
        self.widget.setObjectName(u"widget")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.toolbar_row = QHBoxLayout(self.widget)
        self.toolbar_row.setSpacing(3)
        self.toolbar_row.setObjectName(u"toolbar_row")
        self.toolbar_row.setContentsMargins(0, 0, 0, 0)
        self.displayed_groups_combo = QComboBox(self.widget)
        self.displayed_groups_combo.addItem("")
        self.displayed_groups_combo.addItem("")
        self.displayed_groups_combo.addItem("")
        self.displayed_groups_combo.setObjectName(u"displayed_groups_combo")

        self.toolbar_row.addWidget(self.displayed_groups_combo)

        self.line = QFrame(self.widget)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.toolbar_row.addWidget(self.line)

        self.search_bar = QLineEdit(self.widget)
        self.search_bar.setObjectName(u"search_bar")

        self.toolbar_row.addWidget(self.search_bar)

        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")

        self.toolbar_row.addWidget(self.label_3)

        self.search_category_combo = QComboBox(self.widget)
        self.search_category_combo.addItem("")
        self.search_category_combo.addItem("")
        self.search_category_combo.addItem("")
        self.search_category_combo.addItem("")
        self.search_category_combo.setObjectName(u"search_category_combo")

        self.toolbar_row.addWidget(self.search_category_combo)

        self.info_btn = QToolButton(self.widget)
        self.info_btn.setObjectName(u"info_btn")

        self.toolbar_row.addWidget(self.info_btn)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.toolbar_row.addItem(self.horizontalSpacer)


        self.gridLayout.addWidget(self.widget, 0, 0, 1, 2)

        self.cluster_table = QTableWidget(ProteinGroupTable)
        self.cluster_table.setObjectName(u"cluster_table")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.cluster_table.sizePolicy().hasHeightForWidth())
        self.cluster_table.setSizePolicy(sizePolicy1)

        self.gridLayout.addWidget(self.cluster_table, 2, 0, 1, 2)

        self.info_lbl = QLabel(ProteinGroupTable)
        self.info_lbl.setObjectName(u"info_lbl")
        self.info_lbl.setWordWrap(True)

        self.gridLayout.addWidget(self.info_lbl, 1, 0, 1, 2)


        self.retranslateUi(ProteinGroupTable)

        QMetaObject.connectSlotsByName(ProteinGroupTable)
    # setupUi

    def retranslateUi(self, ProteinGroupTable):
        ProteinGroupTable.setWindowTitle(QCoreApplication.translate("ProteinGroupTable", u"Form", None))
        self.displayed_groups_combo.setItemText(0, QCoreApplication.translate("ProteinGroupTable", u"Groups", None))
        self.displayed_groups_combo.setItemText(1, QCoreApplication.translate("ProteinGroupTable", u"Subgroups", None))
        self.displayed_groups_combo.setItemText(2, QCoreApplication.translate("ProteinGroupTable", u"User-created", None))

#if QT_CONFIG(tooltip)
        self.displayed_groups_combo.setToolTip(QCoreApplication.translate("ProteinGroupTable", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Only displays a subset of all protein groups available.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Protein groups are hierarchically organized, meaning that certain groups are subsets of other groups.</p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-"
                        "indent:0px;\"><br />- Global sequence alignment-based groups are homogenous, but only contain very similar proteins.</p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">- Local sequence alignment-based groups combine the previous type into larger groups which are more heterogenous, allowing for more distant similarities between proteins to be seen but also may threaten to bring in </p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">- The user may use user-created groups to combine / re-allocate the above two types</p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">- The toplevel option simply displays the topmost group of each hierarchy, regardless of type.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-i"
                        "ndent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">EXAMPLE of a protein group hierarchy:</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">User-created group</p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">  |-- Local sequence alignment-based group</p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">  |     |-- Global sequence alignment-based group</p"
                        ">\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">  |     |-- Global sequence alignment-based group</p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">  |</p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">  |-- Local sequence alignment-based group</p>\n"
"<p style=\" margin-top:2px; margin-bottom:2px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">         |-- Global sequence alignment-based group</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("ProteinGroupTable", u"in", None))
        self.search_category_combo.setItemText(0, QCoreApplication.translate("ProteinGroupTable", u"All fields", None))
        self.search_category_combo.setItemText(1, QCoreApplication.translate("ProteinGroupTable", u"Group identifiers", None))
        self.search_category_combo.setItemText(2, QCoreApplication.translate("ProteinGroupTable", u"All annotations", None))
        self.search_category_combo.setItemText(3, QCoreApplication.translate("ProteinGroupTable", u"Top annotation", None))

        self.info_btn.setText(QCoreApplication.translate("ProteinGroupTable", u"?", None))
        self.info_lbl.setText(QCoreApplication.translate("ProteinGroupTable", u"<html><head/><body><p><span style=\" font-style:italic; color:#585858;\">This section shows all groups of similar proteins. Clicking column headers sorts their respective columns (except for the ID column). Clicking again inverts the sorting order (you will probably need to click twice).</span></p><p><span style=\" font-style:italic; color:#585858;\">Note that if you wish to select protein groups from this table for use within cluseek, you will need to click the protein group's representation in the ID column as you would in cluster view, or tick the checkbox on the left. The highlighting of individual cells in the table is currently only used for copy+pasting their contents.</span></p></body></html>", None))
    # retranslateUi

