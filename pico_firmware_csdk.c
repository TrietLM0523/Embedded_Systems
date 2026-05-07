/*
 * Raspberry Pi Pico Logic Analyzer - C SDK Version
 * 
 * Features:
 * - 8 GPIO input channels
 * - Configurable sample rate (up to ~10 MHz)
 * - UART/USB serial transmission
 * - Command interface
 * 
 * GPIO Mapping:
 * CH0 = GPIO2
 * CH1 = GPIO3
 * ...
 * CH7 = GPIO9
 * 
 * UART0:
 * TX = GPIO0
 * RX = GPIO1
 * Baud = 115200
 */

#include "pico/stdlib.h"
#include "pico/binary_info.h"
#include "hardware/uart.h"
#include "hardware/timer.h"
#include "hardware/gpio.h"

// Configuration
#define UART_ID uart0
#define BAUD_RATE 115200
#define UART_TX_PIN 0
#define UART_RX_PIN 1

#define NUM_CHANNELS 8
#define CH_START_GPIO 2
#define SAMPLE_RATE_HZ 1000

#define FRAME_DELIMITER 0xFF
#define CMD_SET_RATE 0x01
#define CMD_START 0x02
#define CMD_STOP 0x03
#define CMD_STATUS 0x04

// Global state
volatile bool capturing = false;
volatile uint32_t sample_rate = SAMPLE_RATE_HZ;
volatile uint32_t sample_count = 0;

/**
 * Initialize UART for communication
 */
void init_uart(void) {
    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    
    // No flow control
    uart_set_hw_flow(UART_ID, false, false);
    uart_set_fifo_enabled(UART_ID, true);
}

/**
 * Initialize GPIO inputs for channels
 */
void init_gpio_inputs(void) {
    for (int i = 0; i < NUM_CHANNELS; i++) {
        int pin = CH_START_GPIO + i;
        gpio_init(pin);
        gpio_set_dir(pin, GPIO_IN);
        gpio_disable_pulls(pin);
    }
}

/**
 * Read all 8 channels and return as single byte
 * Bit 0 = CH0, Bit 1 = CH1, ..., Bit 7 = CH7
 */
static inline uint8_t read_channels(void) {
    uint8_t data = 0;
    
    for (int i = 0; i < NUM_CHANNELS; i++) {
        int pin = CH_START_GPIO + i;
        if (gpio_get(pin)) {
            data |= (1 << i);
        }
    }
    
    return data;
}

/**
 * Send one frame over UART
 * Format: [num_channels] [channel_data] [delimiter]
 */
void send_frame(uint8_t channel_data) {
    uart_putc(UART_ID, NUM_CHANNELS);
    uart_putc(UART_ID, channel_data);
    uart_putc(UART_ID, FRAME_DELIMITER);
}

/**
 * Process incoming commands from PC
 */
void process_command(void) {
    if (!uart_is_readable(UART_ID)) {
        return;
    }
    
    uint8_t cmd = uart_getc(UART_ID);
    
    switch (cmd) {
        case CMD_START:
            capturing = true;
            sample_count = 0;
            printf("Capture started\n");
            break;
        
        case CMD_STOP:
            capturing = false;
            printf("Capture stopped (%lu samples)\n", sample_count);
            break;
        
        case CMD_STATUS:
            if (capturing) {
                uart_puts(UART_ID, "RUNNING\r\n");
            } else {
                uart_puts(UART_ID, "IDLE\r\n");
            }
            break;
        
        case CMD_SET_RATE:
            if (uart_is_readable_within_us(UART_ID, 1000)) {
                uint32_t rate = 0;
                for (int i = 0; i < 4; i++) {
                    rate |= ((uint32_t)uart_getc(UART_ID)) << (i * 8);
                }
                sample_rate = rate;
                printf("Sample rate set to %lu Hz\n", sample_rate);
            }
            break;
        
        default:
            break;
    }
}

/**
 * Main capture loop
 * Uses timer for accurate sampling
 */
void capture_loop(void) {
    uint64_t last_sample_time = 0;
    uint64_t sample_interval_us = 1_000_000 / sample_rate;
    
    printf("Starting capture at %lu Hz (%llu us per sample)\n", 
           sample_rate, sample_interval_us);
    
    while (capturing) {
        uint64_t now = time_us_64();
        
        // Check if it's time for next sample
        if (now - last_sample_time >= sample_interval_us) {
            last_sample_time = now;
            
            // Read channels
            uint8_t channel_data = read_channels();
            
            // Send frame
            send_frame(channel_data);
            
            sample_count++;
        }
        
        // Process incoming commands
        process_command();
    }
    
    printf("Capture complete (%lu samples)\n", sample_count);
}

/**
 * Continuous capture mode
 * Sends data as fast as possible
 */
