import sys
from PyQt5 import QtWidgets
from la_core import LACanvas

class LogicAnalyzerApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logic Analyzer")
        self.resize(1000, 500)
        
        self.main_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QtWidgets.QHBoxLayout(self.main_widget)
        
        self.control_panel = QtWidgets.QVBoxLayout()
        
        self.btn_run = QtWidgets.QPushButton("Run")
        self.btn_stop = QtWidgets.QPushButton("Stop")
        self.btn_clear = QtWidgets.QPushButton("Clear")
        
        self.control_panel.addWidget(self.btn_run)
        self.control_panel.addWidget(self.btn_stop)
        self.control_panel.addWidget(self.btn_clear)
        self.control_panel.addStretch()
        
        self.la_view = LACanvas()
        
        self.main_layout.addLayout(self.control_panel, 1)
        self.main_layout.addWidget(self.la_view, 9)
        
        self.btn_run.clicked.connect(self.la_view.start_sim)
        self.btn_stop.clicked.connect(self.la_view.stop_sim)
        self.btn_clear.clicked.connect(self.la_view.clear_data)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = LogicAnalyzerApp()
    window.show()
    sys.exit(app.exec_())
