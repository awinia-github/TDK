# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 17:15:07 2019

@author: hoeren
"""

import sys

from PyQt5 import QtWidgets



app = QtWidgets.QApplication(sys.argv)
tree = QtWidgets.QTreeWidget()
tree.setHeaderHidden(True)

project = QtWidgets.QTreeWidgetItem(tree)
project.setText(0, "HATC")

documentation = QtWidgets.QTreeWidgetItem(project)
documentation.setText(0, 'documentation')

definitions = QtWidgets.QTreeWidgetItem(project, documentation)
definitions.setText(0, 'definitions')

states = QtWidgets.QTreeWidgetItem(definitions)
states.setText(0, 'states')

protocols = QtWidgets.QTreeWidgetItem(definitions, states)
protocols.setText(0, 'protocols')

flows = QtWidgets.QTreeWidgetItem(definitions, protocols)
flows.setText(0, 'flows')

products = QtWidgets.QTreeWidgetItem(definitions, flows)
products.setText(0, 'products')

devices = QtWidgets.QTreeWidgetItem(definitions, products)
devices.setText(0, 'devices')

packages = QtWidgets.QTreeWidgetItem(definitions, devices)
packages.setText(0, 'packages')

dies = QtWidgets.QTreeWidgetItem(definitions, packages)
dies.setText(0, 'dies')

masksets = QtWidgets.QTreeWidgetItem(definitions, dies)
masksets.setText(0, 'masksets')

hardwaresetups = QtWidgets.QTreeWidgetItem(definitions, masksets)
hardwaresetups.setText(0, 'hardwaresetups')

sources = QtWidgets.QTreeWidgetItem(project, definitions)
sources.setText(0, 'source')

tests = QtWidgets.QTreeWidgetItem(sources)
tests.setText(0, 'tests')

ptests = QtWidgets.QTreeWidgetItem(tests)
ptests.setText(0, 'products')

dtests = QtWidgets.QTreeWidgetItem(tests, ptests)
dtests.setText(0, 'dies')

progs = QtWidgets.QTreeWidgetItem(sources, tests)
progs.setText(0, 'programs')

pprogs = QtWidgets.QTreeWidgetItem(progs)
pprogs.setText(0, 'products')

dprogs = QtWidgets.QTreeWidgetItem(progs, pprogs)
dprogs.setText(0, 'dies')








tree.show() 
sys.exit(app.exec_()) 