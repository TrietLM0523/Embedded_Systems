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
        """Xử lý frame dữ liệu từ Pico và giải nén bits"""
        try:
            # Format frame: [num_channels (1 byte)] [packed_data...] 
            if len(frame) < 1:
                return
            
            num_channels = frame[0]
            data = []
            
            # Tính số byte dữ liệu cần thiết (bit-packed)
            num_bytes = (num_channels + 7) // 8
            
            if len(frame) < 1 + num_bytes:
                # Không đủ dữ liệu cho số kênh khai báo
                return
                
            # Giải nén từng bit thành một giá trị trong list data
            for byte_idx in range(num_bytes):
                byte_val = frame[1 + byte_idx]
                for bit_idx in range(8):
                    channel_idx = byte_idx * 8 + bit_idx
                    if channel_idx < num_channels:
                        bit_val = (byte_val >> bit_idx) & 0x01
                        data.append(bit_val)
            
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
        self.num_channels = 8
    
    def connect(self) -> bool:
        """Mock connection"""
        self.is_connected = True
        self.stop_event.clear()
        
        # Không start thread ở đây nữa, start ở start_capture
        print("Connected to MOCK Pico")
        return True
    
    def disconnect(self):
        """Mock disconnect"""
        self.stop_event.set()
        self.is_connected = False
        if self.mock_thread:
            self.mock_thread.join(timeout=2)
            self.mock_thread = None
            
    def start_capture(self, num_channels: int):
        """Bắt đầu mock capture"""
        self.num_channels = num_channels
        self.stop_event.clear()
        
        if not self.mock_thread or not self.mock_thread.is_alive():
            self.mock_thread = threading.Thread(target=self._mock_data_thread, daemon=True)
            self.mock_thread.start()
        
        print(f"Mock capture started with {num_channels} channels")
    
    def stop_capture(self):
        """Dừng mock capture"""
        self.stop_event.set()
        if self.mock_thread:
            self.mock_thread.join(timeout=2)
            self.mock_thread = None
        print("Mock capture stopped")

    def _mock_data_thread(self):
        """Sinh dữ liệu giả (UART, I2C, SPI) để test"""
        import time
        from protocol_simulator import MockProtocolStream
        
        stream = MockProtocolStream()
        
        while not self.stop_event.is_set():
            time.sleep(0.01)  # 100 Hz sampling
            
            data = stream.get_next_sample(self.num_channels)
            
            if self.on_data_received:
                self.on_data_received(data)
