import network
from urequests import post
from time import sleep, localtime, time
from machine import Pin
from sys import exit
import _thread

SERVER_ADDR = "10.0.0.10"
PORT = 80
SENSOR_NO = 1
LOCATION = "Harman Science Library - Floor 2 (Quiet)"
TRNSMT_INTERVAL = 30
WIFI_SSID = "Noam"
WIFI_PD = "0527904190"
LAN_TIMEOUT = 15 # In seconds
MOTION_ON = 0
MOTION_OFF = 1
MOTION_TIMEOUT = 1 # The timout duration to cancel an entrance or exit if only one sensor was activated.

# Components' Declaration:
led_motion = Pin(23, Pin.OUT) # Blue: Activated when detected motion.
led_lan_conn = Pin(22, Pin.OUT) # Yellow: Lights if successfully connected to LAN, blinks if trying to connect, off if isn't connected.
led_server_success = Pin(21, Pin.OUT) # Green: Successfully connected to server.
led_server_failure = Pin(19, Pin.OUT) # Red: Failed connecting to server.
pe_sensor_L = Pin(13, Pin.IN)
pe_sensor_R = Pin(12, Pin.IN)

def check_enter(sensor_L, sensor_R, previous_L, previous_R):
    if sensor_R.value() != previous_R and sensor_R.value() == MOTION_ON:
        print(f"Motion!: sensor_R = {sensor_R.value()}, previous_R = {previous_R}")
        start = time()
        while time() - start <= MOTION_TIMEOUT:
            # print(f"Motion!: sensor_R = {sensor_R.value()}, sensor_L = {sensor_L.value()}")
            if sensor_R.value() == MOTION_OFF and sensor_L.value() == MOTION_ON:
                print("Entrance!")
                return 1
    return 0

def check_exit(sensor_L, sensor_R, previous_L, previous_R):
    if sensor_L.value() != previous_L and sensor_L.value() == MOTION_ON:
        print(f"Motion!: sensor_L = {sensor_L.value()}, previous_L = {previous_L}")
        start = time()
        while time() - start <= MOTION_TIMEOUT:
            # print(f"Motion!: sensor_R = {sensor_R.value()}, sensor_L = {sensor_L.value()}")
            if sensor_L.value() == MOTION_OFF and sensor_R.value() == MOTION_ON:
                print("Exit!")
                return 1
    return 0

# def write_data(data_dict):
#     # Write constant data to file:
#     with open(DATA_FILE, 'w') as f:
#         f.writelines(   SENSOR_NO + '\n' + 
#                         LOCATION + '\n' +
#                         data_dict["Weekday"] = wday
#         data_dict["Date"] = dstamp
#         data_dict["Time"] = tstamp
#                     )


if __name__ == '__main__':
    # WiFi Declaration:
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(WIFI_SSID, WIFI_PD)

    # Connect to LAN:
    start = time()
    while not station.isconnected() and not time()-start > LAN_TIMEOUT:
        if led_lan_conn.value():
            led_lan_conn.value(0)
        else:
            led_lan_conn.value(1)
        print(f"\r({time()-start}s) Connecting{((time()-start) % 4) * '.'}   ", end='')
        sleep(.25)

    # LAN timeout:
    if time()-start > LAN_TIMEOUT:
        station.active(False)
        print("Disconnected from WiFi.")
        raise Exception(f"LAN_TIMEOUT_EXCEPTION ({LAN_TIMEOUT}s)")

    print("\nConnected to WiFi.")
    if not led_lan_conn.value(): # Make LAN LED light solid
        led_lan_conn.value(1)

    # Add sensor's constant data:
    data_dict = {}
    data_dict["S.N."] = SENSOR_NO
    data_dict["Location"] = LOCATION
    entrances, exits = 0, 0
    pe_previous_R, pe_previous_L = MOTION_OFF, MOTION_OFF

    # Measure entrances and exits:
    def measure_movement():
        start_msrmnt = time()
        print(f"Started Measurement at {start_msrmnt}.")
        while time() - start_msrmnt <= TRNSMT_INTERVAL:
            enter_value = check_enter(pe_sensor_L, pe_sensor_R, pe_previous_L, pe_previous_R)
            exit_value = check_exit(pe_sensor_L, pe_sensor_R, pe_previous_L, pe_previous_R)
            
            # Blink motion LED:
            if enter_value and exit_value: 
                led_motion.value(1)
                sleep(0.5)
                led_motion.value(0)

            entrances += enter_value
            exits += exit_value
            pe_previous_L = pe_sensor_L.value()
            pe_previous_R = pe_sensor_R.value()
        print("Ended Measurement.")

    # Transmit to server
    def transmit():
        # Send data to server:
        print("Sending to server:")
        try:
            post("http://"+SERVER_ADDR, data=str(data_dict))
            print("Sent successfully.")
            led_server_success.value(1)          

        except Exception as e:
            # Connection Failed:
            print("Connection failed.")
            print("Exception raised: "+str(e))
            led_server_failure.value(1)

    # Main measuring loop:
    while(True):              
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
        data_dict["Weekday"] = wday
        data_dict["Date"] = dstamp
        data_dict["Time"] = tstamp
        
        print(data_dict)
        
        # Main loop - Run independant transmit and measure threads,
        # then print the sent data.
        try:
            _thread.start_new_thread(transmit, [])
            exit(1)
            _thread.start_new_thread(measure_movement, [])
            data_dict["Entrances"] = entrances
            data_dict["Exits"] = exits
            print(data_dict)

        except Exception as e:
            print("There was an error with multithreading: ")
            print(e)
            led_server_success.value(0)
            led_server_failure.value(1)
            exit(-1)
            
