# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 16:41:09 2019

@author: hoeren

source : https://stackoverflow.com/questions/36555153/pyqt5-closing-terminating-application

"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QToolTip, QPushButton, QMessageBox)
from PyQt5.QtCore import QCoreApplication, Qt


class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        btn = QPushButton("Close", self)
        btn.setToolTip("Close Application")
        # btn.clicked.connect(QCoreApplication.instance().quit)
        # instead of above button signal, try to call closeEvent method below
        btn.clicked.connect(self.closeEvent)

        btn.resize(btn.sizeHint())
        btn.move(410, 118)
        self.setGeometry(30, 450, 500, 150)
        self.setWindowTitle("Terminator")
        self.show()

    def closeEvent(self, event):
        """Generate 'question' dialog on clicking 'X' button in title bar.

        Reimplement the closeEvent() event handler to include a 'Question'
        dialog with options on how to proceed - Save, Close, Cancel buttons
        """
        print("closeEvent")
        reply = QMessageBox.question(
            self, "Message",
            "Are you sure you want to quit? Any unsaved work will be lost.",
            QMessageBox.Save | QMessageBox.Close | QMessageBox.Cancel,
            QMessageBox.Save)

        print(reply)
        if reply == QMessageBox.Close:
            self.close()
        else:
            pass

    def keyPressEvent(self, event):
        """Close application from escape key.

        results in QMessageBox dialog from closeEvent, good but how/why?
        """
        if event.key() == Qt.Key_Escape:
            print("escape key pressed")
            self.close()

if __name__ == '__main__':

    app = QApplication(sys.argv)
    w = Window()
    sys.exit(app.exec_())

