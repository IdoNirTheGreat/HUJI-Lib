import network
from urequests import post
from time import sleep, localtime, time
from machine import Pin
import _thread as thread

# Network Constants:
SERVER_ADDR = "127.0.0.1"
PORT = 80
WLAN_SSID = "MWTSOA"
WLAN_PW = "zmora6599"

# Sensor Constants:
SENSOR_NO = 1
LOCATION = "Harman Science Library - Floor 2 (Quiet)"
TRNSMT_INTERVAL = 30 # In seconds
LAN_TIMEOUT = 15 # In seconds
MOTION_ON = 0
MOTION_OFF = 1
MOTION_TIMEOUT = 1 # The timout duration to cancel an entrance or exit if only one sensor was activated.

# Component Constants:
YELLOW_LED_PIN = 23 # Yellow: Lights if successfully connected to LAN, blinks if trying to connect, off if isn't connected.
BLUE_LED_PIN = 22 # Blue: Activated when detected motion.
GREEN_LED_PIN = 21 # Green: Successfully connected to server.
RED_LED_PIN = 19 # Red: Failed connecting to server.
MOTION_L_PIN = 13 # Left motion sensor's pin.
MOTION_R_PIN = 12 # Right motion sensor's pin.

class Sensor:
    def __init__(self):
        """
            The HUJI-Lib sensor object which houses all possible
            functions for the sensor to do.
        """
        # Data Attributes:
        self.serial_num = SENSOR_NO
        self.location = LOCATION

        # WiFi Attirbutes:
        self.station = network.WLAN(network.STA_IF)

        # Component Attributes:
        self.yellow_led = Pin(YELLOW_LED_PIN, Pin.OUT)
        self.blue_led = Pin(BLUE_LED_PIN, Pin.OUT)
        self.green_led = Pin(GREEN_LED_PIN, Pin.OUT)
        self.red_led = Pin(RED_LED_PIN, Pin.OUT)
        self.motion_L = Pin(MOTION_L_PIN, Pin.IN)
        self.motion_R = Pin(MOTION_R_PIN, Pin.IN)

    def connect(self) -> bool:
        """
            Connect to WiFi network. Blinks yellow LED while 
            attempting to connect, solid yellow when connected,
            red LED if connection attempt failed.
            Returns True if attempt was successful, False other.
        """
        # Set station as active:
        try:
            self.station.active(True)
        except Exception as e:
            print(  f"WiFi station could not be activated.\n"
                    "Exception: {e}")
            return False

        # Connect to LAN:
        self.station.connect(WLAN_SSID, WLAN_PW)
        start = time()
        while not self.station.isconnected() and not time()-start > LAN_TIMEOUT:
            if self.yellow_led():
                self.yellow_led.value(0)
            else:
                self.yellow_led.value(1)
            print(f"\r({time()-start}s) Connecting{((time()-start) % 4) * '.'}   ", end='')
            sleep(.25)

        # Connection attempt passed timeout:
        if time()-start > LAN_TIMEOUT:
            self.station.active(False)
            print("Could not connect to WiFi.")
            self.yellow_led.value(0)
            self.red_led.value(1)
            print(f"LAN_TIMEOUT_EXCEPTION ({LAN_TIMEOUT}s)")
            return False
        
        # Connection attempt was successful:
        else:
            print("\nConnected to WiFi.")
            if not self.yellow_led.value():
                self.yellow_led.value(1)
        
        return True

    def disconnect(self) -> bool:
        """
            Disconnects from WLAN and deactivates WiFi station.
            Turns yellow LED off if succeeded, turns red LED 
            on if an error occurred.
        """

        try:
            self.station.disconnect()
            self.station.active(False)
            print("Connection to WLAN was terminated.")
            return True

        except Exception as e:
            print(  f"The sensor could not disconnect from WLAN.\n"
                    "Exception: {e}")
            return False

if __name__ == '__main__':
    sensor = Sensor()
    sensor.connect()
    sleep(3)
    sensor.disconnect()
