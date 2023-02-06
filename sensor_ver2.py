import network
from urequests import post
from time import sleep, localtime, time
from machine import Pin
import _thread as thread

# Network Constants:
SERVER_ADDR = "192.168.1.218"
PORT = 80
WLAN_SSID = "Nir"
WLAN_PW = "Thenirs013"

# Operation Constants:
SENSOR_NO = 1
LOCATION = "Harman Science Library - Floor 2 (Quiet)"
TRNSMT_INTERVAL = 10 # In seconds
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

class ThreadSafeQueue:
    def __init__(self) -> None:
        self._queue = []
        self._lock = thread.allocate_lock()

    def push(self, value):
        self._lock.acquire()
        self._queue.append(value)
        self._lock.release()

    def try_pop(self):
        self._lock.acquire()
        value = self._queue.pop() if len(self._queue) else None
        self._lock.release()
        return value

class NetworkWorker:
    def __init__(self, queue: ThreadSafeQueue) -> None:
        """
        HUJI-Lib network sender, sends updates from the
        sender to the server.
        """
        # Data Attributes:
        self.transmission = {}
        self.transmission["S.N."] = SENSOR_NO
        self.transmission["Location"] = LOCATION
        self.transmission["Entrances"] = 0
        self.transmission["Exits"] = 0
        self.update_time()

        # System Attirbutes:
        self.station = network.WLAN(network.STA_IF)
        self.queue = queue

        # Component Attributes:
        self.yellow_led = Pin(YELLOW_LED_PIN, Pin.OUT)
        self.green_led = Pin(GREEN_LED_PIN, Pin.OUT)
        self.red_led = Pin(RED_LED_PIN, Pin.OUT)

    def run(self) -> None:
        print("HUJI-Lib Sensor has started running...")
        if not self.station.isconnected():
            self.connect()

        while True:
            sleep(TRNSMT_INTERVAL)
            value = self.queue.try_pop()
            if not value:
                continue
            print('popped')
            entrances, exits = value
            self.transmission["Entrances"] = entrances
            self.transmission["Exits"] = exits
            self.update_time()
            self.transmit()

        self.disconnect()

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
            print(  f"\nWiFi station could not be activated.\n"
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

        self.update_time()
        try:
            response = post("http://"+SERVER_ADDR, data=str(self.transmission))
        except Exception as e:  # TODO" catch a speciifc exception?
            print(f"Transmission failed.\n Exception: {e}")
            self.red_led.value(1)
            return False
        # print(str(response))
        # try:
            
        # except Exception as e:
        #     print(f"Transmission failed.\n Exception: {e}")
        #     self.red_led.value(1)
        #     return False
        
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

class Sensor:
    def __init__(self, queue) -> None:
        """
            The HUJI-Lib sensor object which houses all possible
            functions for the sensor to do.
        """
        # Data Attributes:
        self.entrances = 0
        self.exits = 0

        # System Attirbutes:
        self.queue = queue

        # Component Attributes:
        self.blue_led = Pin(BLUE_LED_PIN, Pin.OUT)
        self.motion_L = Pin(MOTION_L_PIN, Pin.IN)
        self.motion_R = Pin(MOTION_R_PIN, Pin.IN)
        self.prev_L = MOTION_OFF
        self.prev_R = MOTION_OFF

    # Execution Functions:

    def run(self) -> None:
        while True:
            msrmnt_start = time()
            while time() - msrmnt_start <= TRNSMT_INTERVAL:
                self.measure()
            print('pushing')
            self.queue.push((self.entrances, self.exits))

    # Motion Detection Functions:

    def check_enter(self) -> bool:
        """
            Checks if someone entered the room. Returns 1 if 
            someone entered, 0 if not.
            Entrance direction is R -> L.
        """
        if self.motion_R.value() == MOTION_ON and self.prev_R == MOTION_OFF:
            start = time()
            while time() - start <= MOTION_TIMEOUT:
                l_val, r_val = self.motion_L.value(), self.motion_R.value()
                if l_val == MOTION_ON:
                    self.prev_L, self.prev_R = l_val, r_val
                    print("Entrance!")
                    return True
        return False

    def check_exit(self) -> bool:
        """
            Checks if someone has left the room. Returns 1 if 
            someone left, 0 if not.
            Exit direction is L -> R.
        """
        if self.motion_L.value() == MOTION_ON and self.prev_L == MOTION_OFF:
            start = time()
            while time() - start <= MOTION_TIMEOUT:
                l_val, r_val = self.motion_L.value(), self.motion_R.value()
                if r_val == MOTION_ON:
                    self.prev_L, self.prev_R = l_val, r_val
                    print("Exit!")
                    return True
        return False
 
    def measure(self) -> None:
        """
            Measures entrances and exits. Works for {TRNSMT_INTERVAL}
            seconds, then updates the 'self.entrances' and `self.exits`.
        """
        start = time()
        while time() - start <= TRNSMT_INTERVAL:
            self.entrances += 1 if self.check_enter() else 0
            self.exits += 1 if self.check_exit() else 0
            self.prev_L, self.prev_R = self.motion_L.value(), self.motion_R.value()

if __name__ == '__main__':
    queue = ThreadSafeQueue()
    net = NetworkWorker(queue)
    sensor = Sensor(queue)
    thread.start_new_thread(sensor.run, ())
    thread.start_new_thread(net.run, ())
