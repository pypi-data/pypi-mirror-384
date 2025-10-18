# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'NeiviewLegend.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_NeiviewLegend(object):
    def setupUi(self, NeiviewLegend):
        if not NeiviewLegend.objectName():
            NeiviewLegend.setObjectName(u"NeiviewLegend")
        NeiviewLegend.resize(663, 510)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(NeiviewLegend.sizePolicy().hasHeightForWidth())
        NeiviewLegend.setSizePolicy(sizePolicy)
        NeiviewLegend.setMinimumSize(QSize(230, 270))
        self.gridLayout = QGridLayout(NeiviewLegend)
        self.gridLayout.setObjectName(u"gridLayout")
        self.scrollArea = QScrollArea(NeiviewLegend)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 626, 1080))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_7 = QLabel(self.scrollAreaWidgetContents)
        self.label_7.setObjectName(u"label_7")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy1)
        self.label_7.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_7)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout.addWidget(self.scrollArea, 0, 0, 1, 1)


        self.retranslateUi(NeiviewLegend)

        QMetaObject.connectSlotsByName(NeiviewLegend)
    # setupUi

    def retranslateUi(self, NeiviewLegend):
        NeiviewLegend.setWindowTitle(QCoreApplication.translate("NeiviewLegend", u"Form", None))
        self.label_7.setText(QCoreApplication.translate("NeiviewLegend", u"<html><head/><body><p><span style=\" font-size:14pt; font-weight:600;\">Overview</span></p><p>When first loading into CluSeek, only the<span style=\" font-weight:600;\"> Info </span>tab is visible to the left, and the <span style=\" font-weight:600;\">Clusters</span> tab to the right. The <span style=\" font-weight:600;\">Clusters</span> tab is comprised of <span style=\" font-weight:600;\">cluster headers</span> (to the left, featuring names of taxa and sequence IDs) and cluster contents (to the right, showing<span style=\" font-weight:600;\"> protein groups</span> / coding sequences as arrows).</p><p>You can also open the <span style=\" font-weight:600;\">Proteins</span> tab to view a summary of all protein groups in your dataset, and the <span style=\" font-weight:600;\">Filtering</span> tab to select specific clusters based on which proteins they do or do not contain.</p><p><br/></p><p><span style=\" font-size:14pt; font-weight:600;\">Cluster view controls briefly</span></p><p><span style=\" font-style:ita"
                        "lic;\">These are the mouse controls for </span><span style=\" font-weight:600; font-style:italic;\">Clusters</span><span style=\" font-style:italic;\"> tab.</span></p><p><span style=\" font-weight:600;\">Left click: </span>Select protein group or cluster and display relevant information about it in the info section. <span style=\" font-weight:600;\">Drag</span> to copy protein groups into the red fields of the filtering section.</p><p><span style=\" font-weight:600;\">Ctrl + Left click</span>: select multiple protein groups or cluster headers. <span style=\" font-weight:600;\">Drag</span> to copy all selected protein groups into the red fields of the filtering section.</p><p><span style=\" font-weight:600;\">Shift + Left click</span>: Can be used to select a range of cluster headers. <span style=\" font-weight:600;\">Drag</span> in the cluster contents to measure distance in the cluster contents (ruler). This function is also used to select data to export.</p><p><span style=\" font-weight:600;\">Alt + Left cli"
                        "ck:Drag</span> to move cluster contents left and right, or to move cluster headers up and down.</p><p><span style=\" font-weight:600;\">Alt + Double left click</span>: Flip the orientation of the cluster. This can also be done by right clicking a cluster header and choosing &quot;Flip selected&quot;</p><p><span style=\" font-style:italic;\">Note: In order to </span><span style=\" font-weight:600; font-style:italic;\">Drag</span><span style=\" font-style:italic;\">, hold down the indicated mouse button and move your mouse.</span></p><p>Many other functions are accessible by opening the context menu (right clicking) either cluster headers or protein groups. When right clicking protein groups, make sure to try the <span style=\" font-weight:600;\">Align to</span> function and the <span style=\" font-weight:600;\">Set color</span> function. If you wish to rename protein groups or customize the appearance of protein groups in detail, use the <span style=\" font-weight:600;\">Customize</span> function.</p><p><br/></"
                        "p><p><span style=\" font-size:14pt; font-weight:600;\">Cluster view controls not as briefly:</span></p><p>Individual arrows represent protein coding sequences. As proteins are grouped by sequence homology, clicking on a single one will select (highlight) all homologs within the same group. If you have the &quot;Info&quot; tab enabled (it will show up on the left), detailed information about the protein group will be shown.</p><p>You can also right click protein groups to perform additional operations like customizing their appearance or aligning all clusters to that protein group.</p><p>You can also left click, hold and drag protein groups into certain parts of the user interface, like in the Filtering tab.</p><p>Further, there are four modifiers which you can hold to alter how you interact with the mouse:</p><p><span style=\" font-weight:600;\">Ctrl \u2013 Multiple select modifier</span></p><p>Holding Ctrl and left clicking allows you to select multiple individual protein groups. This is useful for example if"
                        " you want to apply the same customization to all of them at once. </p><p>You can also select multiple clusters (rows) in the same way by clicking on their names.</p><p><span style=\" font-weight:600;\">Shift \u2013 Drag select modifier / Ruler</span></p><p>Holding shift and dragging with left mouse lets you measure genetic distances in base pairs. If you highlight a region, you can export its contents using the export menu, which is accessed from the toolbar.<span style=\" font-weight:600;\"> To unselect the region, you need to click again while still holding shift.</span> This is to prevent accidentally unselecting a region you are preparing for export.</p><p>Shift can be also used to select a range of gene clusters (rows) by selecting their names to the left.</p><p><span style=\" font-weight:600;\">Alt \u2013 Movement modifier</span></p><p>Holding alt and dragging with the Left Mouse Button lets you manually align clusters by moving them left and right. You can also grab the names of the clusters on the left"
                        " and move them up and down. Use Alt+Double click on a cluster's body to reverse (flip) its direction.</p><p><span style=\" font-weight:600;\">Un/Highlight rare</span></p><p>With this option selected, protein groups that are only found in one cluster are colored dark gray (unless otherwise customized), and protein groups that are found in fewer than 20% of all displayed clusters are colored light gray. There is currently no way to change the threshold.</p></body></html>", None))
    # retranslateUi

