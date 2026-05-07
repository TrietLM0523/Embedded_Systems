"""
Logic Analyzer GUI Application - Main Entry Point (PyQt5 Version)
"""
import sys
import os
import json
from PyQt5 import QtWidgets, QtCore, QtGui
from la_core_enhanced import LACore, LACanvas
from serial_interface import PicoSerialInterface, MockPicoInterface
from protocol_decoder import UARTDecoder, I2CDecoder, SPIDecoder, SignalAnalyzer
import serial.tools.list_ports
from typing import Optional
from datetime import datetime

class ConnectionDialog(QtWidgets.QDialog):
    """Dialog để chọn COM port"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to Pico")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        
        # COM port selection
        layout.addWidget(QtWidgets.QLabel("COM Port:"))
        self.combo_port = QtWidgets.QComboBox()
        self.refresh_ports()
        layout.addWidget(self.combo_port)
        
        # Baud rate selection
        layout.addWidget(QtWidgets.QLabel("Baud Rate:"))
        self.combo_baud = QtWidgets.QComboBox()
        self.combo_baud.addItems(["115200", "230400", "460800", "921600"])
        self.combo_baud.setCurrentText("115200")
        layout.addWidget(self.combo_baud)
        
        # Use mock
        self.check_mock = QtWidgets.QCheckBox("Use Mock Device (for testing)")
        self.check_mock.setChecked(True) # Default to mock
        layout.addWidget(self.check_mock)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_refresh = QtWidgets.QPushButton("Refresh Ports")
        btn_refresh.clicked.connect(self.refresh_ports)
        btn_layout.addWidget(btn_refresh)
        
        btn_ok = QtWidgets.QPushButton("Connect")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def refresh_ports(self):
        """Refresh danh sách COM ports"""
        self.combo_port.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.combo_port.addItem(port.device)
        
        if self.combo_port.count() == 0:
            self.combo_port.addItem("(No COM ports found)")
    
    def get_port(self) -> Optional[str]:
        return self.combo_port.currentText()
    
    def get_baudrate(self) -> int:
        try:
            return int(self.combo_baud.currentText())
        except ValueError:
            return 115200
    
    def use_mock(self) -> bool:
        return self.check_mock.isChecked()


class SettingsPanel(QtWidgets.QDockWidget):
    """Panel cấu hình các tham số"""
    
    signal_sample_rate_changed = QtCore.pyqtSignal(float)
    signal_num_channels_changed = QtCore.pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__("Settings", parent)
        self.setup_ui()
    
    def setup_ui(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        
        # Sample rate
        layout.addWidget(QtWidgets.QLabel("Sample Rate (Hz):"))
        self.spin_sample_rate = QtWidgets.QSpinBox()
        self.spin_sample_rate.setRange(1000, 100_000_000)
        self.spin_sample_rate.setValue(1_000_000)
        self.spin_sample_rate.setSuffix(" Hz")
        self.spin_sample_rate.valueChanged.connect(
            lambda v: self.signal_sample_rate_changed.emit(float(v))
        )
        layout.addWidget(self.spin_sample_rate)
        
        # Number of channels
        layout.addWidget(QtWidgets.QLabel("Number of Channels:"))
        self.spin_num_channels = QtWidgets.QSpinBox()
        self.spin_num_channels.setRange(1, 16)
        self.spin_num_channels.setValue(8)
        self.spin_num_channels.valueChanged.connect(
            lambda v: self.signal_num_channels_changed.emit(v)
        )
        layout.addWidget(self.spin_num_channels)
        
        # Trigger settings
        layout.addSpacing(10)
        layout.addWidget(QtWidgets.QLabel("=== Trigger ==="))
        
        self.check_trigger_enable = QtWidgets.QCheckBox("Enable Trigger")
        layout.addWidget(self.check_trigger_enable)
        
        layout.addWidget(QtWidgets.QLabel("Trigger Channel:"))
        self.spin_trigger_channel = QtWidgets.QSpinBox()
        self.spin_trigger_channel.setRange(0, 15)
        layout.addWidget(self.spin_trigger_channel)
        
        layout.addWidget(QtWidgets.QLabel("Trigger Edge:"))
        self.combo_trigger_edge = QtWidgets.QComboBox()
        self.combo_trigger_edge.addItems(["RISING", "FALLING", "BOTH"])
        layout.addWidget(self.combo_trigger_edge)
        
        # Protocol decoding
        layout.addSpacing(10)
        layout.addWidget(QtWidgets.QLabel("=== Protocol Decode ==="))
        
        layout.addWidget(QtWidgets.QLabel("Protocol:"))
        self.combo_protocol = QtWidgets.QComboBox()
        self.combo_protocol.addItems(["None", "UART", "I2C", "SPI"])
        layout.addWidget(self.combo_protocol)
        
        layout.addWidget(QtWidgets.QLabel("UART Baudrate:"))
        self.spin_uart_baud = QtWidgets.QSpinBox()
        self.spin_uart_baud.setRange(300, 3_000_000)
        self.spin_uart_baud.setValue(9600)
        layout.addWidget(self.spin_uart_baud)
        
        layout.addStretch()
        widget.setLayout(layout)
        self.setWidget(widget)


class StatsPanel(QtWidgets.QDockWidget):
    """Panel hiển thị thống kê"""
    
    def __init__(self, parent=None):
        super().__init__("Statistics", parent)
        self.setup_ui()
    
    def setup_ui(self):
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        
        self.stats_widget = QtWidgets.QWidget()
        self.stats_layout = QtWidgets.QVBoxLayout(self.stats_widget)
        self.scroll.setWidget(self.stats_widget)
        
        self.setWidget(self.scroll)
        self.update_stats({})
    
    def update_stats(self, stats_dict):
        """Cập nhật hiển thị thống kê"""
        # Clear old
        while self.stats_layout.count() > 0:
            item = self.stats_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        if not stats_dict:
            self.stats_layout.addWidget(QtWidgets.QLabel("No data"))
            return
        
        for ch_name, ch_stats in stats_dict.items():
            label = QtWidgets.QLabel(f"<b>{ch_name}</b>")
            self.stats_layout.addWidget(label)
            
            for stat_name, stat_value in ch_stats.items():
                info = QtWidgets.QLabel(f"  {stat_name}: {stat_value}")
                self.stats_layout.addWidget(info)
            
            self.stats_layout.addSpacing(5)
        
        self.stats_layout.addStretch()


class LogicAnalyzerApp(QtWidgets.QMainWindow):
    """Ứng dụng Logic Analyzer chính"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logic Analyzer GUI v1.0")
        self.setMinimumSize(1200, 700)
        
        # State
        self.la_core: Optional[LACore] = None
        self.la_canvas: Optional[LACanvas] = None
        self.pico_interface: Optional[PicoSerialInterface] = None
        self.is_capturing = False
        
        self.setup_ui()
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready. Connect a device to start.")
    
    def setup_ui(self):
        """Setup UI chính"""
        # Central widget
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        
        central_layout = QtWidgets.QVBoxLayout()
        
        # Toolbar
        toolbar = QtWidgets.QHBoxLayout()
        
        self.btn_connect = QtWidgets.QPushButton("Connect")
        self.btn_connect.clicked.connect(self.show_connection_dialog)
        toolbar.addWidget(self.btn_connect)
        
        self.btn_start = QtWidgets.QPushButton("Start Capture")
        self.btn_start.clicked.connect(self.start_capture)
        self.btn_start.setEnabled(False)
        toolbar.addWidget(self.btn_start)
        
        self.btn_stop = QtWidgets.QPushButton("Stop Capture")
        self.btn_stop.clicked.connect(self.stop_capture)
        self.btn_stop.setEnabled(False)
        toolbar.addWidget(self.btn_stop)
        
        self.btn_clear = QtWidgets.QPushButton("Clear Data")
        self.btn_clear.clicked.connect(self.clear_data)
        self.btn_clear.setEnabled(False)
        toolbar.addWidget(self.btn_clear)
        
        toolbar.addSpacing(20)
        
        self.label_status = QtWidgets.QLabel("Status: Disconnected")
        self.label_status.setStyleSheet("color: red; font-weight: bold;")
        toolbar.addWidget(self.label_status)
        
        toolbar.addStretch()
        
        self.btn_export = QtWidgets.QPushButton("Export CSV")
        self.btn_export.clicked.connect(self.export_csv)
        self.btn_export.setEnabled(False)
        toolbar.addWidget(self.btn_export)
        
        self.btn_export_json = QtWidgets.QPushButton("Export JSON")
        self.btn_export_json.clicked.connect(self.export_json)
        self.btn_export_json.setEnabled(False)
        toolbar.addWidget(self.btn_export_json)
        
        central_layout.addLayout(toolbar)
        
        # Main Canvas Area
        self.canvas_container = QtWidgets.QFrame()
        self.canvas_container.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.canvas_layout = QtWidgets.QVBoxLayout(self.canvas_container)
        
        welcome_label = QtWidgets.QLabel("Not connected.\nClick 'Connect' and select a device to start.")
        welcome_label.setAlignment(QtCore.Qt.AlignCenter)
        self.canvas_layout.addWidget(welcome_label)
        
        central_layout.addWidget(self.canvas_container)
        
        self.central_widget.setLayout(central_layout)
        
        # Dock widgets
        self.settings_panel = SettingsPanel()
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.settings_panel)
        
        self.stats_panel = StatsPanel()
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.stats_panel)
        
        # Update timer cho stats
        self.stats_timer = QtCore.QTimer()
        self.stats_timer.timeout.connect(self.update_stats_callback)
        self.stats_timer.start(500)
    
    def show_connection_dialog(self):
        """Hiển thị dialog kết nối"""
        dialog = ConnectionDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            if dialog.use_mock():
                self.connect_mock()
            else:
                port = dialog.get_port()
                baudrate = dialog.get_baudrate()
                if port and "No COM" not in port:
                    self.connect_pico(port, baudrate)
                else:
                    QtWidgets.QMessageBox.warning(self, "Warning", "No serial port selected.")
    
    def connect_mock(self):
        """Kết nối với thiết bị mock"""
        self.pico_interface = MockPicoInterface()
        
        if self.pico_interface.connect():
            self.initialize_la()
            self.label_status.setText("Status: Connected (MOCK)")
            self.label_status.setStyleSheet("color: orange; font-weight: bold;")
            self.btn_start.setEnabled(True)
            self.btn_clear.setEnabled(True)
            self.btn_export.setEnabled(True)
            self.btn_export_json.setEnabled(True)
    
    def connect_pico(self, port: str, baudrate: int):
        """Kết nối với Raspberry Pi Pico"""
        try:
            self.pico_interface = PicoSerialInterface(port, baudrate)
            
            if self.pico_interface.connect():
                self.initialize_la()
                self.label_status.setText(f"Status: Connected ({port})")
                self.label_status.setStyleSheet("color: green; font-weight: bold;")
                self.btn_start.setEnabled(True)
                self.btn_clear.setEnabled(True)
                self.btn_export.setEnabled(True)
                self.btn_export_json.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "Connection Error", f"Failed to connect to {port}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Connection Error", str(e))
    
    def initialize_la(self):
        """Khởi tạo Logic Analyzer"""
        num_channels = self.settings_panel.spin_num_channels.value()
        sample_rate = self.settings_panel.spin_sample_rate.value()
        
        self.la_core = LACore(
            num_channels=num_channels,
            buffer_size=10000,
            sample_rate=sample_rate
        )
        
        # Setup callbacks
        self.pico_interface.on_data_received = self.on_data_received
        self.pico_interface.on_error = self.on_error
        
        # Clear existing canvas
        while self.canvas_layout.count():
            item = self.canvas_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Create new canvas
        self.la_canvas = LACanvas(self.la_core)
        self.canvas_layout.addWidget(self.la_canvas)
        
        # Connect settings signals
        self.settings_panel.signal_num_channels_changed.connect(
            self.on_num_channels_changed
        )
    
    def on_data_received(self, channel_data: list):
        """Callback khi nhận dữ liệu từ Pico"""
        if self.la_core:
            self.la_core.add_samples(channel_data)
    
    def on_error(self, error_msg: str):
        """Callback khi có lỗi"""
        print(f"Error: {error_msg}")
        self.status_bar.showMessage(f"Error: {error_msg}")
    
    def start_capture(self):
        """Bắt đầu capture"""
        if self.pico_interface and self.la_core:
            self.is_capturing = True
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            
            # Setup trigger
            if self.settings_panel.check_trigger_enable.isChecked():
                ch = self.settings_panel.spin_trigger_channel.value()
                edge = self.settings_panel.combo_trigger_edge.currentText()
                self.la_core.set_trigger(True, ch, edge)
            else:
                self.la_core.set_trigger(False)
            
            # Start canvas update
            self.la_canvas.start_update(100)
            
            # Send command to Pico
            self.pico_interface.start_capture(self.la_core.num_channels)
            self.status_bar.showMessage("Capturing...")
    
    def stop_capture(self):
        """Dừng capture"""
        if self.pico_interface and self.la_canvas:
            self.is_capturing = False
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            
            self.la_canvas.stop_update()
            self.pico_interface.stop_capture()
            self.status_bar.showMessage("Stopped.")
    
    def clear_data(self):
        """Xóa dữ liệu"""
        if self.la_core:
            self.la_core.reset()
            if self.la_canvas:
                self.la_canvas.update_plot()
    
    def update_stats_callback(self):
        """Cập nhật thống kê"""
        if not self.la_core:
            return
        
        stats = {}
        analyzer = SignalAnalyzer()
        
        for ch in range(min(4, self.la_core.num_channels)):  # Show first 4 channels
            _, values = self.la_core.get_channel_data(ch, 1000)
            
            if len(values) > 0:
                freq = analyzer.measure_frequency(values.tolist(), self.la_core.sample_rate)
                duty = analyzer.measure_duty_cycle(values.tolist())
                
                stats[self.la_core.channel_names[ch]] = {
                    "Freq": f"{freq:.2f} Hz",
                    "Duty": f"{duty:.1f}%",
                    "Samples": len(values)
                }
        
        self.stats_panel.update_stats(stats)
    
    def on_num_channels_changed(self, num_channels: int):
        """Xử lý thay đổi số kênh"""
        if self.la_canvas:
            self.la_canvas.set_displayed_channels(num_channels)
    
    def export_csv(self):
        """Export dữ liệu ra CSV"""
        if not self.la_core:
            return
        
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV Files (*.csv)"
        )
        
        if filename:
            self.la_core.export_csv(filename)
            QtWidgets.QMessageBox.information(self, "Success", f"Data exported to {filename}")
    
    def export_json(self):
        """Export dữ liệu ra JSON"""
        if not self.la_core:
            return
        
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export JSON", "", "JSON Files (*.json)"
        )
        
        if filename:
            self.la_core.export_json(filename)
            QtWidgets.QMessageBox.information(self, "Success", f"Data exported to {filename}")
    
    def closeEvent(self, event):
        """Xử lý đóng ứng dụng"""
        if self.pico_interface:
            self.pico_interface.stop_capture()
        event.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = LogicAnalyzerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
