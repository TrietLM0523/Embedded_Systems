"""
Raspberry Pi Pico Firmware - MicroPython Version
Logic Analyzer Data Capture & Transmission

Features:
- Capture 8 GPIO channels
- 1 kHz sampling rate (adjustable)
- Send data via UART/USB
- Simple command interface
"""

import machine
import time
import struct
from micropython import const

# Constants
NUM_CHANNELS = const(8)
SAMPLE_RATE_HZ = const(1000)
SAMPLE_PERIOD_US = const(1_000_000 // SAMPLE_RATE_HZ)

# GPIO input pins (CH0-CH7)
GPIO_PINS = list(range(2, 2 + NUM_CHANNELS))

# UART configuration (USB CDC or UART0)
uart = machine.UART(0, 115200)

# Frame delimiter
FRAME_DELIMITER = const(0xFF)

# Command codes
CMD_SET_SAMPLE_RATE = const(0x01)
CMD_START_CAPTURE = const(0x02)
CMD_STOP_CAPTURE = const(0x03)
CMD_GET_STATUS = const(0x04)

class LogicAnalyzer:
    """Simple Logic Analyzer for Raspberry Pi Pico"""
    
    def __init__(self, num_channels=NUM_CHANNELS, sample_rate_hz=SAMPLE_RATE_HZ):
        self.num_channels = num_channels
        self.sample_rate_hz = sample_rate_hz
        self.sample_period_us = 1_000_000 // sample_rate_hz
        self.is_running = False
        
        # Initialize GPIO inputs
        self.pins = []
        for i in range(num_channels):
            pin = machine.Pin(GPIO_PINS[i], machine.Pin.IN)
            self.pins.append(pin)
            print(f"CH{i} -> GPIO{GPIO_PINS[i]}")
        
        print(f"LogicAnalyzer initialized:")
        print(f"  Channels: {num_channels}")
        print(f"  Sample Rate: {sample_rate_hz} Hz")
        print(f"  Sample Period: {self.sample_period_us} us")
    
    def read_channels(self):
        """Read all channels and return as list"""
        data = []
        for pin in self.pins:
            data.append(pin.value())
        return data
    
    def capture_samples(self, num_samples=10000):
        """
        Capture N samples and send over UART
        Format: [num_channels] [CH0] [CH1] ... [CHn] [0xFF]
        """
        print(f"Starting capture: {num_samples} samples...")
        self.is_running = True
        
        try:
            for sample in range(num_samples):
                # Read all channels
                channel_data = self.read_channels()
                
                # Build frame: [num_channels] [data...] [delimiter]
                frame = bytes([self.num_channels]) + bytes(channel_data)
                
                # Send frame
                uart.write(frame)
                uart.write(bytes([FRAME_DELIMITER]))
                
                # Wait for next sample
                time.sleep_us(self.sample_period_us)
                
                # Check for stop command
                if uart.any():
                    cmd = uart.read(1)
                    if cmd and cmd[0] == CMD_STOP_CAPTURE:
                        print("Capture stopped by command")
                        break
        
        finally:
            self.is_running = False
            print(f"Capture complete")
    
    def continuous_capture(self):
        """Continuous capture until stopped"""
        print("Starting continuous capture...")
        self.is_running = True
        sample_count = 0
        
        try:
            while self.is_running:
                # Read all channels
                channel_data = self.read_channels()
                
                # Build frame
                frame = bytes([self.num_channels]) + bytes(channel_data)
                
                # Send frame
                uart.write(frame)
                uart.write(bytes([FRAME_DELIMITER]))
                
                sample_count += 1
                
                # Check for commands
                if uart.any():
                    cmd_byte = uart.read(1)
                    if cmd_byte:
                        self.process_command(cmd_byte[0])
                
                # Wait for next sample
                time.sleep_us(self.sample_period_us)
        
        finally:
            self.is_running = False
            print(f"Continuous capture stopped ({sample_count} samples)")
    
    def process_command(self, cmd):
        """Process command from PC"""
        if cmd == CMD_SET_SAMPLE_RATE:
            # Read 4-byte sample rate (little-endian)
            if uart.any() >= 4:
                rate_bytes = uart.read(4)
                self.sample_rate_hz = struct.unpack('<I', rate_bytes)[0]
                self.sample_period_us = 1_000_000 // self.sample_rate_hz
                print(f"Sample rate set to {self.sample_rate_hz} Hz")
        
        elif cmd == CMD_START_CAPTURE:
            if not self.is_running:
                self.continuous_capture()
        
        elif cmd == CMD_STOP_CAPTURE:
            self.is_running = False
            print("Stop command received")
        
        elif cmd == CMD_GET_STATUS:
            status = b'OK' if not self.is_running else b'RUN'
            uart.write(status)
            uart.write(b'\r\n')
    
    def command_interface(self):
        """Simple command interface"""
        print("Command Interface Ready")
        print("Commands:")
        print("  'c' - Capture 1000 samples")
        print("  'x' - Continuous capture (press Ctrl+C to stop)")
        print("  'q' - Quit")
        
        while True:
            if uart.any():
                cmd = uart.read(1).decode().lower()
                
                if cmd == 'c':
                    self.capture_samples(1000)
                
                elif cmd == 'x':
                    self.continuous_capture()
                
                elif cmd == 'q':
                    print("Goodbye!")
                    break
                
                elif cmd in ['1', '2', '3', '4']:
                    # Quick capture
                    num = int(cmd) * 1000
                    self.capture_samples(num)
                
                time.sleep_ms(10)

def test_gpio():
    """Test GPIO connections"""
    print("\nTesting GPIO connections...")
    print("Connect test signals to CH0-CH7")
    
    pins = [machine.Pin(GPIO_PINS[i], machine.Pin.IN) for i in range(NUM_CHANNELS)]
    
    for _ in range(10):
        values = [pin.value() for pin in pins]
        print(f"CH: {values}")
        time.sleep(0.1)

def main():
    """Main entry point"""
    print("\n" + "="*50)
    print("  Raspberry Pi Pico Logic Analyzer")
    print("  Firmware v1.0")
    print("="*50)
    
    # Create analyzer
    la = LogicAnalyzer(NUM_CHANNELS, SAMPLE_RATE_HZ)
    
    print("\nStarting continuous capture...")
    print("Connect GUI application and click 'Connect'")
    
    try:
        la.continuous_capture()
    
    except KeyboardInterrupt:
        print("\nShutdown by user")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        print("Pico ready for next run")

if __name__ == "__main__":
    main()
