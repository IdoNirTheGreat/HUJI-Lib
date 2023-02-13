# Module Imports:
import network
import queue
from machine import Pin, deepsleep
import uasyncio as asyncio
from time import sleep, localtime, time

# Network Constants:
SERVER_ADDR = "192.168.170.34"
SERVER_PORT = 80
WLAN_SSID = "MWTSOA"
WLAN_PW = "zmora6599"

# Operation Constants:
_SN_VAL = 1
_LOC_VAL = "Harman Science Library - Floor 2 (Quiet)"
TRANSMIT_INTERVAL = 60 # In seconds
TRANSMIT_TIMEOUT = 5 # In seconds
LAN_TIMEOUT = 15 # In seconds
MOTION_ON = 0
MOTION_OFF = 1
MOTION_TIMEOUT = 1 # The timout duration to cancel an entrance or exit if only one sensor was activated.
BLINK_TIME = 0.25 # In seconds
WAKEUP_TIME = (8, 0) # (Hours, Minutes)
SLEEP_TIME = (19, 0) # (Hours, Minutes)

# Component Constants:
YELLOW_LED_PIN = 23 # Yellow: Lights if successfully connected to LAN, blinks if trying to connect, off if isn't connected.
BLUE_LED_PIN = 22 # Blue: Activated when detected motion.
GREEN_LED_PIN = 21 # Green: Successfully connected to server.
RED_LED_PIN = 19 # Red: Failed connecting to server.
MOTION_L_PIN = 12 # Left motion sensor's pin.
MOTION_R_PIN = 14 # Right motion sensor's pin.

# Dictionary Constants:
SN = "S.N."
LOCATION = "Location"
ENTRANCES = "Entrances"
EXITS = "Exits"
WEEKDAY = "Weekday"
DATE = "Date"
TIME = "Time"

# Queue Put Values:
TRANSMIT = "Transmit"
BLINK = "Blink"
CHECK_ENTER = "Check Enter"
CHECK_EXIT = "Check Exit"

