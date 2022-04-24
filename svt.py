#!/bin/env python3

import sys
import os
# PyVista
import pyvista as pv
from pyvistaqt import QtInteractor, MainWindow
# PyQt
from PyQt5 import QtWidgets, QtCore

class SVTAppWindow(MainWindow):
    def __init__(self, parent=None, show=True):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.setWindowTitle("SVT")

        windowLayout = QtWidgets.QVBoxLayout()

        self.frame = QtWidgets.QFrame()

        self.plotter = QtInteractor(self.frame)

        self.frame.setLayout(windowLayout)

        self.signal_close.connect(self.plotter.close)

        titleLabel = QtWidgets.QLabel("CFD Solution Viewer Tool")

        buttonLayoutFrame = QtWidgets.QFrame()
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayoutFrame.setLayout(buttonLayout)

        loadDirButton = QtWidgets.QPushButton("Load Directory")
        loadDirButton.clicked.connect(self.openLoadDir)
        buttonLayout.addWidget(loadDirButton)

        self.layerSelector = QtWidgets.QComboBox()
        self.layerSelector.addItems([ "Select Layer..." ])
        self.layerSelector.activated.connect(self.display_local)
        buttonLayout.addWidget(self.layerSelector)

        self.frameSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.frameSlider.valueChanged.connect(self.display_local)

        self.progressBar = QtWidgets.QProgressBar()

        windowLayout.addWidget(titleLabel)
        windowLayout.addWidget(buttonLayoutFrame)
        windowLayout.addWidget(self.frameSlider)
        windowLayout.addWidget(self.plotter.interactor)
        windowLayout.addWidget(self.progressBar)

        self.setCentralWidget(self.frame)

        if show: self.show()

    def display(self, mesh):
        self.plotter.clear()
        self.plotter.add_mesh(mesh, scalars=self.layerSelector.currentText())

    def display_local(self):
        file, mesh = self.meshes[self.frameSlider.value()]
        self.status(f"Viewing {file}")
        self.display(mesh)

    def openLoadDir(self):
        # Call Qt open dir dialog
        dialog = QtWidgets.QFileDialog(self, "Open Directory")
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if not dialog.exec(): return
        # Only load the first selected entry
        # TODO: Support loading multiple dirs
        directory = dialog.selectedFiles()[0]

        self.setWindowTitle(f"SVT: {directory}")

        # Load meshes from directory
        self.meshes = []
        meshfiles = sorted(os.listdir(directory))
        for idx, file in enumerate(meshfiles):
            self.meshes.append((file, pv.read(os.path.join(directory, file))))
            self.status(f"Loading {file}...")
            self.progress(int(100 * (idx + 1) / len(meshfiles)))

        # Retrieve the layers
        self.layerSelector.clear()
        _, demomesh = self.meshes[0]
        for layer in demomesh.cell_data:
            self.layerSelector.addItem(layer)

        # Reset the slider
        self.frameSlider.setRange(0, len(meshfiles) - 1)
        self.frameSlider.setValue(0)

        # Display the first mesh
        if self.meshes:
            self.display_local()

    def status(self, newStatus):
        self.progressBar.setFormat(newStatus)

    def progress(self, newProgress):
        self.progressBar.setValue(newProgress)

# MAIN
def main():
    qtApp = QtWidgets.QApplication([])
    window = SVTAppWindow()
    qtApp.exec()

if __name__ == "__main__":
    main()
