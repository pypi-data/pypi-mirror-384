# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'styledictcreator.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_StyledictCreator(object):
    def setupUi(self, StyledictCreator):
        if not StyledictCreator.objectName():
            StyledictCreator.setObjectName(u"StyledictCreator")
        StyledictCreator.resize(623, 627)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(StyledictCreator.sizePolicy().hasHeightForWidth())
        StyledictCreator.setSizePolicy(sizePolicy)
        self.gridLayout_2 = QGridLayout(StyledictCreator)
        self.gridLayout_2.setSpacing(1)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(3, 3, 3, 3)
        self.cluster_hierarchy_scroller = QScrollArea(StyledictCreator)
        self.cluster_hierarchy_scroller.setObjectName(u"cluster_hierarchy_scroller")
        self.cluster_hierarchy_scroller.setWidgetResizable(True)
        self.cluster_hierarchy_scrollable = QWidget()
        self.cluster_hierarchy_scrollable.setObjectName(u"cluster_hierarchy_scrollable")
        self.cluster_hierarchy_scrollable.setGeometry(QRect(0, 0, 613, 124))
        self.cluster_hierarchy_lay = QHBoxLayout(self.cluster_hierarchy_scrollable)
        self.cluster_hierarchy_lay.setSpacing(0)
        self.cluster_hierarchy_lay.setObjectName(u"cluster_hierarchy_lay")
        self.cluster_hierarchy_lay.setContentsMargins(1, 1, 1, 1)
        self.cluster_hierarchy_scroller.setWidget(self.cluster_hierarchy_scrollable)

        self.gridLayout_2.addWidget(self.cluster_hierarchy_scroller, 0, 0, 1, 1)

        self.container_layout = QHBoxLayout()
        self.container_layout.setSpacing(1)
        self.container_layout.setObjectName(u"container_layout")

        self.gridLayout_2.addLayout(self.container_layout, 1, 0, 1, 1)

        self.widget = QWidget(StyledictCreator)
        self.widget.setObjectName(u"widget")
        self.gridLayout = QGridLayout(self.widget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(2)
        self.gridLayout.setVerticalSpacing(1)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.label_4 = QLabel(self.widget)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 1, 0, 1, 1)

        self.line = QFrame(self.widget)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line, 9, 0, 1, 4)

        self.text_color_btn = QPushButton(self.widget)
        self.text_color_btn.setObjectName(u"text_color_btn")

        self.gridLayout.addWidget(self.text_color_btn, 12, 2, 1, 1)

        self.text_underlined_inherit = QCheckBox(self.widget)
        self.text_underlined_inherit.setObjectName(u"text_underlined_inherit")

        self.gridLayout.addWidget(self.text_underlined_inherit, 18, 4, 1, 1)

        self.text_title_ledit = QLineEdit(self.widget)
        self.text_title_ledit.setObjectName(u"text_title_ledit")

        self.gridLayout.addWidget(self.text_title_ledit, 10, 2, 1, 2)

        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 2, 1, 1, 1)

        self.text_title_inherit = QCheckBox(self.widget)
        self.text_title_inherit.setObjectName(u"text_title_inherit")

        self.gridLayout.addWidget(self.text_title_inherit, 10, 4, 1, 1)

        self.outline_thickness_spinbox = QSpinBox(self.widget)
        self.outline_thickness_spinbox.setObjectName(u"outline_thickness_spinbox")
        self.outline_thickness_spinbox.setMaximumSize(QSize(16777215, 16777215))
        self.outline_thickness_spinbox.setMaximum(15)

        self.gridLayout.addWidget(self.outline_thickness_spinbox, 3, 2, 1, 1)

        self.outline_color_btn = QPushButton(self.widget)
        self.outline_color_btn.setObjectName(u"outline_color_btn")

        self.gridLayout.addWidget(self.outline_color_btn, 1, 2, 1, 1)

        self.foreground_pattern_inherit = QCheckBox(self.widget)
        self.foreground_pattern_inherit.setObjectName(u"foreground_pattern_inherit")

        self.gridLayout.addWidget(self.foreground_pattern_inherit, 8, 4, 1, 1)

        self.foreground_color_btn = QPushButton(self.widget)
        self.foreground_color_btn.setObjectName(u"foreground_color_btn")

        self.gridLayout.addWidget(self.foreground_color_btn, 7, 2, 1, 1)

        self.label_11 = QLabel(self.widget)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout.addWidget(self.label_11, 14, 1, 1, 1)

        self.line_2 = QFrame(self.widget)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_2, 6, 0, 1, 4)

        self.background_color_inherit = QCheckBox(self.widget)
        self.background_color_inherit.setObjectName(u"background_color_inherit")

        self.gridLayout.addWidget(self.background_color_inherit, 5, 4, 1, 1)

        self.outline_color_inherit = QCheckBox(self.widget)
        self.outline_color_inherit.setObjectName(u"outline_color_inherit")

        self.gridLayout.addWidget(self.outline_color_inherit, 1, 4, 1, 1)

        self.text_font_inherit = QCheckBox(self.widget)
        self.text_font_inherit.setObjectName(u"text_font_inherit")

        self.gridLayout.addWidget(self.text_font_inherit, 14, 4, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 12, 3, 1, 1)

        self.selected_cluster_lbl_info = QLabel(self.widget)
        self.selected_cluster_lbl_info.setObjectName(u"selected_cluster_lbl_info")

        self.gridLayout.addWidget(self.selected_cluster_lbl_info, 0, 0, 1, 2)

        self.foreground_color_inherit = QCheckBox(self.widget)
        self.foreground_color_inherit.setObjectName(u"foreground_color_inherit")

        self.gridLayout.addWidget(self.foreground_color_inherit, 7, 4, 1, 1)

        self.label_5 = QLabel(self.widget)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 5, 0, 1, 1)

        self.line_3 = QFrame(self.widget)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_3, 4, 0, 1, 4)

        self.label_14 = QLabel(self.widget)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout.addWidget(self.label_14, 15, 1, 1, 1)

        self.label_10 = QLabel(self.widget)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout.addWidget(self.label_10, 10, 0, 1, 1)

        self.outline_style_inherit = QCheckBox(self.widget)
        self.outline_style_inherit.setObjectName(u"outline_style_inherit")

        self.gridLayout.addWidget(self.outline_style_inherit, 2, 4, 1, 1)

        self.label_12 = QLabel(self.widget)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout.addWidget(self.label_12, 12, 1, 1, 1)

        self.text_formatting_bold = QCheckBox(self.widget)
        self.text_formatting_bold.setObjectName(u"text_formatting_bold")

        self.gridLayout.addWidget(self.text_formatting_bold, 15, 2, 1, 2)

        self.outline_style_combo = QComboBox(self.widget)
        self.outline_style_combo.setObjectName(u"outline_style_combo")

        self.gridLayout.addWidget(self.outline_style_combo, 2, 2, 1, 2)

        self.label_8 = QLabel(self.widget)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout.addWidget(self.label_8, 7, 1, 1, 1)

        self.label_15 = QLabel(self.widget)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setWordWrap(True)

        self.gridLayout.addWidget(self.label_15, 11, 2, 1, 2)

        self.text_italic_inherit = QCheckBox(self.widget)
        self.text_italic_inherit.setObjectName(u"text_italic_inherit")

        self.gridLayout.addWidget(self.text_italic_inherit, 17, 4, 1, 1)

        self.label_7 = QLabel(self.widget)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 7, 0, 1, 1)

        self.background_color_btn = QPushButton(self.widget)
        self.background_color_btn.setObjectName(u"background_color_btn")

        self.gridLayout.addWidget(self.background_color_btn, 5, 2, 1, 1)

        self.text_bold_inherit = QCheckBox(self.widget)
        self.text_bold_inherit.setObjectName(u"text_bold_inherit")

        self.gridLayout.addWidget(self.text_bold_inherit, 15, 4, 1, 1)

        self.outline_thickness_inherit = QCheckBox(self.widget)
        self.outline_thickness_inherit.setObjectName(u"outline_thickness_inherit")

        self.gridLayout.addWidget(self.outline_thickness_inherit, 3, 4, 1, 1)

        self.text_formatting_italic = QCheckBox(self.widget)
        self.text_formatting_italic.setObjectName(u"text_formatting_italic")

        self.gridLayout.addWidget(self.text_formatting_italic, 17, 2, 1, 2)

        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 1, 1, 1, 1)

        self.text_color_inherit = QCheckBox(self.widget)
        self.text_color_inherit.setObjectName(u"text_color_inherit")

        self.gridLayout.addWidget(self.text_color_inherit, 12, 4, 1, 1)

        self.text_font_combo = QFontComboBox(self.widget)
        self.text_font_combo.setObjectName(u"text_font_combo")
        self.text_font_combo.setFontFilters(QFontComboBox.ScalableFonts)

        self.gridLayout.addWidget(self.text_font_combo, 14, 2, 1, 2)

        self.text_formatting_underlined = QCheckBox(self.widget)
        self.text_formatting_underlined.setObjectName(u"text_formatting_underlined")

        self.gridLayout.addWidget(self.text_formatting_underlined, 18, 2, 1, 1)

        self.label_6 = QLabel(self.widget)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 5, 1, 1, 1)

        self.label_13 = QLabel(self.widget)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout.addWidget(self.label_13, 10, 1, 1, 1)

        self.label_9 = QLabel(self.widget)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout.addWidget(self.label_9, 8, 1, 1, 1)

        self.foreground_pattern_combo = QComboBox(self.widget)
        self.foreground_pattern_combo.setObjectName(u"foreground_pattern_combo")

        self.gridLayout.addWidget(self.foreground_pattern_combo, 8, 2, 1, 2)

        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 3, 1, 1, 1)

        self.selected_cluster_lbl = QLabel(self.widget)
        self.selected_cluster_lbl.setObjectName(u"selected_cluster_lbl")
        self.selected_cluster_lbl.setWordWrap(True)

        self.gridLayout.addWidget(self.selected_cluster_lbl, 0, 2, 1, 2)


        self.gridLayout_2.addWidget(self.widget, 2, 0, 1, 1)


        self.retranslateUi(StyledictCreator)

        QMetaObject.connectSlotsByName(StyledictCreator)
    # setupUi

    def retranslateUi(self, StyledictCreator):
        StyledictCreator.setWindowTitle(QCoreApplication.translate("StyledictCreator", u"Form", None))
        self.label_4.setText(QCoreApplication.translate("StyledictCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">Outline</span></p></body></html>", None))
        self.text_color_btn.setText(QCoreApplication.translate("StyledictCreator", u"Set", None))
        self.text_underlined_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Default", None))
        self.label_2.setText(QCoreApplication.translate("StyledictCreator", u"Style:", None))
        self.text_title_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Default", None))
        self.outline_color_btn.setText(QCoreApplication.translate("StyledictCreator", u"Set", None))
        self.foreground_pattern_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Default", None))
        self.foreground_color_btn.setText(QCoreApplication.translate("StyledictCreator", u"Set", None))
        self.label_11.setText(QCoreApplication.translate("StyledictCreator", u"Font:", None))
        self.background_color_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Default", None))
        self.outline_color_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Default", None))
        self.text_font_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Default", None))
        self.selected_cluster_lbl_info.setText(QCoreApplication.translate("StyledictCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">Selected group:</span></p></body></html>", None))
        self.foreground_color_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Default", None))
        self.label_5.setText(QCoreApplication.translate("StyledictCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">Background</span></p></body></html>", None))
        self.label_14.setText(QCoreApplication.translate("StyledictCreator", u"Formatting:", None))
        self.label_10.setText(QCoreApplication.translate("StyledictCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">Text</span></p></body></html>", None))
        self.outline_style_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Reserved", None))
        self.label_12.setText(QCoreApplication.translate("StyledictCreator", u"Color:", None))
        self.text_formatting_bold.setText(QCoreApplication.translate("StyledictCreator", u"Bold", None))
        self.label_8.setText(QCoreApplication.translate("StyledictCreator", u"Color:", None))
        self.label_15.setText(QCoreApplication.translate("StyledictCreator", u"<html><head/><body><p><span style=\" font-style:italic; color:#585858;\">In most contexts, only the group name of the parent group is displayed.</span></p></body></html>", None))
        self.text_italic_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Default", None))
        self.label_7.setText(QCoreApplication.translate("StyledictCreator", u"<html><head/><body><p><span style=\" font-weight:600;\">Foreground</span></p></body></html>", None))
        self.background_color_btn.setText(QCoreApplication.translate("StyledictCreator", u"Set", None))
        self.text_bold_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Default", None))
        self.outline_thickness_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Reserved", None))
        self.text_formatting_italic.setText(QCoreApplication.translate("StyledictCreator", u"Italic", None))
        self.label.setText(QCoreApplication.translate("StyledictCreator", u"Color:", None))
        self.text_color_inherit.setText(QCoreApplication.translate("StyledictCreator", u"Default", None))
        self.text_formatting_underlined.setText(QCoreApplication.translate("StyledictCreator", u"Underlined", None))
        self.label_6.setText(QCoreApplication.translate("StyledictCreator", u"Color:", None))
        self.label_13.setText(QCoreApplication.translate("StyledictCreator", u"Group name", None))
        self.label_9.setText(QCoreApplication.translate("StyledictCreator", u"Pattern:", None))
        self.label_3.setText(QCoreApplication.translate("StyledictCreator", u"Thickness:", None))
        self.selected_cluster_lbl.setText(QCoreApplication.translate("StyledictCreator", u"N/A", None))
    # retranslateUi

