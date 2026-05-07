# Yêu cầu Ứng dụng Logic Analyzer GUI

**Phiên bản**: 1.0  
**Ngày**: Tháng 5, 2025  
**Mục đích**: Hiển thị và phân tích dữ liệu từ logic analyzer lõi Raspberry Pi Pico

---

## 1. Chức năng Cốt lõi

### 1.1 Quản lý Kết nối
- **Kết nối/ngắt kết nối** với Pico qua USB Serial
- **Tự động phát hiện** COM ports có sẵn
- **Cấu hình** baud rate (300 → 3M)
- **Chế độ Mock** để test không có hardware
- **Hiển thị trạng thái** kết nối (Connected/Disconnected)

### 1.2 Capture Dữ liệu
- **Hỗ trợ** 1-16 kênh logic
- **Cấu hình sampling rate** từ 1 kHz đến 100+ MHz
- **Ring buffer** để lưu trữ hiệu quả
- **Trigger** trên Rising/Falling/Both edge
- **Start/Stop capture** linh hoạt

### 1.3 Hiển thị Dữ liệu
- **Chế độ Stacked**: Hiển thị từng kênh tách riêng
- **Chế độ Overlay**: Hiển thị tất cả kênh trên 1 biểu đồ
- **Zoom/Pan** trên trục thời gian
- **Thời gian thực** update (configurable)
- **Grid & legend** cho dễ đọc
- **Màu sắc khác nhau** cho từng kênh

### 1.4 Phân tích Tín hiệu
- **Đo tần số** (từ counting transitions)
- **Đo duty cycle** (%)
- **Đo pulse width** (microseconds)
- **Hiển thị thống kê** real-time trong panel

### 1.5 Giải mã Giao thức
- **UART**: Decode RX/TX, hiển thị ký tự hoặc hex
- **I2C**: Detect START/STOP/ACK/NAK
- **SPI**: Decode CLK/MOSI/MISO/CS
- **Cấu hình** protocol settings
- **Hiển thị** events trong table hoặc console

### 1.6 Export & Save
- **Export CSV**: Dữ liệu dạng bảng (Time, CH0, CH1, ...)
- **Export JSON**: Kèm metadata (sample rate, trigger, v.v.)
- **Save workspace**: Lưu setup & dữ liệu để load lại sau
- **Screenshot**: Capture biểu đồ thành PNG/PDF

---

## 2. Giao diện Người dùng

### 2.1 Main Window
```
┌─────────────────────────────────────────────────────────┐
│ Logic Analyzer v1.0                        [_][□][X]    │
├─────────────────────────────────────────────────────────┤
│ [Connect] [Start] [Stop] [Clear] [Export CSV] [Export JSON]│
│ Status: Connected (COM3 @ 115200)                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│              Plot Area (pyqtgraph)                       │
│              CH0: ─────┐     ├─────                      │
│              CH1: ─┐   └──┐  │                           │
│              CH2: ─┴─────┐└──┴──                         │
│              CH3: ───────┘                               │
│                                                           │
├────────────────┬──────────────────────────────────────────┤
│  Settings      │  Statistics                              │
│  ─────────     │  ───────────                             │
│  Sample Rate   │  CH0:                                    │
│  [1000000] Hz  │    Freq: 1234.56 Hz                      │
│                │    Duty: 50.0%                           │
│  Channels: [8] │    Min/Max: 0/1                          │
│                │  CH1:                                    │
│  Trigger:      │    Freq: 567.89 Hz                       │
│  [✓] Enabled   │    ...                                   │
│  Channel: [0]  │                                          │
│  Edge: [Rising]│  Protocol Decode:                        │
│                │  UART RX: 'A' 0x41                       │
│  Protocol:     │  UART TX: 'B' 0x42                       │
│  [UART]        │  ...                                     │
│  Baud: [9600]  │                                          │
└────────────────┴──────────────────────────────────────────┘
```

### 2.2 Dialog Kết nối
```
┌────────────────────────┐
│ Connect to Pico        │
├────────────────────────┤
│ COM Port:              │
│ [COM3         ▼]       │
│                        │
│ Baud Rate:             │
│ [115200       ▼]       │
│                        │
│ [✓] Use Mock Device    │
│                        │
│     [Refresh] [OK]     │
└────────────────────────┘
```

### 2.3 Menu Bar (Optional)
```
File:
  - Open Session
  - Save Session
  - Export CSV
  - Export JSON
  - Export Screenshot
  - Exit

View:
  - Display Mode (Stacked/Overlay)
  - Channel Settings
  - Fullscreen

Tools:
  - Protocol Analyzer
  - Measurements
  - Cursors

Help:
  - About
  - Documentation
```

---

## 3. Yêu cầu Kỹ thuật

### 3.1 Hiệu suất
- **Latency**: < 100ms từ capture đến hiển thị
- **Memory**: < 200 MB cho 10K samples x 16 channels
- **CPU**: < 20% trên i5/Ryzen 5
- **Data rate**: Hỗ trợ USB 2.0 full-speed (12 Mbps)

