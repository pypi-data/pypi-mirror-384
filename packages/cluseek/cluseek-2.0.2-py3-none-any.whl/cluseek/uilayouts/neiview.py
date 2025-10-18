# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'neiview.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_NeiView(object):
    def setupUi(self, NeiView):
        if not NeiView.objectName():
            NeiView.setObjectName(u"NeiView")
        NeiView.resize(1186, 563)
        self.gridLayout_3 = QGridLayout(NeiView)
        self.gridLayout_3.setSpacing(1)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(4, 4, 4, 4)
        self.toolbar = QWidget(NeiView)
        self.toolbar.setObjectName(u"toolbar")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolbar.sizePolicy().hasHeightForWidth())
        self.toolbar.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(self.toolbar)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(4, 1, 4, 1)
        self.displayname_lbl = QLabel(self.toolbar)
        self.displayname_lbl.setObjectName(u"displayname_lbl")

        self.horizontalLayout.addWidget(self.displayname_lbl)

        self.displayname_ledit = QLineEdit(self.toolbar)
        self.displayname_ledit.setObjectName(u"displayname_ledit")
        self.displayname_ledit.setMaximumSize(QSize(130, 16777215))

        self.horizontalLayout.addWidget(self.displayname_ledit)

        self.delete_btn = QToolButton(self.toolbar)
        self.delete_btn.setObjectName(u"delete_btn")

        self.horizontalLayout.addWidget(self.delete_btn)

        self.config_btn = QToolButton(self.toolbar)
        self.config_btn.setObjectName(u"config_btn")

        self.horizontalLayout.addWidget(self.config_btn)

        self.tool_export = QToolButton(self.toolbar)
        self.tool_export.setObjectName(u"tool_export")

        self.horizontalLayout.addWidget(self.tool_export)

        self.line = QFrame(self.toolbar)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.line_7 = QFrame(self.toolbar)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setFrameShape(QFrame.VLine)
        self.line_7.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line_7)

        self.label = QLabel(self.toolbar)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.tool_hide1 = QToolButton(self.toolbar)
        self.tool_hide1.setObjectName(u"tool_hide1")

        self.horizontalLayout.addWidget(self.tool_hide1)

        self.tool_hide2 = QToolButton(self.toolbar)
        self.tool_hide2.setObjectName(u"tool_hide2")

        self.horizontalLayout.addWidget(self.tool_hide2)

        self.tool_hide3 = QToolButton(self.toolbar)
        self.tool_hide3.setObjectName(u"tool_hide3")

        self.horizontalLayout.addWidget(self.tool_hide3)

        self.label_2 = QLabel(self.toolbar)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)

        self.tool_hide4 = QToolButton(self.toolbar)
        self.tool_hide4.setObjectName(u"tool_hide4")

        self.horizontalLayout.addWidget(self.tool_hide4)

        self.line_6 = QFrame(self.toolbar)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.VLine)
        self.line_6.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line_6)

        self.line_8 = QFrame(self.toolbar)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setFrameShape(QFrame.VLine)
        self.line_8.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line_8)

        self.legend_btn = QToolButton(self.toolbar)
        self.legend_btn.setObjectName(u"legend_btn")

        self.horizontalLayout.addWidget(self.legend_btn)

        self.horizontalSpacer_2 = QSpacerItem(747, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.gridLayout_3.addWidget(self.toolbar, 0, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(1)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lefttabs_tabs = QTabWidget(NeiView)
        self.lefttabs_tabs.setObjectName(u"lefttabs_tabs")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lefttabs_tabs.sizePolicy().hasHeightForWidth())
        self.lefttabs_tabs.setSizePolicy(sizePolicy1)
        self.lefttabs_tabs.setMinimumSize(QSize(0, 0))
        self.lefttabs_tabs.setTabPosition(QTabWidget.North)

        self.horizontalLayout_2.addWidget(self.lefttabs_tabs)

        self.main_splitter = QSplitter(NeiView)
        self.main_splitter.setObjectName(u"main_splitter")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.main_splitter.sizePolicy().hasHeightForWidth())
        self.main_splitter.setSizePolicy(sizePolicy2)
        self.main_splitter.setOrientation(Qt.Horizontal)
        self.main_splitter.setOpaqueResize(False)
        self.main_splitter.setChildrenCollapsible(False)
        self.clusterview_frame = QFrame(self.main_splitter)
        self.clusterview_frame.setObjectName(u"clusterview_frame")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.clusterview_frame.sizePolicy().hasHeightForWidth())
        self.clusterview_frame.setSizePolicy(sizePolicy3)
        self.clusterview_frame.setFrameShape(QFrame.Panel)
        self.clusterview_frame.setFrameShadow(QFrame.Raised)
        self.gridLayout_2 = QGridLayout(self.clusterview_frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setHorizontalSpacing(0)
        self.gridLayout_2.setVerticalSpacing(2)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.clusterview_toolbar = QWidget(self.clusterview_frame)
        self.clusterview_toolbar.setObjectName(u"clusterview_toolbar")
        sizePolicy.setHeightForWidth(self.clusterview_toolbar.sizePolicy().hasHeightForWidth())
        self.clusterview_toolbar.setSizePolicy(sizePolicy)
        self.horizontalLayout_3 = QHBoxLayout(self.clusterview_toolbar)
        self.horizontalLayout_3.setSpacing(1)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(4, 0, 4, 0)
        self.searchbar_ledit = QLineEdit(self.clusterview_toolbar)
        self.searchbar_ledit.setObjectName(u"searchbar_ledit")
        sizePolicy4 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.searchbar_ledit.sizePolicy().hasHeightForWidth())
        self.searchbar_ledit.setSizePolicy(sizePolicy4)

        self.horizontalLayout_3.addWidget(self.searchbar_ledit)

        self.line_2 = QFrame(self.clusterview_toolbar)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setLineWidth(2)
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_3.addWidget(self.line_2)

        self.sort_btn = QToolButton(self.clusterview_toolbar)
        self.sort_btn.setObjectName(u"sort_btn")
        self.sort_btn.setPopupMode(QToolButton.MenuButtonPopup)
        self.sort_btn.setArrowType(Qt.NoArrow)

        self.horizontalLayout_3.addWidget(self.sort_btn)

        self.tool_toggle_sizemode = QToolButton(self.clusterview_toolbar)
        self.tool_toggle_sizemode.setObjectName(u"tool_toggle_sizemode")

        self.horizontalLayout_3.addWidget(self.tool_toggle_sizemode)

        self.line_3 = QFrame(self.clusterview_toolbar)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setLineWidth(2)
        self.line_3.setFrameShape(QFrame.VLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_3.addWidget(self.line_3)

        self.line_5 = QFrame(self.clusterview_toolbar)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.VLine)
        self.line_5.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_3.addWidget(self.line_5)

        self.highlightrare_btn = QToolButton(self.clusterview_toolbar)
        self.highlightrare_btn.setObjectName(u"highlightrare_btn")

        self.horizontalLayout_3.addWidget(self.highlightrare_btn)

        self.horizontalSpacer = QSpacerItem(623, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)


        self.gridLayout_2.addWidget(self.clusterview_toolbar, 0, 0, 1, 4)

        self.headers_slide = QWidget(self.clusterview_frame)
        self.headers_slide.setObjectName(u"headers_slide")
        sizePolicy5 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.headers_slide.sizePolicy().hasHeightForWidth())
        self.headers_slide.setSizePolicy(sizePolicy5)
        self.headers_slide_lay = QGridLayout(self.headers_slide)
        self.headers_slide_lay.setSpacing(0)
        self.headers_slide_lay.setObjectName(u"headers_slide_lay")
        self.headers_slide_lay.setContentsMargins(0, 0, 0, 0)
        self.headers_scroller = QScrollArea(self.headers_slide)
        self.headers_scroller.setObjectName(u"headers_scroller")
        sizePolicy2.setHeightForWidth(self.headers_scroller.sizePolicy().hasHeightForWidth())
        self.headers_scroller.setSizePolicy(sizePolicy2)
        self.headers_scroller.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.headers_scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.headers_scroller.setWidgetResizable(True)
        self.headers_scrollable = QWidget()
        self.headers_scrollable.setObjectName(u"headers_scrollable")
        self.headers_scrollable.setGeometry(QRect(0, 0, 69, 486))
        self.headers_scrollable_lay = QVBoxLayout(self.headers_scrollable)
        self.headers_scrollable_lay.setSpacing(0)
        self.headers_scrollable_lay.setObjectName(u"headers_scrollable_lay")
        self.headers_scrollable_lay.setContentsMargins(1, 1, 1, 1)
        self.headers_scroller.setWidget(self.headers_scrollable)

        self.headers_slide_lay.addWidget(self.headers_scroller, 0, 0, 1, 2)

        self.headers_scrollbar = QScrollBar(self.headers_slide)
        self.headers_scrollbar.setObjectName(u"headers_scrollbar")
        self.headers_scrollbar.setMinimumSize(QSize(0, 18))
        self.headers_scrollbar.setOrientation(Qt.Horizontal)

        self.headers_slide_lay.addWidget(self.headers_scrollbar, 1, 0, 1, 2)


        self.gridLayout_2.addWidget(self.headers_slide, 1, 0, 1, 1)

        self.handle_slide = QFrame(self.clusterview_frame)
        self.handle_slide.setObjectName(u"handle_slide")
        self.handle_slide.setFrameShape(QFrame.StyledPanel)
        self.handle_slide.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.handle_slide)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(4, 2, 2, 2)
        self.line_4 = QFrame(self.handle_slide)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShadow(QFrame.Sunken)
        self.line_4.setLineWidth(4)
        self.line_4.setMidLineWidth(2)
        self.line_4.setFrameShape(QFrame.VLine)

        self.horizontalLayout_4.addWidget(self.line_4)


        self.gridLayout_2.addWidget(self.handle_slide, 1, 1, 1, 1)

        self.clusters_slide = QWidget(self.clusterview_frame)
        self.clusters_slide.setObjectName(u"clusters_slide")
        self.clusters_slide_lay = QGridLayout(self.clusters_slide)
        self.clusters_slide_lay.setSpacing(0)
        self.clusters_slide_lay.setObjectName(u"clusters_slide_lay")
        self.clusters_slide_lay.setContentsMargins(0, 0, 0, 0)
        self.horizontal_scrollbar = QScrollBar(self.clusters_slide)
        self.horizontal_scrollbar.setObjectName(u"horizontal_scrollbar")
        self.horizontal_scrollbar.setMinimumSize(QSize(0, 18))
        self.horizontal_scrollbar.setOrientation(Qt.Horizontal)

        self.clusters_slide_lay.addWidget(self.horizontal_scrollbar, 1, 0, 1, 1)

        self.clusters_scroller = QScrollArea(self.clusters_slide)
        self.clusters_scroller.setObjectName(u"clusters_scroller")
        sizePolicy2.setHeightForWidth(self.clusters_scroller.sizePolicy().hasHeightForWidth())
        self.clusters_scroller.setSizePolicy(sizePolicy2)
        self.clusters_scroller.setMidLineWidth(0)
        self.clusters_scroller.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.clusters_scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.clusters_scroller.setWidgetResizable(True)
        self.clusters_scrollable_container = QWidget()
        self.clusters_scrollable_container.setObjectName(u"clusters_scrollable_container")
        self.clusters_scrollable_container.setGeometry(QRect(0, 0, 810, 486))
        self.clusters_scrollable_container_lay = QVBoxLayout(self.clusters_scrollable_container)
        self.clusters_scrollable_container_lay.setSpacing(0)
        self.clusters_scrollable_container_lay.setObjectName(u"clusters_scrollable_container_lay")
        self.clusters_scrollable_container_lay.setContentsMargins(0, 0, 0, 0)
        self.clusters_scrollable = QWidget(self.clusters_scrollable_container)
        self.clusters_scrollable.setObjectName(u"clusters_scrollable")
        sizePolicy6 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.clusters_scrollable.sizePolicy().hasHeightForWidth())
        self.clusters_scrollable.setSizePolicy(sizePolicy6)
        self.clusters_scrollable_lay = QVBoxLayout(self.clusters_scrollable)
        self.clusters_scrollable_lay.setSpacing(1)
        self.clusters_scrollable_lay.setObjectName(u"clusters_scrollable_lay")
        self.clusters_scrollable_lay.setContentsMargins(1, 1, 1, 3)

        self.clusters_scrollable_container_lay.addWidget(self.clusters_scrollable)

        self.clusters_scroller.setWidget(self.clusters_scrollable_container)

        self.clusters_slide_lay.addWidget(self.clusters_scroller, 0, 0, 1, 1)


        self.gridLayout_2.addWidget(self.clusters_slide, 1, 2, 1, 1)

        self.vertical_scrollbar = QScrollBar(self.clusterview_frame)
        self.vertical_scrollbar.setObjectName(u"vertical_scrollbar")
        self.vertical_scrollbar.setOrientation(Qt.Vertical)

        self.gridLayout_2.addWidget(self.vertical_scrollbar, 1, 3, 1, 1)

        self.main_splitter.addWidget(self.clusterview_frame)
        self.right_slide = QFrame(self.main_splitter)
        self.right_slide.setObjectName(u"right_slide")
        sizePolicy7 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.right_slide.sizePolicy().hasHeightForWidth())
        self.right_slide.setSizePolicy(sizePolicy7)
        self.right_slide.setFrameShape(QFrame.Panel)
        self.right_slide.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.right_slide)
        self.gridLayout.setSpacing(1)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.main_splitter.addWidget(self.right_slide)

        self.horizontalLayout_2.addWidget(self.main_splitter)

        self.righttabs_tabs = QTabWidget(NeiView)
        self.righttabs_tabs.setObjectName(u"righttabs_tabs")
        sizePolicy1.setHeightForWidth(self.righttabs_tabs.sizePolicy().hasHeightForWidth())
        self.righttabs_tabs.setSizePolicy(sizePolicy1)
        self.righttabs_tabs.setTabPosition(QTabWidget.North)

        self.horizontalLayout_2.addWidget(self.righttabs_tabs)


        self.gridLayout_3.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)


        self.retranslateUi(NeiView)

        self.lefttabs_tabs.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(NeiView)
    # setupUi

    def retranslateUi(self, NeiView):
        NeiView.setWindowTitle(QCoreApplication.translate("NeiView", u"Form", None))
        self.displayname_lbl.setText(QCoreApplication.translate("NeiView", u"Name:", None))
        self.delete_btn.setText(QCoreApplication.translate("NeiView", u"Delete cluster view", None))
        self.config_btn.setText(QCoreApplication.translate("NeiView", u"Configure", None))
        self.tool_export.setText(QCoreApplication.translate("NeiView", u"Export", None))
        self.label.setText(QCoreApplication.translate("NeiView", u"Displays:", None))
        self.tool_hide1.setText(QCoreApplication.translate("NeiView", u"Info", None))
        self.tool_hide2.setText(QCoreApplication.translate("NeiView", u"Gene clusters", None))
        self.tool_hide3.setText(QCoreApplication.translate("NeiView", u"Protein groups", None))
        self.label_2.setText(QCoreApplication.translate("NeiView", u"Analysis:", None))
        self.tool_hide4.setText(QCoreApplication.translate("NeiView", u"Filtering", None))
        self.legend_btn.setText(QCoreApplication.translate("NeiView", u"? (HELP)", None))
        self.searchbar_ledit.setText("")
        self.searchbar_ledit.setPlaceholderText(QCoreApplication.translate("NeiView", u"Search...", None))
        self.sort_btn.setText(QCoreApplication.translate("NeiView", u"Sort clusters", None))
        self.tool_toggle_sizemode.setText(QCoreApplication.translate("NeiView", u"Fixed sizes", None))
        self.highlightrare_btn.setText(QCoreApplication.translate("NeiView", u"Un/Highlight rare", None))
    # retranslateUi

