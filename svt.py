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

        self._titleBase = "SVT"

        self.setWindowTitle(self._titleBase)

        # Playback options
        self.playing    = False
        self.outputGif  = False
        self.meshes     = []
        self.meshfiles  = []
        self.v2h        = False
        self.actor      = None

        # Background plotter for GIF output
        self.bgPlotter = pv.Plotter(notebook=False, off_screen=True)

        self.frame = QtWidgets.QFrame()

        # Window layout
        windowLayout = QtWidgets.QVBoxLayout()
        self.frame.setLayout(windowLayout)

        # PyVista plotter
        self.plotter = QtInteractor(self.frame, auto_update=False)
        self.signal_close.connect(self.plotter.close)

        # Menu button rows
        fileButtonLayoutFrame = QtWidgets.QFrame()
        fileButtonLayout = QtWidgets.QHBoxLayout()
        fileButtonLayout.setContentsMargins(0, 0, 0, 0)
        fileButtonLayoutFrame.setLayout(fileButtonLayout)
        viewButtonLayoutFrame = QtWidgets.QFrame()
        viewButtonLayout = QtWidgets.QHBoxLayout()
        viewButtonLayout.setContentsMargins(0, 0, 0, 0)
        viewButtonLayoutFrame.setLayout(viewButtonLayout)
        playbackButtonLayoutFrame = QtWidgets.QFrame()
        playbackButtonLayout = QtWidgets.QHBoxLayout()
        playbackButtonLayout.setContentsMargins(0, 0, 0, 0)
        playbackButtonLayoutFrame.setLayout(playbackButtonLayout)

        # Load dir button
        loadDirButton = QtWidgets.QPushButton("Load Directory")
        loadDirButton.clicked.connect(self.openLoadDir)
        fileButtonLayout.addWidget(loadDirButton)

        # Output GIF button
        self.outputGifButton = QtWidgets.QPushButton("GIF output OFF")
        self.outputGifButton.clicked.connect(self.toggleOutputGif)
        fileButtonLayout.addWidget(self.outputGifButton)

        # Layer selector menu
        self.layerSelector = QtWidgets.QComboBox()
        self.layerSelector.addItems([ "Select Layer..." ])
        self.layerSelector.activated.connect(self.displayLocal)
        viewButtonLayout.addWidget(self.layerSelector)

        # Automatically convert selected data layer to mesh height
        self.scalarHeightButton = QtWidgets.QPushButton("Height map OFF")
        self.scalarHeightButton.clicked.connect(self.toggleValToHeights)
        viewButtonLayout.addWidget(self.scalarHeightButton)

        # Play button
        self.playButton = QtWidgets.QPushButton("Play")
        self.playButton.clicked.connect(self.playPause)
        playbackButtonLayout.addWidget(self.playButton)

        # "Playback speed" picker
        self.skipFrames = QtWidgets.QSpinBox()
        self.skipFrames.setMinimum(1)
        self.skipFrames.setMaximum((1 << 31) - 1)
        self.skipFrames.setValue(1)
        skipFramesLabel = QtWidgets.QLabel("Advance frames:")
        skipFramesLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        playbackButtonLayout.addWidget(skipFramesLabel)
        playbackButtonLayout.addWidget(self.skipFrames)

        # Playback FPS picker
        self.FPSPicker = QtWidgets.QSpinBox()
        self.FPSPicker.setMinimum(1)
        self.FPSPicker.setMaximum((1 << 31) - 1)
        self.FPSPicker.setValue(60)
        FPSPickerLabel = QtWidgets.QLabel("FPS:")
        FPSPickerLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        playbackButtonLayout.addWidget(FPSPickerLabel)
        playbackButtonLayout.addWidget(self.FPSPicker)

        # Time slider
        self.frameSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.frameSlider.valueChanged.connect(self.displayLocal)

        # Progress bar
        self.progressBar = QtWidgets.QProgressBar()

        windowLayout.addWidget(fileButtonLayoutFrame)
        windowLayout.addWidget(viewButtonLayoutFrame)
        windowLayout.addWidget(playbackButtonLayoutFrame)
        windowLayout.addWidget(self.frameSlider)
        windowLayout.addWidget(self.plotter.interactor)
        windowLayout.addWidget(self.progressBar)

        self.setCentralWidget(self.frame)

        # Play timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.playFrame)

        if show: self.show()

    def display(self, mesh, text = None):
        if self.outputGif:
            self.bgPlotter.clear()
            if text: self.bgPlotter.add_text(text, render=False)
            self.bgPlotter.add_mesh(mesh, scalars=self.layerSelector.currentText(), render=False)
            self.bgPlotter.write_frame()
        self.plotter.clear()
        if text: self.plotter.add_text(text, render=False)
        self.plotter.add_mesh(mesh, scalars=self.layerSelector.currentText(), render=False)

    def displayLocal(self):
        if not self.meshes: return

        file, mesh = self.meshes[self.frameSlider.value()]
        self.status(f"Viewing {file}")
        self.display(mesh, f"Mesh {file}")

    def openLoadDir(self):
        # Imported meshes don't have height info by default
        if self.v2h: self.toggleValToHeights()
        # Call Qt open dir dialog
        dialog = QtWidgets.QFileDialog(self, "Open Directory")
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if not dialog.exec(): return
        # Only load the first selected entry
        # TODO: Support loading multiple dirs
        directory = dialog.selectedFiles()[0]

        # Update window title
        self.setWindowTitle(f"{self._titleBase}: {directory}")

        # Load meshes from directory
        self.meshes = []
        # Get mesh files list & sort it
        # TODO: Verify that directory contains VTU's and filter out other files
        self.meshfiles = sorted(os.listdir(directory), key = lambda e: float(os.path.splitext(e)[0]))
        for idx, file in enumerate(self.meshfiles):
            # Save both filename and loaded mesh
            self.meshes.append((file, pv.read(os.path.join(directory, file))))
            self.status(f"Loading {file}...")
            self.progress(int(100 * (idx + 1) / len(self.meshfiles)))

        # Retrieve the layers from the first mesh
        # (all the meshes from the same calculation share the same layers) 
        self.layerSelector.clear()
        _, demomesh = self.meshes[0]
        for layer in demomesh.cell_data:
            self.layerSelector.addItem(layer)

        # Reset the slider range and position
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

    def playFrame(self):
        self.displayLocal()
        nextVal = self.frameSlider.value() + self.skipFrames.value()
        if nextVal >= len(self.meshes):
            nextVal = 0
        self.frameSlider.setValue(nextVal)

    def playPause(self, startFrame = -1):
        self.playing = not self.playing
        if self.playing:
            self.timer.start(int(1000.0 / self.FPSPicker.value()))
            if startFrame != -1:
                self.frameSlider.setValue(startFrame)

            self.playButton.setText("Stop")
        else:
            self.timer.stop()
            self.playButton.setText("Play")

    def toggleOutputGif(self):
        self.outputGif = not self.outputGif
        if self.outputGif:
            name, ext = QtWidgets.QFileDialog.getSaveFileName(self, "Save GIF", "", ".gif")
            gifname = name + ext
            if not name: gifname = "svt.gif"
            self.bgPlotter.open_gif(gifname)
            self.outputGifButton.setText("GIF output ON")
        else:
            self.outputGifButton.setText("GIF output OFF")
            self.bgPlotter.close()
            self.bgPlotter = pv.Plotter(notebook=False, off_screen=True)

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

        self.status("Done!")
        self.displayLocal()

# MAIN
def main():
    qtApp = QtWidgets.QApplication([])
    window = SVTAppWindow()
    qtApp.exec()

if __name__ == "__main__":
    main()
