from protocol_simulator import MockProtocolStream
from protocol_decoder import UARTDecoder, I2CDecoder, SPIDecoder
import numpy as np

def test_mock_decoding():
    stream = MockProtocolStream()
    samples = [stream.get_next_sample(8) for _ in range(stream.length)]
    samples = np.array(samples)
    
    timestamps = [i * 0.01 for i in range(len(samples))]
    
    print("--- UART Test ---")
    # Generator uses 10 samples per bit, so sample_rate=100 and baudrate=10 works
    uart_decoder = UARTDecoder(baudrate=10, sample_rate=100) 
    ch0_data = samples[:, 0].tolist()
    events = uart_decoder.decode(ch0_data, [], timestamps)
    for e in events:
        print(f"[{e.timestamp:.2f}] {e.data}")

    print("\n--- I2C Test ---")
    i2c_decoder = I2CDecoder()
    scl = samples[:, 1].tolist()
    sda = samples[:, 2].tolist()
    events = i2c_decoder.decode(sda, scl, timestamps)
    for e in events:
        print(f"[{e.timestamp:.2f}] {e.data}")

    print("\n--- SPI Test ---")
    spi_decoder = SPIDecoder()
    cs = samples[:, 3].tolist()
    sck = samples[:, 4].tolist()
    mosi = samples[:, 5].tolist()
    miso = [0] * len(mosi)
    events = spi_decoder.decode(sck, mosi, miso, cs, timestamps)
    for e in events:
        print(f"[{e.timestamp:.2f}] {e.data}")

if __name__ == "__main__":
    test_mock_decoding()
