#!/bin/env python3

# ----- IMPORTS -----
import sys
import os
import time
# PyVista
import pyvista as pv
from pyvistaqt import QtInteractor, MainWindow
# PyQt
from PyQt5 import QtWidgets, QtCore

# ----- APP WINDOW -----
class SVTAppWindow(MainWindow):
    # Constructor
    def __init__(self, parent=None, show=True):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.setWindowTitle("SVT")

        # Playback options
        self.fps = 60 # Animation frames per second
        self.playing = False
        self.outputGif = False
        self.meshes = []
        self.meshfiles = []
        self.v2h = False
        self.actor = None

        self.bgPlotter = pv.Plotter(notebook=False, off_screen=True)

        windowLayout = QtWidgets.QVBoxLayout()

        self.frame = QtWidgets.QFrame()

        # PyVista plotter
        self.plotter = QtInteractor(self.frame, auto_update=False)

        self.frame.setLayout(windowLayout)

        self.signal_close.connect(self.plotter.close)

        # Menu buttons
        buttonLayout1Frame = QtWidgets.QFrame()
        buttonLayout1 = QtWidgets.QHBoxLayout()
        buttonLayout1Frame.setLayout(buttonLayout1)
        buttonLayout2Frame = QtWidgets.QFrame()
        buttonLayout2 = QtWidgets.QHBoxLayout()
        buttonLayout2Frame.setLayout(buttonLayout2)

        # Load dir button
        loadDirButton = QtWidgets.QPushButton("Load Directory")
        loadDirButton.clicked.connect(self.openLoadDir)
        buttonLayout1.addWidget(loadDirButton)

        # Play button
        self.playButton = QtWidgets.QPushButton("Play")
        self.playButton.clicked.connect(self.playPause)
        buttonLayout1.addWidget(self.playButton)

        # Layer selector menu
        self.layerSelector = QtWidgets.QComboBox()
        self.layerSelector.addItems([ "Select Layer..." ])
        self.layerSelector.activated.connect(self.displayLocal)
        buttonLayout1.addWidget(self.layerSelector)

        # Automatically convert selected data layer to mesh height
        self.scalarHeightButton = QtWidgets.QPushButton("Height map OFF")
        self.scalarHeightButton.clicked.connect(self.toggleValToHeights)
        buttonLayout2.addWidget(self.scalarHeightButton)

        # Output GIF button
        self.outputGifButton = QtWidgets.QPushButton("GIF output OFF")
        self.outputGifButton.clicked.connect(self.toggleOutputGif)
        buttonLayout2.addWidget(self.outputGifButton)

        # Time slider
        self.frameSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.frameSlider.valueChanged.connect(self.displayLocal)

        # Progress bar
        self.progressBar = QtWidgets.QProgressBar()

        windowLayout.addWidget(buttonLayout1Frame)
        windowLayout.addWidget(buttonLayout2Frame)
        windowLayout.addWidget(self.frameSlider)
        windowLayout.addWidget(self.plotter.interactor)
        windowLayout.addWidget(self.progressBar)

        self.setCentralWidget(self.frame)

        # Play timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.timerPlayFrames)
        self.timer.start(1000 / self.fps)

        if show: self.show()

    def display(self, mesh):
        if self.outputGif:
            self.bgPlotter.clear()
            self.bgPlotter.add_mesh(mesh, scalars=self.layerSelector.currentText(), render=False)
            self.bgPlotter.write_frame()
        self.plotter.clear()
        self.plotter.add_mesh(mesh, scalars=self.layerSelector.currentText(), render=False)

    def displayLocal(self):
        if not self.meshes: return

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
        self.meshfiles = sorted(os.listdir(directory))
        for idx, file in enumerate(self.meshfiles):
            self.meshes.append((file, pv.read(os.path.join(directory, file))))
            self.status(f"Loading {file}...")
            self.progress(int(100 * (idx + 1) / len(self.meshfiles)))

        # Retrieve the layers
        self.layerSelector.clear()
        _, demomesh = self.meshes[0]
        for layer in demomesh.cell_data:
            self.layerSelector.addItem(layer)

        # Reset the slider
        self.frameSlider.setRange(0, len(self.meshfiles) - 1)
        self.frameSlider.setValue(0)

        # Display the first mesh
        if self.meshes:
            self.displayLocal()

    # Set progress bar text
    def status(self, newStatus):
        self.progressBar.setFormat(newStatus)

    # Set progress bar percentage
    def progress(self, newProgress):
        self.progressBar.setValue(newProgress)

    def timerPlayFrames(self):
        if not self.playing: return

        self.playFrame()

    def playFrame(self):
        self.displayLocal()
        self.frameSlider.setValue(self.frameSlider.value() + 1)
        if self.frameSlider.value() >= len(self.meshes):
            self.frameSlider.setValue(0)
        time.sleep(1.0 / self.fps)

    def playPause(self, startFrame = -1):
        self.playing = not self.playing
        if self.playing:
            if startFrame != -1:
                self.frameSlider.setValue(startFrame)

            self.playButton.setText("Stop")
        else:
            self.playButton.setText("Play")

    def toggleOutputGif(self):
        self.outputGif = not self.outputGif
        if self.outputGif:
            self.bgPlotter.open_gif("svt.gif")
            self.outputGifButton.setText("GIF output ON")
        else:
            self.outputGifButton.setText("GIF output OFF")
            self.bgPlotter.close()

    def toggleValToHeights(self):
        if not self.meshes: return

        self.v2h = not self.v2h
        if self.v2h:
            self.scalarHeightButton.setText("Height map ON")
        else:
            self.scalarHeightButton.setText("Height map OFF")
        for idx,(file,mesh) in enumerate(self.meshes):
            self.status(f"Converting mesh {file}...")
            self.progress(int(100 * (idx + 1) / len(self.meshes)))
            if self.v2h:
                mesh = mesh.cell_data_to_point_data()
                vals = mesh.point_data.get_array(self.layerSelector.currentText())
                mesh.points[:, -1] = vals.ravel() * 5
            else:
                mesh.points[:, -1] = 0

# MAIN
def main():
    qtApp = QtWidgets.QApplication([])
    window = SVTAppWindow()
    qtApp.exec()

if __name__ == "__main__":
    main()
