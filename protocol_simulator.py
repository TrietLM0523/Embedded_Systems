"""
Protocol simulator for generating mock UART, I2C, and SPI signals.
"""
from typing import List

class ProtocolGenerator:
    def __init__(self, sample_rate: int = 100):
        self.sample_rate = sample_rate
        self.counter = 0

    def generate_uart(self, message: str, baudrate: int = 10) -> List[int]:
        """
        Generates UART signal. 10 samples per bit for better stability.
        """
        samples_per_bit = 10
        bits = [1] * 20 # Initial idle
        for char in message:
            byte_val = ord(char)
            # Start bit (0)
            bits.extend([0] * samples_per_bit)
            # Data bits (LSB first)
            for i in range(8):
                bit = (byte_val >> i) & 1
                bits.extend([bit] * samples_per_bit)
            # Stop bit (1)
            bits.extend([1] * samples_per_bit)
            # Idle
            bits.extend([1] * (samples_per_bit * 2))
        return bits

    def generate_i2c(self, address: int, data: bytes) -> List[List[int]]:
        """
        Generates I2C signals. 4 samples per clock phase.
        """
        scl = []
        sda = []
        sp = 4 # samples per phase
        
        # Start Condition
        scl.extend([1] * (sp*2))
        sda.extend([1] * sp + [0] * sp)
        
        def write_byte(byte):
            for i in range(7, -1, -1):
                bit = (byte >> i) & 1
                # Clock low, set data
                scl.extend([0] * sp); sda.extend([bit] * sp)
                # Clock high, data stable
                scl.extend([1] * sp); sda.extend([bit] * sp)
            # ACK bit (0)
            scl.extend([0] * sp); sda.extend([0] * sp)
            scl.extend([1] * sp); sda.extend([0] * sp)

        # Address + Write (0)
        write_byte((address << 1) | 0)
        
        # Data bytes
        for b in data:
            write_byte(b)
            
        # Stop Condition
        scl.extend([0] * sp + [1] * sp)
        sda.extend([0] * (sp*2))
        scl.extend([1] * sp)
        sda.extend([0] * sp + [1] * sp)
        
        return [scl, sda]

    def generate_spi(self, data: bytes) -> List[List[int]]:
        """
        Generates SPI signals. 4 samples per clock phase.
        """
        cs = []
        sck = []
        mosi = []
        sp = 4
        
        # CS active
        cs.extend([1] * sp); sck.extend([0] * sp); mosi.extend([0] * sp)
        cs.extend([0] * sp); sck.extend([0] * sp); mosi.extend([0] * sp)
        
        for byte in data:
            for i in range(7, -1, -1):
                bit = (byte >> i) & 1
                # SCK low, MOSI set
                cs.extend([0] * sp); sck.extend([0] * sp); mosi.extend([bit] * sp)
                # SCK high, MOSI stable
                cs.extend([0] * sp); sck.extend([1] * sp); mosi.extend([bit] * sp)
        
        # CS idle
        cs.extend([0] * sp); sck.extend([0] * sp); mosi.extend([0] * sp)
        cs.extend([1] * sp); sck.extend([0] * sp); mosi.extend([0] * sp)
        
        return [cs, sck, mosi]

class MockProtocolStream:
    """
    Manages infinite streaming of protocol data.
    """
    def __init__(self, message_uart="Hello UART", message_i2c=b"Hello I2C", message_spi=b"Hello SPI"):
        gen = ProtocolGenerator()
        self.uart_bits = gen.generate_uart(message_uart)
        self.i2c_bits = gen.generate_i2c(0x50, message_i2c)
        self.spi_bits = gen.generate_spi(message_spi)
        
        # Padding to make them loop somewhat nicely
        max_len = max(len(self.uart_bits), len(self.i2c_bits[0]), len(self.spi_bits[0])) + 50
        
        self.uart_bits += [1] * (max_len - len(self.uart_bits))
        self.i2c_bits[0] += [1] * (max_len - len(self.i2c_bits[0]))
        self.i2c_bits[1] += [1] * (max_len - len(self.i2c_bits[1]))
        self.spi_bits[0] += [1] * (max_len - len(self.spi_bits[0]))
        self.spi_bits[1] += [0] * (max_len - len(self.spi_bits[1]))
        self.spi_bits[2] += [0] * (max_len - len(self.spi_bits[2]))
        
        self.length = max_len
        self.ptr = 0

    def get_next_sample(self, num_channels=8) -> List[int]:
        data = [0] * num_channels
        
        # CH0: UART TX
        data[0] = self.uart_bits[self.ptr]
        
        # CH1, CH2: I2C SCL, SDA
        if num_channels > 2:
            data[1] = self.i2c_bits[0][self.ptr]
            data[2] = self.i2c_bits[1][self.ptr]
            
        # CH3, CH4, CH5: SPI CS, SCK, MOSI
        if num_channels > 5:
            data[3] = self.spi_bits[0][self.ptr]
            data[4] = self.spi_bits[1][self.ptr]
            data[5] = self.spi_bits[2][self.ptr]
            
        # CH6, CH7: Simple patterns
        if num_channels > 6:
            data[6] = 1 if (self.ptr % 10) < 5 else 0
        if num_channels > 7:
            data[7] = 1 if (self.ptr % 4) < 2 else 0
            
        self.ptr = (self.ptr + 1) % self.length
        return data
