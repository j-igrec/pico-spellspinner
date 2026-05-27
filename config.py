# Pin assignments — Waveshare 1.14" LCD on Pico 2 W
LCD_SPI  = 1
LCD_CLK  = 10
LCD_MOSI = 11
LCD_CS   = 9
LCD_DC   = 8
LCD_RST  = 12
LCD_BL   = 13

# I2C for MPU-6050
IMU_I2C  = 0
IMU_SDA  = 4
IMU_SCL  = 5
IMU_ADDR = 0x68

# Buttons + joystick (active-low, pull-up) — Waveshare 1.14" LCD module onboard
BTN_A    = 15
BTN_B    = 17
JOY_UP   = 2
JOY_DOWN = 18
JOY_LEFT = 16
JOY_RIGHT = 20
JOY_CTR  = 3

# Buttons (debounce)
BTN_DEBOUNCE = 200  # ms — minimum interval between button triggers

# Shake detection
SHAKE_THRESHOLD = 2.5   # g — total acceleration magnitude to trigger
SHAKE_DEBOUNCE  = 1000  # ms — minimum interval between triggers
