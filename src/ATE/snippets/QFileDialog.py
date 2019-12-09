#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 09:48:46 2019

@author: tho



https://stackoverflow.com/questions/27998880/how-to-use-options-in-qfiledialog-getopenfilename
https://doc.qt.io/archives/qt-4.8/qfiledialog.html#Option-enum
https://doc.qt.io/qt-5/qfiledialog.html
"""


from PyQt5.QtWidgets import (QMainWindow, QTextEdit, 
    QAction, QFileDialog, QApplication)
from PyQt5.QtGui import QIcon
import sys, os
import qdarkstyle

class Example(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    def initUI(self):      

        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()

        openFile = QAction(QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.showDialog)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)       
        
        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('File dialog')
        self.show()
        
        
    def showDialog(self):
        directory = os.getcwd()
        Filter = ''
        initialFilter = ''
        
        # options = QFileDialog.ShowDirsOnly
        options = QFileDialog.DontUseNativeDialog
        

        # fname = QFileDialog.getOpenFileName(self, 'Select Directory', directory=directory, filter=Filter, initialFilter=initialFilter, options=options)

        dname = QFileDialog.getExistingDirectory(self, "Select Directory", options=options)
        print(dname)

        # if fname[0]:
        #     f = open(fname[0], 'r')
        #     with f:
        #         data = f.read()
        #         self.textEdit.setText(data)        
        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    ex = Example()
    sys.exit(app.exec_())