### 3.2 Tương thích
- **OS**: Windows 7+, Linux (Ubuntu 18.04+), macOS 10.12+
- **Python**: 3.9, 3.10, 3.11, 3.12
- **Qt Version**: PyQt5.15+
- **Architecture**: x86_64, ARM64

### 3.3 Hardware
- **Raspberry Pi Pico**: RP2040 @ 125 MHz
- **USB Cable**: Micro USB (tối thiểu 500mA)
- **COM Port**: Virtual COM port thông qua USB

### 3.4 Thư viện Python
- `PyQt5`: GUI framework
- `pyqtgraph`: Plotting library
- `numpy`: Data processing
- `pyserial`: Serial communication
- `PyInstaller`: Build executable

---

## 4. Data Format

### 4.1 Serial Protocol
```
Frame format (từ Pico):
[num_channels (1B)] [CH0 (1B)] [CH1 (1B)] ... [CHn (1B)] [0xFF]

Ví dụ (8 channels, all low):
0x08 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0xFF

Ví dụ (3 channels, mixed):
0x03 0x01 0x00 0x01 0xFF
```

### 4.2 CSV Export Format
```
Time (s),CH0,CH1,CH2,CH3,CH4,CH5,CH6,CH7
0.0,1,0,1,0,1,0,0,1
0.000001,1,0,1,0,1,0,0,1
0.000002,0,0,1,0,0,0,1,1
```

### 4.3 JSON Export Format
```json
{
  "metadata": {
    "timestamp": "2025-05-06T10:30:45.123456",
    "num_channels": 8,
    "sample_rate": 1000000.0,
    "total_samples": 10000,
    "trigger": "CH0 RISING"
  },
  "channels": {
    "CH0": {
      "timestamps": [0.0, 1e-6, 2e-6, ...],
      "values": [1, 1, 0, ...]
    },
    "CH1": { ... }
  }
}
```

---

## 5. Protocol Decoder Specs

### 5.1 UART
- **Start Bit**: 1 bit (always 0)
- **Data Bits**: 5-9 bits configurable
- **Parity**: None/Odd/Even
- **Stop Bits**: 1-2 bits
- **Display**: ASCII (printable) hoặc Hex
- **Error Detection**: Parity/framing errors

### 5.2 I2C
- **Detect**: START (SDA 1→0 @ SCL=1)
- **Detect**: STOP (SDA 0→1 @ SCL=1)
- **Detect**: ACK/NAK (9th bit)
- **Display**: Address + Data bytes
- **Speed**: Standard/Fast/Fast+

### 5.3 SPI
- **Modes**: CPOL/CPHA (0-3)
- **Detect**: CS active (configurable)
- **Decode**: MOSI/MISO bytes
- **Display**: Hex format
- **LSB/MSB**: Configurable

---

## 6. Yêu cầu Non-Functional

### 6.1 Usability
- Intuitive UI (mỗi hành động ≤ 2 clicks)
- Tooltips & help text
- Keyboard shortcuts (Ctrl+S, Ctrl+E, v.v.)
- Dark mode default (eye-friendly)

### 6.2 Reliability
- Graceful error handling
- Connection recovery
- Data integrity check
- Crash recovery (auto-save)

### 6.3 Documentation
- README file
- Inline code comments
- Example configurations
- Video tutorial (optional)

### 6.4 Testing
- Unit tests cho decoders
- Integration tests cho serial I/O
- GUI automation tests
- Performance benchmarks

---

## 7. Deliverables

### 7.1 Code
- ✅ `main_enhanced.py` - Main GUI application
- ✅ `la_core_enhanced.py` - LA logic & canvas
- ✅ `serial_interface.py` - Serial communication
- ✅ `protocol_decoder.py` - Protocol decoders
- ✅ `requirements.txt` - Dependencies
- ✅ `build_exe.py` - Build script

### 7.2 Documentation
- ✅ `README.md` - User guide & setup
- ✅ `REQUIREMENTS.md` - This file
- ✅ Inline code documentation
- ✅ Example firmware (Pico)

### 7.3 Build Artifacts
- ✅ `dist/LogicAnalyzer.exe` - Standalone executable
- ✅ `dist/` folder - All dependencies

---

## 8. Timeline

| Phase | Deliverable | Deadline |
|-------|-------------|----------|
| Phase 1 | Basic GUI + Serial I/O | Week 1 |
| Phase 2 | Data capture + Display | Week 2 |
| Phase 3 | Protocol decoders | Week 3 |
| Phase 4 | Testing + Optimization | Week 4 |
| Phase 5 | Documentation + Build EXE | Week 5 |
| Phase 6 | Demo + Final testing | Week 6 |

---

## 9. Success Criteria

- ✅ Giao diện đẹp, responsive
- ✅ Kết nối stable với Pico
- ✅ Capture dữ liệu chính xác
- ✅ Hiển thị real-time hoặc offline
- ✅ Export hoạt động đúng
- ✅ Build EXE thành công
- ✅ Documentation đầy đủ
- ✅ Demo demo video chuyên nghiệp

---

**Notes:**
- Nếu Pico không hỗ trợ sample rate cao, focus vào Topic 1
- Có thể mở rộng với FPGA sau (Xilinx/Intel Cyclone)
- Khuyến khích thêm advanced features (measurements, scripting, v.v.)
