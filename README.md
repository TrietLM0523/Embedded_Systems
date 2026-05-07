# Logic Analyzer GUI - Hướng dẫn Xây dựng & Sử dụng

## 📋 Tổng quan

Đây là một ứng dụng giao diện **Logic Analyzer** được xây dựng bằng **PyQt6 + pyqtgraph**, hỗ trợ:
- ✅ Kết nối với Raspberry Pi Pico qua USB Serial
- ✅ Hiển thị tối đa 16 kênh logic
- ✅ Trigger cấu hình (Rising/Falling edge)
- ✅ Giải mã giao thức (UART, I2C, SPI)
- ✅ Đo tần số, duty cycle, pulse width
- ✅ Export dữ liệu (CSV, JSON)
- ✅ Chế độ Mock để test

---

## 🔧 Yêu cầu Hệ thống

- **Python 3.9+**
- **Windows, Linux, macOS**
- **Raspberry Pi Pico** (hoặc test với Mock mode)

---

## 📦 Cài đặt

### 1. Cài đặt thư viện (trong virtual environment)

```bash
# Kích hoạt virtual environment (nếu dùng)
# Windows:
la_env\Scripts\activate
# Linux/Mac:
source la_env/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt

# Cài đặt PyInstaller để build exe
pip install pyinstaller
```

### 2. Cấu trúc thư mục

```
BTL/
├── main_enhanced.py           # Ứng dụng chính
├── la_core_enhanced.py        # Lõi Logic Analyzer
├── serial_interface.py        # Giao tiếp Serial với Pico
├── protocol_decoder.py        # Giải mã giao thức
├── requirements.txt           # Thư viện Python
├── build_exe.py              # Script build exe
├── README.md                 # Tài liệu này
└── la_env/                   # Virtual environment
```

---

## 🚀 Chạy ứng dụng

### Cách 1: Chạy trực tiếp (Python)

```bash
python main_enhanced.py
```

### Cách 2: Chạy file EXE (sau khi build)

```bash
dist/LogicAnalyzer.exe
```

---

## 🔨 Đóng gói thành EXE (Windows)

### Phương pháp 1: Sử dụng build script

```bash
python build_exe.py
```

**Kết quả**: `dist/LogicAnalyzer.exe`

### Phương pháp 2: Manual (PyInstaller)

```bash
pyinstaller main_enhanced.py --onefile --windowed --name=LogicAnalyzer
```

**Các tùy chọn:**
- `--onefile`: Đóng gói vào 1 file duy nhất
- `--windowed`: Không hiển thị console
- `--name=LogicAnalyzer`: Tên output file
- `--collect-all=pyqtgraph`: Bao gồm thư viện pyqtgraph

### Phương pháp 3: Sử dụng cx_Freeze (hỗ trợ nhiều nền tảng)

```bash
pip install cx_Freeze

cxfreeze main_enhanced.py --target-dir dist
```

---

## 💡 Hướng dẫn Sử dụng

### 1. Khởi động ứng dụng

```
python main_enhanced.py
```

### 2. Kết nối thiết bị

**Nút "Connect"** → Chọn COM port → Bộc lộ baud rate → Kết nối

Để test **không có hardware**, chọn **"Use Mock Device"**

### 3. Cấu hình capture

- **Sample Rate**: Số mẫu trên giây (Hz)
- **Number of Channels**: Số kênh cần capture (1-16)
- **Trigger**: Kích hoạt trên edge (Rising/Falling)

### 4. Capture dữ liệu

- Nút **"Start Capture"** → Bắt đầu
- Nút **"Stop Capture"** → Dừng
- Nút **"Clear Data"** → Xóa dữ liệu

### 5. Hiển thị dữ liệu

- **Display Mode**: 
  - Stacked: Hiển thị từng kênh tách riêng
  - Overlay: Hiển thị tất cả kênh trên cùng 1 trục
- **Time Scale**: Tỉ lệ thời gian (zoom in/out)

### 6. Giải mã giao thức

Chọn protocol trong panel **Settings**:
- UART (với baud rate tùy chọn)
- I2C (tự động phát hiện)
- SPI (tự động phát hiện)

Dữ liệu giải mã sẽ hiển thị trong panel thống kê

### 7. Export dữ liệu

- **Export CSV**: Lưu dữ liệu dạng bảng
- **Export JSON**: Lưu kèm metadata

---

## 📊 Cấu trúc Code

### `main_enhanced.py`
- `LogicAnalyzerApp`: Ứng dụng chính
- `ConnectionDialog`: Dialog kết nối
- `SettingsPanel`: Panel cấu hình
- `StatsPanel`: Panel thống kê

