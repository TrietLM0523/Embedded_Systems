"""
Serial interface module for Raspberry Pi Pico Logic Analyzer
Handles USB/COM communication and data parsing
"""
import serial
import threading
import queue
from typing import Callable, Optional, List
import struct

class PicoSerialInterface:
    """Interface để giao tiếp với Raspberry Pi Pico qua USB Serial"""
    
    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.is_connected = False
        self.data_queue = queue.Queue()
        self.read_thread = None
        self.stop_event = threading.Event()
        
        # Callback
        self.on_data_received: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
    def connect(self) -> bool:
        """Kết nối đến Pico"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            self.is_connected = True
            self.stop_event.clear()
            
            # Khởi động thread đọc dữ liệu
            self.read_thread = threading.Thread(target=self._read_data_thread, daemon=True)
            self.read_thread.start()
            
            print(f"Connected to {self.port}")
            return True
        except Exception as e:
            if self.on_error:
                self.on_error(f"Connection failed: {str(e)}")
            print(f"Error connecting: {str(e)}")
            return False
    
    def disconnect(self):
        """Ngắt kết nối"""
        if self.is_connected:
            self.stop_event.set()
            self.is_connected = False
            if self.read_thread:
                self.read_thread.join(timeout=2)
            if self.ser:
                self.ser.close()
            print("Disconnected from Pico")
    
    def _read_data_thread(self):
        """Thread để đọc dữ liệu từ cổng serial"""
        buffer = b''
        
        while not self.stop_event.is_set() and self.is_connected:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    chunk = self.ser.read(self.ser.in_waiting)
                    buffer += chunk
                    
                    # Xử lý các frame hoàn chỉnh (ví dụ: 0xFF là frame delimiter)
                    while b'\xff' in buffer:
                        frame_end = buffer.index(b'\xff')
                        frame = buffer[:frame_end]
                        buffer = buffer[frame_end + 1:]
                        
                        if len(frame) > 0:
                            self._process_frame(frame)
            except Exception as e:
                if self.on_error:
                    self.on_error(f"Read error: {str(e)}")
    
    def _process_frame(self, frame: bytes):
        """Xử lý frame dữ liệu từ Pico"""
        try:
            # Format frame: [num_channels (1 byte)] [channel_data...] 
            if len(frame) < 1:
                return
            
            num_channels = frame[0]
            data = []
            
            # Mỗi kênh là 1 byte (0 hoặc 1)
            for i in range(1, min(len(frame), num_channels + 1)):
                data.append(frame[i])
            
            if self.on_data_received:
                self.on_data_received(data)
                
        except Exception as e:
            if self.on_error:
                self.on_error(f"Frame processing error: {str(e)}")
    
    def send_command(self, command: bytes):
        """Gửi lệnh đến Pico"""
        try:
            if self.is_connected and self.ser:
                self.ser.write(command)
        except Exception as e:
            if self.on_error:
                self.on_error(f"Send error: {str(e)}")
    
    def set_sampling_rate(self, rate_hz: int):
        """Thiết lập sampling rate trên Pico (tuỳ firmware)"""
        # Format: CMD (0x01) + rate (4 bytes little-endian)
        cmd = struct.pack('<BI', 0x01, rate_hz)
        self.send_command(cmd)
    
    def start_capture(self, num_channels: int):
        """Bắt đầu capture dữ liệu"""
        # Format: CMD (0x02) + num_channels
        cmd = struct.pack('<BB', 0x02, num_channels)
        self.send_command(cmd)
    
    def stop_capture(self):
        """Dừng capture"""
        cmd = struct.pack('<B', 0x03)
        self.send_command(cmd)


class MockPicoInterface(PicoSerialInterface):
    """Mock interface để test khi không có hardware"""
    
    def __init__(self):
        super().__init__("MOCK", 115200)
        self.mock_thread = None
    
    def connect(self) -> bool:
        """Mock connection"""
        import time
        import random
        
        self.is_connected = True
        self.stop_event.clear()
        
        # Sinh dữ liệu giả
        self.mock_thread = threading.Thread(target=self._mock_data_thread, daemon=True)
        self.mock_thread.start()
        
        print("Connected to MOCK Pico")
        return True
    
    def disconnect(self):
        """Mock disconnect"""
        self.stop_event.set()
        self.is_connected = False
        if self.mock_thread:
            self.mock_thread.join(timeout=2)
    
    def _mock_data_thread(self):
        """Sinh dữ liệu giả để test"""
        import time
        import random
        import numpy as np
        
        counter = 0
        while not self.stop_event.is_set():
            time.sleep(0.01)  # 100 Hz sampling
            
            # Tạo pattern cho 8 kênh
            data = []
            # CH0: Sóng vuông nhanh
            data.append(1 if (counter % 4) < 2 else 0)
            # CH1: Sóng vuông chậm
            data.append(1 if (counter % 10) < 5 else 0)
            # CH2: Random
            data.append(random.randint(0, 1))
            # CH3: Counter bit 0
            data.append(counter % 2)
            # CH4: Counter bit 1
            data.append((counter // 2) % 2)
            # CH5: Counter bit 2
            data.append((counter // 4) % 2)
            # CH6: Một số xung thỉnh thoảng
            data.append(1 if (counter % 50) == 0 else 0)
            # CH7: Luôn 0 hoặc 1 (test tĩnh)
            data.append(0)
            
            if self.on_data_received:
                self.on_data_received(data)
            
            counter += 1
