'''
Created on Nov 22, 2019

@author: hoeren
'''
from PyQt5 import QtGui, QtCore, QtWidgets, uic
import sys


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("cleanlooks")
    
    pins = 7
    
    model = QtGui.QStandardItemModel()
    model.setHorizontalHeaderLabels(['Pin#', 'Name'])

    for pin in enumerate(range(pins)):
        
    

    tableView = QtWidgets.QTableView()
    tableView.setModel(model)
    
    header = tableView.horizontalHeader()
    header.setDefaultAlignment(QtCore.Qt.AlignHCenter)
    
    tableView.show()

    sys.exit(app.exec_())