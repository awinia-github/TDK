# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 16:09:05 2019

@author: hoeren
"""
from PyQt5 import QtGui, QtCore, QtWidgets, uic

import os, re

import pickle

from ATE.org.listings import list_devices, list_products, dict_project_paths
from ATE.org.validation import is_ATE_project

class NewProductWizard(QtWidgets.QDialog):

    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        
        my_ui = __file__.replace('.py', '.ui')
        if not os.path.exists(my_ui):
            raise Exception("can not find %s" % my_ui)
        uic.loadUi(my_ui, self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(' '.join(re.findall('.[^A-Z]*', os.path.basename(__file__).replace('.py', ''))))
 
        self.parent = parent
        self.project_path = os.path.join(self.parent.workspace_path, self.parent.active_project)

        self.existing_devices = [''] + list_devices(self.project_path)
        self.existing_products = list_products(self.project_path)

        from ATE.org.validation import valid_product_name_regex
        rxProductName = QtCore.QRegExp(valid_product_name_regex)
        ProductName_validator = QtGui.QRegExpValidator(rxProductName, self)
        self.ProductName.setText("")        
        self.ProductName.setValidator(ProductName_validator)
        self.ProductName.textChanged.connect(self.verify)

        self.FromDevice.blockSignals(True)
        self.FromDevice.clear()
        self.FromDevice.addItems(self.existing_devices)
        self.FromDevice.setCurrentIndex(0) # this is the empty string !
        self.FromDevice.currentIndexChanged.connect(self.verify)
        self.FromDevice.blockSignals(False)

        self.Feedback.setText("No die name")
        self.Feedback.setStyleSheet('color: orange')
    
        self.CancelButton.clicked.connect(self.CancelButtonPressed)    
        self.OKButton.clicked.connect(self.OKButtonPressed)
        self.OKButton.setEnabled(False)

        self.verify()
        self.show()

    def verify(self):
        if self.ProductName.text() in self.existing_products:
            self.Feedback.setText("Product already exists !")
            self.OKButton.setEnabled(False)
        else:
            if self.FromDevice.currentText() == "":
                self.Feedback.setText("No maskset selected")
                self.OKButton.setEnabled(False)
            else:
                self.Feedback.setText("")
                self.OKButton.setEnabled(True)

    def CancelButtonPressed(self):
        self.accept()
    
    def OKButtonPressed(self):
        product_data = {}
        product_data['defines'] = 'product'
        product_data['product_name'] = self.ProductName.text()
        product_data['from_device'] = self.FromDevice.currentText()
        create_new_product(self.parent.active_project_path, product_data)
        self.accept()

def create_new_product(project_path, product_data):
    '''
    given a project_path, a product_name (in product_data),
    create the appropriate definition file for this new product.
    
        product_data = {'defines' : 'product',
                        'product_name' : str,
                        'from_device' : str}
    '''
    if is_ATE_project(project_path):
        product_root = dict_project_paths(project_path)['product_root']
        product_name = product_data['product_name']
        product_path = os.path.join(product_root, "%s.pickle" % product_name)
        pickle.dump(product_data, open(product_path, 'wb'), protocol=4) # fixing the protocol guarantees compatibility

def new_product_dialog(parent):
    newProductWizard = NewProductWizard(parent)
    newProductWizard.exec_()
    del(newProductWizard)  

if __name__ == '__main__':
    import sys, qdarkstyle
    from ATE.org.actions.dummy_main import DummyMainWindow
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())    
    dummyMainWindow = DummyMainWindow()
    dialog = NewProductWizard(dummyMainWindow)
    dummyMainWindow.register_dialog(dialog)
    sys.exit(app.exec_())    