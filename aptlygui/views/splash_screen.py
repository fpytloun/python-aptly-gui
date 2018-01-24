#!/usr/bin/env python3

from PyQt5.QtWidgets import (QGridLayout, QProgressBar, QPushButton, QLabel, QTextEdit, QLineEdit, QDialog)
from PyQt5.QtCore import pyqtSlot

from aptlygui.views.main_window import Window
from aptlygui.workers.aptly_workers import DataThread
from aptlygui.model.data_manager import DataManager


class QLogConsole(QTextEdit):
    def __init__(self, *args, **kwargs):
        super(QLogConsole, self).__init__(*args, **kwargs)
        self.setReadOnly(True)

    @pyqtSlot(str, str)
    def on_log_received(self, msg, severity="info"):
        self.__getattribute__(severity)(msg)

    def write(self, msg, color):
        if not color:
            self.insertPlainText("{0}\n".format(msg))
        else:
            self.insertHtml("<font color={0}>{1}</font><br>".format(color, msg))
        self.ensureCursorVisible()

    def info(self, msg):
        self.write(msg, "blue")

    def debug(self, msg):
        self.write(msg, "gray")

    def error(self, msg):
        self.write(msg, "red")

    def success(self, msg):
        self.write(msg, "green")


class SplashScreen(QDialog):
    def __init__(self):
        super(SplashScreen, self).__init__()
        self.layout = QGridLayout()
        self.progressBar = QProgressBar(self)
        self.urlLabel = QLabel("URL of Aptly :")
        self.urlEdit = QLineEdit("http://127.0.0.1:8089")
        self.loadButton = QPushButton("Connect to aptly")
        self.quitButton = QPushButton("Quit")
        self.dataManager = DataManager()
        self.logConsole = QLogConsole("")

        self.setupUI()

    def load_main_window(self):
        if not self.dataThread.cancelled:
            self.setModal(False)
            self.window = Window(self.dataManager)
            self.window.show()
            self.close()

    def load_publish_connector(self):
        self.logConsole.info("Initializing connection")
        self.progressBar.setValue(0)

        try:
            self.dataManager.create_client(self.urlEdit.text())
        except Exception as e:
            self.logConsole.error(repr(e))
            return

        self.dataThread = DataThread(self.dataManager, self.progressBar)
        self.dataThread.log.connect(self.logConsole.on_log_received)

        self.dataThread.start()
        self.loadButton.disconnect()
        self.loadButton.setText("Cancel")
        self.loadButton.clicked.connect(self.abort_load)
        self.dataThread.finished.connect(self.load_main_window)

    def abort_load(self):
        self.dataThread.cancelled = True
        self.loadButton.setText("Load publish")
        self.loadButton.disconnect()
        self.loadButton.clicked.connect(self.load_publish_connector)

    def setupUI(self):
        self.setWindowTitle("python-aptly GUI")
        self.setFixedSize(600, 200)
        self.setVisible(True)
        self.setLayout(self.layout)

        self.progressBar.setVisible(True)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)

        self.layout.addWidget(self.urlLabel)
        self.layout.addWidget(self.urlEdit)
        self.layout.addWidget(self.loadButton)
        self.layout.addWidget(self.progressBar)
        self.layout.addWidget(self.logConsole)
        self.layout.addWidget(self.quitButton)

        self.loadButton.clicked.connect(self.load_publish_connector)
        self.quitButton.clicked.connect(self.close)