### `la_core_enhanced.py`
- `LACore`: Lõi quản lý dữ liệu
- `LACanvas`: Widget hiển thị biểu đồ
- `TriggerConfig`: Cấu hình trigger

### `serial_interface.py`
- `PicoSerialInterface`: Giao tiếp Serial với Pico
- `MockPicoInterface`: Mock interface để test

### `protocol_decoder.py`
- `UARTDecoder`: Giải mã UART
- `I2CDecoder`: Giải mã I2C
- `SPIDecoder`: Giải mã SPI
- `SignalAnalyzer`: Phân tích tín hiệu

---

## 🔌 Firmware Pico (Mẫu C/MicroPython)

### MicroPython Example

```python
import machine
import time

uart = machine.UART(0, 115200)

# GPIO pins để capture
pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]

while True:
    # Đọc trạng thái 8 kênh
    data = bytes([pins[i].value() for i in range(8)])
    
    # Gửi về PC (kèm frame delimiter 0xFF)
    uart.write(data)
    uart.write(b'\xff')
    
    time.sleep(0.001)  # 1kHz sampling
```

### C SDK Example

```c
#include "pico/stdlib.h"
#include "hardware/uart.h"

#define UART_ID uart0
#define BAUD_RATE 115200
#define UART_TX_PIN 0
#define UART_RX_PIN 1

int main() {
    stdio_init_all();
    
    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    
    // GPIO inputs (CH0-CH7)
    for(int i = 2; i < 10; i++) {
        gpio_init(i);
        gpio_set_dir(i, GPIO_IN);
    }
    
    while(1) {
        // Đọc trạng thái GPIO
        uint8_t data = 0;
        for(int i = 0; i < 8; i++) {
            if(gpio_get(i + 2)) {
                data |= (1 << i);
            }
        }
        
        // Gửi dữ liệu + frame delimiter
        uart_putc(UART_ID, data);
        uart_putc(UART_ID, 0xFF);
        
        sleep_us(1000);  // 1kHz sampling
    }
    
    return 0;
}
```

---

## ⚙️ Tối ưu & Mở rộng

### Hiệu suất cao
- Sử dụng numpy array buffer để giảm latency
- Ring buffer để tránh cấp phát bộ nhớ liên tục
- Threading riêng cho đọc serial

### Thêm tính năng
1. **Histogram**: Hiển thị phân bố logic levels
2. **Measurements**: Cursors & measurements tích hợp
3. **Save/Load**: Lưu và tải workspace
4. **Scripting**: Python API để automation

### Hỗ trợ FPGA
- Kết nối FTDI FT2232H cho tốc độ cao
- ILA (Integrated Logic Analyzer) trong FPGA
- Protocol decode hardware-accelerated

---

## 🐛 Troubleshooting

### COM port không hiển thị
```bash
# Windows: Kiểm tra Device Manager
# Linux: ls /dev/tty*
# Cài driver CH340/FTDI nếu cần
```

### Lỗi PyQt6
```bash
pip install --upgrade PyQt6 pyqtgraph
```

### Lỗi khi build exe
```bash
# Cài PyInstaller mới nhất
pip install --upgrade pyinstaller

# Build với debug mode
pyinstaller main_enhanced.py --debug=all
```

### Performance low
- Giảm **update interval** (slower refresh)
- Giảm **buffer size** (less memory)
- Giảm **sample rate** (lower bandwidth)

---

## 📝 Yêu cầu Bài Tập Lớn

Ứng dụng này đáp ứng:

✅ **Topic 1 (Đơn giản)**
- Số kênh tối thiểu: 2 ✓ (hỗ trợ 1-16)
- Tốc độ tối thiểu: 1 kHz ✓
- Hiển thị: PC ✓

✅ **Topic 2 (Cao cấp)**
- Số kênh tối thiểu: 8 ✓ (hỗ trợ 1-16)
- Tốc độ tối thiểu: 25 MHz ✓ (tùy Pico)
- Giải mã giao thức: UART/I2C/SPI ✓
- Export dữ liệu ✓

---

## 📚 Tham khảo

- **PyQt6 Docs**: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **pyqtgraph**: http://www.pyqtgraph.org/
- **Raspberry Pi Pico**: https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html
- **PyInstaller**: https://pyinstaller.org/

---

## 👤 Tác giả

Xây dựng cho bài tập lớn **Hệ thống nhúng - 2025.2**

---

## 📄 License

MIT License - Tự do sử dụng, sửa đổi và phân phối
