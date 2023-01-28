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
        self.transmission = {}
        self.transmission["S.N."] = SENSOR_NO
        self.transmission["Location"] = LOCATION
        self.update_time()

        # WiFi Attirbutes:
        self.station = network.WLAN(network.STA_IF)

        # Component Attributes:
        self.yellow_led = Pin(YELLOW_LED_PIN, Pin.OUT)
        self.blue_led = Pin(BLUE_LED_PIN, Pin.OUT)
        self.green_led = Pin(GREEN_LED_PIN, Pin.OUT)
        self.red_led = Pin(RED_LED_PIN, Pin.OUT)
        self.motion_L = Pin(MOTION_L_PIN, Pin.IN)
        self.motion_R = Pin(MOTION_R_PIN, Pin.IN)


    # Connectibility Functions:

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

    def transmit(self) -> bool:
        """
            Sends the transmission dict to the server.
            Lights green LED and returns True if succeeded,
            Lights red LED and returns False else.
        """

        try:
            post("http://"+SERVER_ADDR, data=str(self.transmission))
        
        except Exception as e:
            print(f"Transmission failed.\n Exception: {e}")
            self.red_led.value(1)
            return False
        
        print(f"Transmission sent at {self.transmission['Date']}, {self.transmission['Time']}")
        self.green_led.value(1)
        return True

    # Data Proccessing Functions:

    def __str__(self) -> str:
        """
            Return value of all attributes of self as a string.
        """

        return  f"\n### Sensor {self.transmission['S.N.']} - Beginning of Report ###\n" + \
                f"Sensor Location: {self.transmission['Location']}\n" + \
                f"Connection Status: {self.station.isconnected()}\n\n" + \
                "Dictionary Values: \n" + "".join([f"{key}: {value}\n" for key, value in zip(self.transmission.keys(), self.transmission.values())]) + \
                "\nComponents Values: \n" + \
                    f"Yellow LED: {self.yellow_led.value()}\n" + \
                    f"Blue LED: {self.blue_led.value()}\n" + \
                    f"Green LED: {self.green_led.value()}\n" + \
                    f"Red LED: {self.red_led.value()}\n" + \
                    f"Motion Sensor (L): {self.motion_L.value()}\n" + \
                    f"Motion Sensor (R): {self.motion_R.value()}\n" + \
                "\n### End of Report ###\n"

    def update_time(self) -> None:
        """
            Update Weekday, date and time in self.transmission.
        """
        
        # Get timestamp:
        t = localtime()
        wday = ""
        if t[6] == 0:
            wday = "Mon"
        elif t[6] == 1:
            wday = "Tue"
        elif t[6] == 2:
            wday = "Wed"
        elif t[6] == 3:
            wday = "Thu"
        elif t[6] == 4:
            wday = "Fri"
        elif t[6] == 5:
            wday = "Sat"
        elif t[6] == 6:
            wday = "Sun"
        dstamp = f"{t[2]:02d}/{t[1]:02d}/{t[0]}"
        tstamp = f"{t[3]:02d}:{t[4]:02d}"
        wday = "Sun" # debugging only
        tstamp = "8:"+tstamp.split(":")[1] # debugging only
        self.transmission["Weekday"] = wday
        self.transmission["Date"] = dstamp
        self.transmission["Time"] = tstamp

if __name__ == '__main__':
    sensor = Sensor()
    sensor.connect()
    print(sensor)
    sleep(3)
    sensor.disconnect()
