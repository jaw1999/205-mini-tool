# analysis_tools/constellation_viewer.py
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import numpy as np

class ConstellationViewer(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.plot_widget = pg.PlotWidget(title="Constellation Diagram")
        self.plot_widget.setLabel('left', 'In-Phase')
        self.plot_widget.setLabel('bottom', 'Quadrature')
        layout.addWidget(self.plot_widget)

        self.scatter = pg.ScatterPlotItem()
        self.plot_widget.addItem(self.scatter)

    def update_constellation(self, data):
        self.scatter.setData(x=data.real, y=data.imag)
