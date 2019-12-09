#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 13:35:12 2019

@author: tho

source : https://stackoverflow.com/questions/51361674/is-there-a-way-to-take-screenshot-of-a-window-in-pyqt5-or-qt5
"""

from PyQt5 import QtWidgets
import sys, os

app = QtWidgets.QApplication(sys.argv)
w = QtWidgets.QWidget()

grab_btn=QtWidgets.QPushButton('Grab Screen')
def click_handler():
    screen = QtWidgets.QApplication.primaryScreen()
    screenshot = screen.grabWindow( w.winId() )
    screenshot.save(os.path.join(os.path.dirname(__file__), 'shot.jpg'), 'jpg')
    w.close()

grab_btn.clicked.connect(click_handler)

layout = QtWidgets.QVBoxLayout()
layout.addWidget(grab_btn)
w.setLayout(layout)
w.show()

sys.exit(app.exec_())