void continuous_capture(void) {
    printf("Starting continuous capture\n");
    
    while (capturing) {
        // Read channels
        uint8_t channel_data = read_channels();
        
        // Send frame
        send_frame(channel_data);
        
        sample_count++;
        
        // Check for stop command
        process_command();
    }
    
    printf("Continuous capture stopped (%lu samples)\n", sample_count);
}

/**
 * Test GPIO connections
 */
void test_gpio(void) {
    printf("\nTesting GPIO connections...\n");
    printf("Connect test signals to CH0-CH7\n\n");
    
    for (int i = 0; i < 10; i++) {
        printf("CH: ");
        for (int ch = 0; ch < NUM_CHANNELS; ch++) {
            int pin = CH_START_GPIO + ch;
            printf("%d ", gpio_get(pin));
        }
        printf("\n");
        sleep_ms(200);
    }
    printf("\n");
}

/**
 * Print main menu
 */
void print_menu(void) {
    printf("\n");
    printf("╔════════════════════════════════════════╗\n");
    printf("║  Pico Logic Analyzer - Command Menu    ║\n");
    printf("╚════════════════════════════════════════╝\n");
    printf("  'c' - Capture fixed 1000 samples\n");
    printf("  'x' - Continuous capture (send Ctrl+C to stop)\n");
    printf("  't' - Test GPIO connections\n");
    printf("  '1'-'5' - Capture N*1000 samples\n");
    printf("  'q' - Quit\n");
    printf("  'h' - Show this menu\n");
    printf("\nReady for PC GUI connection...\n");
    printf("Or send command (single char): ");
}

/**
 * Main entry point
 */
int main(void) {
    // Initialize UART for logging
    stdio_init_all();
    
    // Initialize UART for data transmission
    init_uart();
    
    // Initialize GPIO inputs
    init_gpio_inputs();
    
    // Print welcome
    printf("\n");
    printf("╔════════════════════════════════════════╗\n");
    printf("║  Raspberry Pi Pico Logic Analyzer      ║\n");
    printf("║  Firmware v1.0 (C SDK)                 ║\n");
    printf("╚════════════════════════════════════════╝\n");
    printf("\nSample Rate: %lu Hz\n", SAMPLE_RATE_HZ);
    printf("Channels: %d\n", NUM_CHANNELS);
    printf("GPIO CH0-CH7 mapped to GPIO%d-GPIO%d\n", 
           CH_START_GPIO, CH_START_GPIO + NUM_CHANNELS - 1);
    printf("UART: TX=GPIO%d, RX=GPIO%d, Baud=%d\n",
           UART_TX_PIN, UART_RX_PIN, BAUD_RATE);
    
    print_menu();
    
    // Main command loop
    while (1) {
        if (uart_is_readable(UART_ID)) {
            char cmd = uart_getc(UART_ID);
            printf("%c\n", cmd);
            
            switch (cmd) {
                case 'c':
                    // Capture fixed samples
                    capturing = true;
                    sample_count = 0;
                    printf("Capturing 1000 samples...\n");
                    while (capturing && sample_count < 1000) {
                        uint8_t data = read_channels();
                        send_frame(data);
                        sample_count++;
                        sleep_us(1000);  // 1ms delay
                    }
                    capturing = false;
                    printf("Done.\n");
                    break;
                
                case 'x':
                    // Continuous capture
                    capturing = true;
                    continuous_capture();
                    break;
                
                case 't':
                    // Test GPIO
                    test_gpio();
                    break;
                
                case '1':
                case '2':
                case '3':
                case '4':
                case '5':
                    // Capture N*1000 samples
                    capturing = true;
                    sample_count = 0;
                    int num = (cmd - '0') * 1000;
                    printf("Capturing %d samples...\n", num);
                    while (capturing && sample_count < num) {
                        uint8_t data = read_channels();
                        send_frame(data);
                        sample_count++;
                        sleep_us(1000);
                    }
                    capturing = false;
                    printf("Done.\n");
                    break;
                
                case 'q':
                    printf("Goodbye!\n");
                    return 0;
                
                case 'h':
                    print_menu();
                    break;
                
                default:
                    printf("Unknown command. Type 'h' for help.\n");
                    break;
            }
            
            printf("Ready: ");
        }
        
        sleep_ms(10);
    }
    
    return 0;
}

/*
 * Build instructions (CMakeLists.txt integration):
 * 
 * add_executable(pico_logic_analyzer
 *     pico_logic_analyzer.c
 * )
 * 
 * target_link_libraries(pico_logic_analyzer
 *     pico_stdlib
 *     hardware_uart
 *     hardware_timer
 * )
 * 
 * pico_add_extra_outputs(pico_logic_analyzer)
 * 
 * Build:
 * mkdir build
 * cd build
 * cmake ..
 * make pico_logic_analyzer
 * 
 * Then flash .uf2 file to Pico
 */
