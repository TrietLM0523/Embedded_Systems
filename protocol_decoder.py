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
    
    def __init__(self, baudrate: int = 9600, sample_rate: float = 100):
        self.baudrate = baudrate
        self.sample_rate = sample_rate
        self.samples_per_bit = sample_rate / baudrate
        self.data_bits = 8
    
    def decode(self, tx_data: List[int], rx_data: List[int], timestamps: List[float]) -> List[ProtocolEvent]:
        events = []
        if tx_data:
            events.extend(self._decode_line(tx_data, timestamps, 'TX'))
        if rx_data:
            events.extend(self._decode_line(rx_data, timestamps, 'RX'))
        return sorted(events, key=lambda e: e.timestamp)
    
    def _decode_line(self, line: List[int], timestamps: List[float], label: str) -> List[ProtocolEvent]:
        events = []
        i = 0
        while i < len(line) - 1:
            # Tìm start bit (1 -> 0)
            if line[i] == 1 and line[i + 1] == 0:
                start_idx = i + 1
                byte_data = 0
                bit_samples = self.samples_per_bit
                
                success = True
                for bit_idx in range(8):
                    # Lấy mẫu ở giữa bit dữ liệu thứ bit_idx
                    # Start bit kéo dài 1 bit_samples. Bit 0 bắt đầu từ start_idx + bit_samples.
                    # Điểm giữa của bit_idx là: start_idx + (bit_idx + 1.5) * bit_samples
                    sample_pos = int(start_idx + (bit_idx + 1.5) * bit_samples)
                    if sample_pos < len(line):
                        bit_val = line[sample_pos]
                        byte_data |= (bit_val << bit_idx)
                    else:
                        success = False
                        break
                
                if success:
                    char = chr(byte_data) if 32 <= byte_data < 127 else f"\\x{byte_data:02X}"
                    events.append(ProtocolEvent(
                        timestamp=timestamps[start_idx],
                        protocol="UART",
                        data=f"{label}: {char}",
                        details={"byte": byte_data, "line": label}
                    ))
                    i = int(start_idx + bit_samples * 10) 
                    continue
            i += 1
        return events


class I2CDecoder:
    """Giải mã I2C từ 2 kênh SDA/SCL"""
    
    def decode(self, sda: List[int], scl: List[int], timestamps: List[float]) -> List[ProtocolEvent]:
        events = []
        i = 1
        
        while i < len(scl) - 1:
            # START condition: SDA 1->0 khi SCL 1
            if scl[i] == 1 and sda[i-1] == 1 and sda[i] == 0:
                events.append(ProtocolEvent(timestamps[i], "I2C", "START"))
                
                idx = i + 1
                while idx < len(scl) - 1:
                    # Đọc 8 bit dữ liệu
                    byte_val = 0
                    bits_read = 0
                    
                    while bits_read < 8 and idx < len(scl):
                        # Cạnh lên của SCL: mẫu dữ liệu
                        if scl[idx-1] == 0 and scl[idx] == 1:
                            byte_val = (byte_val << 1) | sda[idx]
                            bits_read += 1
                        
                        # Kiểm tra STOP trong khi đang chờ clock (không chuẩn nhưng hay gặp)
                        if scl[idx] == 1 and sda[idx-1] == 0 and sda[idx] == 1:
                             events.append(ProtocolEvent(timestamps[idx], "I2C", "STOP"))
                             i = idx
                             return events # Kết thúc transaction
                        
                        idx += 1
                    
                    if bits_read == 8:
                        # Đọc bit ACK/NACK (cạnh lên tiếp theo của SCL)
                        # Trước tiên phải vượt qua cạnh lên cũ nếu có
                        idx += 1
                        while idx < len(scl) and not (scl[idx-1] == 0 and scl[idx] == 1):
                            idx += 1
                        
                        if idx < len(sda):
                            ack = "ACK" if sda[idx] == 0 else "NACK"
                            char = chr(byte_val) if 32 <= byte_val < 127 else f"0x{byte_val:02X}"
                            events.append(ProtocolEvent(timestamps[idx], "I2C", f"DATA: {char} ({ack})"))
                        
                        # Quan trọng: Vượt qua cạnh ACK để không bị nhầm là bit đầu của byte sau
                        idx += 1
                        
                    # Sau ACK, kiểm tra xem có STOP không trước khi sang byte tiếp theo
                    # STOP: SDA 0->1 khi SCL 1
                    found_stop = False
                    stop_check_limit = idx + 20 # Kiểm tra một khoảng ngắn sau ACK
                    t_idx = idx + 1
                    while t_idx < len(scl) and t_idx < stop_check_limit:
                        if scl[t_idx] == 1 and sda[t_idx-1] == 0 and sda[t_idx] == 1:
                            events.append(ProtocolEvent(timestamps[t_idx], "I2C", "STOP"))
                            idx = t_idx
                            found_stop = True
                            break
                        # Nếu thấy SCL xuống thấp, nghĩa là đang có byte tiếp theo
                        if scl[t_idx] == 0:
                            break
                        t_idx += 1
                    
                    if found_stop:
                        break
                i = idx
            i += 1
        return events


class SPIDecoder:
    """Giải mã SPI từ 3+ kênh CLK/MOSI/MISO/CS"""
    
    def decode(self, clk: List[int], mosi: List[int], miso: List[int], 
               cs: List[int], timestamps: List[float]) -> List[ProtocolEvent]:
        events = []
        in_transaction = False
        byte_mosi = 0
        bit_count = 0
        
        for i in range(1, len(clk)):
            # CS Falling (Active)
            if cs[i-1] == 1 and cs[i] == 0:
                in_transaction = True
                byte_mosi = 0
                bit_count = 0
                events.append(ProtocolEvent(timestamps[i], "SPI", "CS ACTIVE"))
            
            # CS Rising (Idle)
            elif cs[i-1] == 0 and cs[i] == 1:
                in_transaction = False
                events.append(ProtocolEvent(timestamps[i], "SPI", "CS IDLE"))
            
            if in_transaction:
                # Rising edge of Clock
                if clk[i-1] == 0 and clk[i] == 1:
                    byte_mosi = (byte_mosi << 1) | mosi[i]
                    bit_count += 1
                    
                    if bit_count == 8:
                        char = chr(byte_mosi) if 32 <= byte_mosi < 127 else f"0x{byte_mosi:02X}"
                        events.append(ProtocolEvent(timestamps[i], "SPI", f"MOSI: {char}"))
                        byte_mosi = 0
                        bit_count = 0
        
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
