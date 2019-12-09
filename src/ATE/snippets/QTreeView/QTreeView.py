# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 16:08:45 2019

@author: hoeren
https://www.programcreek.com/python/example/108086/PyQt5.QtWidgets.QTreeWidgetItem
"""
import sys
from PyQt5 import QtWidgets, QtCore

app = QtWidgets.QApplication(sys.argv)
tree = QtWidgets.QTreeWidget()
tree.setHeaderHidden(True)
headerItem  = QtWidgets.QTreeWidgetItem()
item    = QtWidgets.QTreeWidgetItem()

for i in range(3):
    parent = QtWidgets.QTreeWidgetItem(tree)
    parent.setText(0, "Parent {}".format(i))
    #parent.setFlags(parent.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
    for x in range(5):
        child = QtWidgets.QTreeWidgetItem(parent)
        #child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
        child.setText(0, "Child {}".format(x))
        #child.setCheckState(0, QtCore.Qt.Unchecked)
tree.show() 
sys.exit(app.exec_()) 