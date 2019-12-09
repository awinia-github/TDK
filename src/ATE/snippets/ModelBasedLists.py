'''
Created on Nov 22, 2019

@author: hoeren
'''
from PyQt5 import QtGui, QtCore, QtWidgets, uic
import sys


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("cleanlooks")
    
    data = ['one', 'two', 'three', 'four', 'five']

    model = QtCore.QStringListModel(data)
    
    listView = QtWidgets.QListView()
    listView.setModel(model)
    listView.show()

    combobox = QtWidgets.QComboBox()
    combobox.setModel(model)
    combobox.show()
    
    sys.exit(app.exec_())