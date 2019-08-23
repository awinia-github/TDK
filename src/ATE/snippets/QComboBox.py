from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QDialog, QComboBox, QVBoxLayout, QLabel
import sys
 
 
class Window(QDialog):
    def __init__(self):
        super().__init__()
 
        self.title = "PyQt5 Combo Box"
        self.top = 200
        self.left = 500
        self.width = 300
        self.height = 100
 
 
        self.InitWindow()
 
 
    def InitWindow(self):
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
 
        vbox = QVBoxLayout()
 
        self.combo = QComboBox()
        self.combo.currentTextChanged.connect(self.comboChanged)
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItem("Python")
        self.combo.addItem("Java")
        self.combo.addItem("C++")
        self.combo.addItem("C#")
        self.combo.addItem("Ruby")
        self.combo.blockSignals(False)
 
        self.combo.currentTextChanged.connect(self.comboChanged)
 
        self.label = QLabel()
        self.label.setFont(QtGui.QFont("Sanserif", 15))
        self.label.setStyleSheet('color:red')
 
        vbox.addWidget(self.combo)
        vbox.addWidget(self.label)
 
 
        self.setLayout(vbox)
 
        self.show()
 
    def comboChanged(self):
        text = self.combo.currentText()
        self.label.setText("You Have Selected : " + text)
 
 
 
App = QApplication(sys.argv)
window = Window()
sys.exit(App.exec())