"""
Protocol decoder module for Logic Analyzer
Supports UART, I2C, SPI decoding
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class EdgeType(Enum):
    RISING = 1
    FALLING = 0
    BOTH = 2

@dataclass
class ProtocolEvent:
    """Sự kiện giải mã từ giao thức"""
    timestamp: float
    protocol: str
    data: str
    details: Dict = None

class UARTDecoder:
    """Giải mã UART từ 2 kênh RX/TX"""
    
    def __init__(self, baudrate: int = 9600, data_bits: int = 8, stop_bits: int = 1):
        self.baudrate = baudrate
        self.bit_duration = 1.0 / baudrate
        self.data_bits = data_bits
        self.stop_bits = stop_bits
        self.events: List[ProtocolEvent] = []
    
    def decode(self, tx_data: List[int], rx_data: List[int], timestamps: List[float]) -> List[ProtocolEvent]:
        """
        Decode UART từ dữ liệu TX/RX
        """
        events = []
        
        # Decode TX line
        if tx_data:
            events.extend(self._decode_line(tx_data, timestamps, 'TX'))
        
        # Decode RX line
        if rx_data:
            events.extend(self._decode_line(rx_data, timestamps, 'RX'))
        
        return sorted(events, key=lambda e: e.timestamp)
    
    def _decode_line(self, line: List[int], timestamps: List[float], label: str) -> List[ProtocolEvent]:
        """Decode một line UART"""
        events = []
        i = 0
        
        while i < len(line) - 1:
            # Tìm start bit (0 -> 1)
            if line[i] == 1 and line[i + 1] == 0:
                # Đây là start bit
                byte_data = 0
                bit_idx = 0
                idx = i + 2
                
                # Đọc data bits
                while bit_idx < self.data_bits and idx < len(line):
                    byte_data |= (line[idx] << bit_idx)
                    bit_idx += 1
                    idx += 1
                
                if bit_idx == self.data_bits:
                    char = chr(byte_data) if 32 <= byte_data < 127 else f"0x{byte_data:02X}"
                    events.append(ProtocolEvent(
                        timestamp=timestamps[i] if i < len(timestamps) else i * self.bit_duration,
                        protocol="UART",
                        data=f"{label}: {char}",
                        details={"byte": byte_data, "line": label}
                    ))
                    i = idx
                    continue
            
            i += 1
        
        return events


class I2CDecoder:
    """Giải mã I2C từ 2 kênh SDA/SCL"""
    
    def decode(self, sda: List[int], scl: List[int], timestamps: List[float]) -> List[ProtocolEvent]:
        """
        Decode I2C từ dữ liệu SDA/SCL
        """
        events = []
        i = 0
        
        while i < len(scl) - 1:
            # Tìm START condition: SDA = 1->0 khi SCL = 1
            if sda[i] == 1 and sda[i + 1] == 0 and scl[i] == 1:
                events.append(ProtocolEvent(
                    timestamp=timestamps[i] if i < len(timestamps) else i * 0.001,
                    protocol="I2C",
                    data="START",
                    details={"type": "START"}
                ))
            
            # Tìm STOP condition: SDA = 0->1 khi SCL = 1
            elif sda[i] == 0 and sda[i + 1] == 1 and scl[i] == 1:
                events.append(ProtocolEvent(
                    timestamp=timestamps[i] if i < len(timestamps) else i * 0.001,
                    protocol="I2C",
                    data="STOP",
                    details={"type": "STOP"}
                ))
            
            i += 1
        
        return events


class SPIDecoder:
    """Giải mã SPI từ 3+ kênh CLK/MOSI/MISO/CS"""
    
    def __init__(self, cpol: int = 0, cpha: int = 0, bits_per_frame: int = 8):
        self.cpol = cpol  # Clock polarity
        self.cpha = cpha  # Clock phase
        self.bits_per_frame = bits_per_frame
    
    def decode(self, clk: List[int], mosi: List[int], miso: List[int], 
               cs: List[int], timestamps: List[float]) -> List[ProtocolEvent]:
        """
        Decode SPI từ dữ liệu CLK/MOSI/MISO/CS
        """
        events = []
        
        # Tìm CS active (thường là 0)
        in_transaction = False
        byte_mosi = 0
        byte_miso = 0
        bit_count = 0
        
        for i in range(1, len(clk)):
            # Detect CS edge
            if cs[i - 1] == 1 and cs[i] == 0:
                in_transaction = True
                byte_mosi = 0
                byte_miso = 0
                bit_count = 0
            elif cs[i - 1] == 0 and cs[i] == 1:
                in_transaction = False
                if bit_count > 0:
                    events.append(ProtocolEvent(
                        timestamp=timestamps[i - 1] if i - 1 < len(timestamps) else i * 0.001,
                        protocol="SPI",
                        data=f"MOSI: 0x{byte_mosi:02X}, MISO: 0x{byte_miso:02X}",
                        details={"mosi": byte_mosi, "miso": byte_miso}
                    ))
            
            # Detect clock edge (tùy CPOL/CPHA)
            if in_transaction:
                if (self.cpha == 0 and clk[i - 1] == 0 and clk[i] == 1) or \
                   (self.cpha == 1 and clk[i - 1] == 1 and clk[i] == 0):
                    byte_mosi = (byte_mosi << 1) | mosi[i]
                    byte_miso = (byte_miso << 1) | miso[i]
                    bit_count += 1
        
        return events


class SignalAnalyzer:
    """Phân tích tín hiệu: tần số, duty cycle, v.v."""
    
    @staticmethod
    def measure_frequency(data: List[int], sample_rate: float) -> float:
        """Đo tần số của tín hiệu"""
        if len(data) < 2:
            return 0
        
        # Đếm số lần thay đổi từ 0->1
        transitions = 0
        for i in range(1, len(data)):
            if data[i - 1] == 0 and data[i] == 1:
                transitions += 1
        
        # Tần số = transitions * sample_rate / (2 * length)
        duration = len(data) / sample_rate
        freq = transitions / duration if duration > 0 else 0
        
        return freq
    
    @staticmethod
    def measure_duty_cycle(data: List[int]) -> float:
        """Đo duty cycle (%)"""
        if len(data) == 0:
            return 0
        
        high_count = sum(data)
        duty = (high_count / len(data)) * 100
        
        return duty
    
    @staticmethod
    def measure_pulse_width(data: List[int], sample_rate: float) -> Tuple[float, float]:
        """Đo chiều rộng pulse (microseconds)"""
        pulse_widths = []
        
        in_pulse = False
        pulse_start = 0
        
        for i, val in enumerate(data):
            if val == 1 and not in_pulse:
                in_pulse = True
                pulse_start = i
            elif val == 0 and in_pulse:
                in_pulse = False
                width = (i - pulse_start) / sample_rate * 1e6  # Convert to microseconds
                pulse_widths.append(width)
        
        if len(pulse_widths) == 0:
            return 0, 0
        
        avg_width = sum(pulse_widths) / len(pulse_widths)
        min_width = min(pulse_widths)
        max_width = max(pulse_widths)
        
        return (avg_width, max_width)
