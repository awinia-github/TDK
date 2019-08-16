from SpyderMU.core.ABC.plugin import SpyderPluginABC

from PyQt5 import QtWidgets, QtCore, QtMultimedia

import qtawesome as qta
import os

#TODO: try with a button, then this custom class can be skipped :-)
class QLabelEx(QtWidgets.QLabel):
    
    clicked = QtCore.pyqtSignal()
    rightClicked = QtCore.pyqtSignal()
    
    def __init(self, parent):
        super().__init__(parent)

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.rightClicked.emit()
        else:
            self.clicked.emit()

class snapshot(SpyderPluginABC):
    
    service = 'CORE'
    service_type = 'ScreenShot'
    
    def __init__(self, spyder):
        super().__init__(spyder)
        self.camera = QLabelEx()
        self.camera.setPixmap(qta.icon('mdi.camera', color='orange', scale_factor=1).pixmap(16, 16))
        self.camera.clicked.connect(self.camera_snapshot)
        self.camera.rightClicked.connect(self.camera_settings)
        self.camera_click_sound_path = os.path.join(__file__, './resources/sounds/camera-shutter-click-01.wav')
        if not os.path.exists(self.camera_click_sound_path):
            raise FileNotFoundError(self.camera_click_sound_path)
        else:
            self.camera_click_sound = QtMultimedia.QSound(self.camera_click_sound_path)
        #TODO: setup the settings dialog and attach it to camera_settings method

    def enable_action(self):
        self.spyder.statusBar().insertPermanentWidget(0, self.camera)

    def disable_action(self):
        self.spyder.statusBar().removeWidget(self.camera)

    def camera_settings(self): # right clicked
        print("camera right clicked")
        
    def camera_snapshot(self):
        print("camera left clicked") # left clicked
        #TODO: implement the screenshot based on the settings