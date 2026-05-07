import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

class LACanvas(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout(self)
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setYRange(-0.5, 1.5)
        self.plot_widget.setMouseEnabled(x=True, y=False)
        
        self.layout.addWidget(self.plot_widget)
        
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color='g', width=2))
        
        self.buffer_size = 1000
        self.data_buffer = np.zeros(self.buffer_size)
        self.ptr = 0
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)

    def start_sim(self):
        self.timer.start(50)

    def stop_sim(self):
        self.timer.stop()

    def clear_data(self):
        self.data_buffer = np.zeros(self.buffer_size)
        self.curve.setData(self.data_buffer)

    def update_data(self):
        new_sample = 1 if np.sin(self.ptr / 5) > 0 else 0
        
        self.data_buffer[:-1] = self.data_buffer[1:]
        self.data_buffer[-1] = new_sample
        self.ptr += 1
        
        self.curve.setData(self.data_buffer)
