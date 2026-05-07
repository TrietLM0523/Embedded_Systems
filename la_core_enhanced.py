from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from typing import List, Tuple, Dict
import time
from dataclasses import dataclass

@dataclass
class TriggerConfig:
    enabled: bool = False
    channel: int = 0
    edge: str = "RISING"  # RISING, FALLING, BOTH

class LACore:
    """Core logic xử lý dữ liệu Logic Analyzer"""
    
    def __init__(self, num_channels=8, buffer_size=10000, sample_rate=1000000):
        self.num_channels = num_channels
        self.buffer_size = buffer_size
        self.sample_rate = sample_rate
        
        # Buffer dữ liệu: mỗi kênh là một numpy array
        self.data_buffers = [np.zeros(buffer_size, dtype=np.uint8) for _ in range(num_channels)]
        self.timestamps = np.zeros(buffer_size, dtype=np.float64)
        
        self.buffer_ptr = 0
        self.total_samples = 0
        self.is_running = False
        
        self.trigger = TriggerConfig()
        self.trigger_fired = False
        
        self.channel_names = [f"CH{i}" for i in range(num_channels)]
        
    def reset(self):
        self.buffer_ptr = 0
        self.total_samples = 0
        self.trigger_fired = False
        for i in range(self.num_channels):
            self.data_buffers[i].fill(0)
        self.timestamps.fill(0)
        
    def set_trigger(self, enabled: bool, channel: int = 0, edge: str = "RISING"):
        self.trigger = TriggerConfig(enabled, channel, edge)
        self.trigger_fired = not enabled  # Nếu không dùng trigger thì coi như đã fired
        
    def add_samples(self, channel_data: List[int]):
        """
        Thêm một sample từ tất cả kênh
        channel_data: list gồm num_channels giá trị (0 hoặc 1)
        """
        if len(channel_data) < self.num_channels:
            # Pad with 0s if data is incomplete
            channel_data = list(channel_data) + [0] * (self.num_channels - len(channel_data))
            
        # Kiểm tra trigger
        if self.trigger.enabled and not self.trigger_fired:
            prev_val = self.data_buffers[self.trigger.channel][(self.buffer_ptr - 1) % self.buffer_size]
            curr_val = channel_data[self.trigger.channel]
            
            fired = False
            if self.trigger.edge == "RISING" and prev_val == 0 and curr_val == 1:
                fired = True
            elif self.trigger.edge == "FALLING" and prev_val == 1 and curr_val == 0:
                fired = True
            elif self.trigger.edge == "BOTH" and prev_val != curr_val:
                fired = True
                
            if fired:
                self.trigger_fired = True
                print(f"Trigger fired on CH{self.trigger.channel}")
            else:
                return # Chờ trigger
        
        # Lưu dữ liệu vào vòng lặp buffer (hoặc linear buffer ở đây đang làm đơn giản)
        idx = self.buffer_ptr
        for i in range(self.num_channels):
            self.data_buffers[i][idx] = channel_data[i]
            
        self.timestamps[idx] = self.total_samples / self.sample_rate
        
        self.buffer_ptr = (self.buffer_ptr + 1) % self.buffer_size
        self.total_samples += 1
        
    def get_channel_data(self, channel: int, num_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """Lấy dữ liệu để hiển thị"""
        if channel >= self.num_channels:
            return np.array([]), np.array([])
            
        if self.total_samples < self.buffer_size:
            # Buffer chưa đầy
            times = self.timestamps[:self.buffer_ptr]
            values = self.data_buffers[channel][:self.buffer_ptr]
        else:
            # Buffer đầy, lấy theo thứ tự
            times = np.concatenate([self.timestamps[self.buffer_ptr:], self.timestamps[:self.buffer_ptr]])
            values = np.concatenate([self.data_buffers[channel][self.buffer_ptr:], self.data_buffers[channel][:self.buffer_ptr]])
            
        # Chỉ lấy num_samples cuối
        return times[-num_samples:], values[-num_samples:]

    def export_csv(self, filename: str):
        import csv
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ["Timestamp"] + self.channel_names
            writer.writerow(header)
            
            # Export all collected data
            count = min(self.total_samples, self.buffer_size)
            if self.total_samples < self.buffer_size:
                for i in range(count):
                    row = [self.timestamps[i]] + [self.data_buffers[ch][i] for ch in range(self.num_channels)]
                    writer.writerow(row)
            else:
                for i in range(self.buffer_size):
                    idx = (self.buffer_ptr + i) % self.buffer_size
                    row = [self.timestamps[idx]] + [self.data_buffers[ch][idx] for ch in range(self.num_channels)]
                    writer.writerow(row)

    def export_json(self, filename: str):
        import json
        data = {
            "sample_rate": self.sample_rate,
            "num_channels": self.num_channels,
            "channels": {}
        }
        for i in range(self.num_channels):
            _, v = self.get_channel_data(i, self.buffer_size)
            data["channels"][self.channel_names[i]] = v.tolist()
            
        with open(filename, 'w') as f:
            json.dump(data, f)

class LACanvas(QtWidgets.QWidget):
    """Widget hiển thị dạng sóng logic"""
    
    signal_data_updated = QtCore.pyqtSignal()
    
    def __init__(self, la_core: LACore, parent=None):
        super().__init__(parent)
        self.la_core = la_core
        self.setup_ui()
        
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_plot)
        
        self.num_displayed_channels = la_core.num_channels  # Hiển thị tất cả các kênh mặc định
        self.curves = []
        self.setup_plots()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.plot_widget = pg.PlotWidget(title="Logic Channels")
        self.plot_widget.setBackground('k')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        layout.addWidget(self.plot_widget)
        
    def setup_plots(self):
        self.plot_widget.clear()
        self.curves = []
        
        colors = ['y', 'g', 'c', 'm', 'r', 'w', 'b', 'orange']
        
        for i in range(self.num_displayed_channels):
            color = colors[i % len(colors)]
            # Tạo offset cho mỗi kênh để không bị đè lên nhau
            # Mỗi kênh hiển thị trong khoảng 0-1, offset theo i
            curve = self.plot_widget.plot(
                pen=pg.mkPen(color=color, width=2),
                name=self.la_core.channel_names[i]
            )
            self.curves.append(curve)
        
        self.plot_widget.addLegend()
        
    def set_displayed_channels(self, num: int):
        self.num_displayed_channels = min(num, self.la_core.num_channels)
        self.setup_plots()
        
    def start_update(self, interval_ms: int = 100):
        """Bắt đầu cập nhật plot"""
        self.update_timer.start(interval_ms)
        
    def stop_update(self):
        """Dừng cập nhật plot"""
        self.update_timer.stop()
        
    def update_plot(self):
        """Cập nhật dữ liệu lên plot"""
        if not self.la_core or self.la_core.total_samples == 0:
            return
            
        for i in range(len(self.curves)):
            times, values = self.la_core.get_channel_data(i, 1000)
            if len(times) > 0:
                # Thêm offset để tách các kênh: CH0 ở trên, CH1 ở dưới...
                # CH0: +3, CH1: +2, CH2: +1, CH3: 0
                offset = (self.num_displayed_channels - 1 - i) * 1.5
                self.curves[i].setData(times, values.astype(float) + offset)
        
        self.signal_data_updated.emit()