class Sensor:
    def __init__(self) -> None:
        """
        HUJI-Lib network sender, sends updates from the
        sender to the server.
        """
        # Data Attributes:
        self.transmission = {}
        self.transmission[SN] = _SN_VAL
        self.transmission[LOCATION] = _LOC_VAL
        self.transmission[ENTRANCES] = 0
        self.transmission[EXITS] = 0
        self.update_time()

        # System Attributes:
        self.station = network.WLAN(network.STA_IF)

        # Component Attributes:
        self.yellow_led = Pin(YELLOW_LED_PIN, Pin.OUT)
        self.green_led = Pin(GREEN_LED_PIN, Pin.OUT)
        self.red_led = Pin(RED_LED_PIN, Pin.OUT)
        self.blue_led = Pin(BLUE_LED_PIN, Pin.OUT)
        self.motion_L = Pin(MOTION_L_PIN, Pin.IN)
        self.motion_R = Pin(MOTION_R_PIN, Pin.IN)
        self.prev_L = MOTION_OFF
        self.prev_R = MOTION_OFF

    ### Runtime Functions:
    async def run(self) -> None:
        print(f"HUJI-Lib Sensor {self.transmission[SN]} has started running...")

        # Create the Consumer-Producer shared queue:
        self.q = queue.Queue()

        # Run the producer and consumer:
        await asyncio.gather(self.producer(self.q), self.consumer(self.q))

    async def producer(self, q: queue.Queue) -> None:
        """
            Measures entrances and exits. Works for {TRNSMT_INTERVAL}
            seconds, then updates the 'self.entrances' and `self.exits`.
        """

        print("Producer has started running.")
        
        # Generate Work:
        while True:
            self.update_time()

            # If the sensor should be awake:
            if self.is_operating_hours():
                print("Sensor is now awake.")
                if not self.station.isconnected(): self.connect()
                start = time()
                while time() - start <= TRANSMIT_INTERVAL:
                    # Check entrances and exits simultaneously with gather:
                    await asyncio.gather(self.check_enter(self.q), self.check_exit(self.q))
                    
                    # Update sensors' previous values:
                    self.prev_L, self.prev_R = self.motion_L.value(), self.motion_R.value()
                
                # Transmit to server:
                await q.put(TRANSMIT)

            # If the sensor should go to deep sleep:
            else:
                print(f"Entering deep sleep mode for {self.get_remaining_sleep_time()} seconds...")
                if self.station.isconnected(): self.disconnect()
                deepsleep(1000 * self.get_remaining_sleep_time())


    async def consumer(self, q: queue.Queue):
        """
            A intermediary function that sends a transmission
            when the producer has flagged it is ready.
        """

        print("Consumer has started running.")
        
        while True:
            # Wait for work:
            item = await q.get()

            # Check for stop signal:
            if item is None:
                break

            # Continue to the corresponding function:
            if item == TRANSMIT:
                await self.transmit()
            
            elif item == BLINK: 
                # Could only blink blue LED for motion
                await self.blink(self.blue_led)

        print("Consumer has finished running.")

    ### Connectibility Functions:
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

    async def transmit(self):
        """
            Sends the transmission dict to the server.
            Lights green LED and returns True if succeeded,
            Lights red LED and returns False else.
        """

        self.update_time()

        try:
            print("Transmitting to server...")
            wrap = asyncio.open_connection(SERVER_ADDR, SERVER_PORT)
            try: # Wrap-around for the open connection function to add timeout:
                self.input_stream, self.output_stream = yield from asyncio.wait_for(wrap, timeout=TRANSMIT_TIMEOUT)
            except asyncio.TimeoutError:
                print("Connection attempt has reached its timeout.")
                
                # Set lights to failure and return from function:
                self.red_led.value(1)
                self.green_led.value(0)
                return

            template = \
                "POST / HTTP/1.1\r\n" \
                "Host: {ip}\r\n" \
                "User-Agent: python-requests/2.28.1\r\n" \
                "Accept-Encoding: gzip, deflate\r\n" \
                "Accept: */*\r\n" \
                "Content-Type: application/text\r\n" \
                "Connection: keep-alive\r\n" \
                "Content-Length: {length}\r\n" \
                "\r\n" \
                "{body}"
            
            # Add the request output stream buffer:
            self.output_stream.write(template.format(ip=SERVER_ADDR, length=len(str(self.transmission)), body=str(self.transmission)))
            # Drain output stream buffer (send through socket):
            await self.output_stream.drain()

            print(f"Transmission sent at {self.transmission['Date']}, {self.transmission['Time']}")

            # Set lights to success:
            self.red_led.value(0)
            self.green_led.value(1)

        except Exception as e:
            print(f"Transmission failed.\n Exception: {e}")

            # Set lights to failure:
            self.green_led.value(0)
            self.red_led.value(1)

        finally:
            # Close connections after every attempt:
            if hasattr(self, 'output_stream'): self.output_stream.close()
            if hasattr(self, 'input_stream'): self.input_stream.close()

    ### Data Proccessing Functions:
    def __str__(self) -> str:
        """
            Return value of all attributes of self as a string.
        """

        return  f"\n### Sensor {self.transmission[SN]} - Beginning of Report ###\n" + \
                f"Sensor Location: {self.transmission[LOCATION]}\n" + \
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
        # wday = "Sun" # debugging only
        # tstamp = "8:"+tstamp.split(":")[1] # debugging only
        self.transmission[WEEKDAY] = wday
        self.transmission[DATE] = dstamp
        self.transmission[TIME] = tstamp

    ### Motion Detection Functions:
    async def check_enter(self, q) -> bool:
        """
            Checks if someone entered the room. Returns 1 if 
            someone entered, 0 if not.
            Entrance direction is R -> L.
        """
        if self.motion_R.value() == MOTION_ON and self.prev_R == MOTION_OFF:
            start = time()
            while time() - start <= MOTION_TIMEOUT:
                l_val, r_val = self.motion_L.value(), self.motion_R.value()
                if l_val == MOTION_ON and r_val == MOTION_OFF:
                    self.prev_L, self.prev_R = l_val, r_val
                    print("Entrance!")
                    self.transmission[ENTRANCES] += 1
                    await q.put(BLINK)
                    return True
        return False

    async def check_exit(self, q) -> bool:
        """
            Checks if someone has left the room. Returns 1 if 
            someone left, 0 if not.
            Exit direction is L -> R.
        """
        if self.motion_L.value() == MOTION_ON and self.prev_L == MOTION_OFF:
            start = time()
            while time() - start <= MOTION_TIMEOUT:
                l_val, r_val = self.motion_L.value(), self.motion_R.value()
                if r_val == MOTION_ON and l_val == MOTION_OFF:
                    self.prev_L, self.prev_R = l_val, r_val
                    print("Exit!")
                    self.transmission[EXITS] += 1
                    await q.put(BLINK)
                    return True
        return False

    # Other Functions:
    async def blink(self, led):
        """
            Blink a given led using async.
        """
        led.value(1)
        await asyncio.sleep(BLINK_TIME)
        led.value(0)

    def get_time(self):
        """
            Returns a tuple format (Day, Hours, Minutes) of current time.
        """
        t = localtime()
        return (t[3], t[4])

    def is_operating_hours(self):
        """
            Returns a boolean which represents if the current time
            is within the operating hours.
        """
        current_day = self.transmission[WEEKDAY]
        current_hour, current_minute = self.get_time()
        if  current_day in ["Sun", "Mon", "Tue", "Wed", "Thu"] and \
            WAKEUP_TIME[0] <= current_hour <= SLEEP_TIME[0] and \
            WAKEUP_TIME[1] <= current_minute <= SLEEP_TIME[1]:
            return True
        
        return False

    def get_remaining_sleep_time(self):
        """
            Returns the remaining sleep time (of sensor) in seconds.
        """
        current_hour, current_minute = self.get_time()
        opening_hour, opening_minute = WAKEUP_TIME
        if opening_minute < current_minute:
            opening_hour -= 1
            opening_minute += 60
        
        if opening_hour < current_hour:
            opening_hour += 24

        return (opening_hour-current_hour)*3600 + (opening_minute-current_minute+1)*60

if __name__ == '__main__':
    sensor = Sensor()
    asyncio.run(sensor.run())
