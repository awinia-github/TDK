#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 00:52:37 2019

@author: tho
"""
import os
import atexit

from IPython.zmq.ipkernel import IPKernelApp
from IPython.lib.kernel import find_connection_file
from IPython.frontend.qt.kernelmanager import QtKernelManager
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.config.application import catch_config_error
from PyQt5 import QtCore


class IPythonLocalKernelApp(IPKernelApp):
    DEFAULT_INSTANCE_ARGS = ['']

    @catch_config_error
    def initialize(self, argv=None):
        super(IPythonLocalKernelApp, self).initialize(argv)
        self.kernel.eventloop = self.loop_qt4_nonblocking

    def loop_qt4_nonblocking(self, kernel):
        """Non-blocking version of the ipython qt4 kernel loop"""
        kernel.timer = QtCore.QTimer()
        kernel.timer.timeout.connect(kernel.do_one_iteration)
        kernel.timer.start(1000*kernel._poll_interval)

    def start(self, argv=DEFAULT_INSTANCE_ARGS):
        """Starts IPython kernel app
        argv: arguments passed to kernel
        """
        self.initialize(argv)
        self.heartbeat.start()

        if self.poller is not None:
            self.poller.start()

        self.kernel.start()


class IPythonConsoleQtWidget(RichIPythonWidget):
    _connection_file = None

    def __init__(self, *args, **kw):
        RichIPythonWidget.__init__(self, *args, **kw)
        self._existing = True
        self._may_close = False
        self._confirm_exit = False

    def _init_kernel_manager(self):
        km = QtKernelManager(connection_file=self._connection_file, config=self.config)
        km.load_connection_file()
        km.start_channels(hb=self._heartbeat)
        self.kernel_manager = km
        atexit.register(self.kernel_manager.cleanup_connection_file)

    def connect_kernel(self, connection_file, heartbeat=False):
        self._heartbeat = heartbeat
        if os.path.exists(connection_file):
            self._connection_file = connection_file
        else:
            self._connection_file = find_connection_file(connection_file)

        self._init_kernel_manager()


def main(**kwargs):
    kernelapp = IPythonLocalKernelApp.instance()
    kernelapp.start()

    widget = IPythonConsoleQtWidget()
    widget.connect_kernel(connection_file=kernelapp.connection_file)
    widget.show()

    return widget

if __name__ == "__main__":
    from PyQt4.QtGui import QApplication
    app = QApplication([''])
    main()
    app.exec_()