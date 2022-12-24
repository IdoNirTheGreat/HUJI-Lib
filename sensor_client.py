import network
from urequests import post
from time import sleep, localtime, time
from machine import Pin

SERVER_ADDR = "192.168.1.215"
PORT = 80
SENSOR_NO = 1
LOCATION = "Harman Science Library - Floor 2 (Quiet)"
TRNSMT_INTERVAL = 10
WIFI_SSID = "Nir 2"
WIFI_PD = "Pn0547436227"
LAN_TIMEOUT = 15 # In seconds

# Pin Declaration:
led_lan_conn = Pin(13, Pin.OUT) # Lights if successfully connected to LAN, blinks if trying to connect, off if isn"t connected.
blue = Pin(12, Pin.OUT)
led_server_success = Pin(14, Pin.OUT) # Successfully connected to server.
led_server_failure = Pin(27, Pin.OUT) # Failed connecting to server.
thermo = Pin(2, Pin.IN)
sound = Pin(4, Pin.IN)
conn_loading = .5

# WiFi Declaration:
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(WIFI_SSID, WIFI_PD)

# Connect to LAN:
start = time()
conn_loading = 0
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

while(True):
    print("\nConnected to WiFi.")
    if not led_lan_conn.value(): # Make LAN LED light solid
        led_lan_conn.value(1)

    # Get data from sensors
    entrances = 30
    exits = 20

    while(True):
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

        # Collect data:
        wday = "Sun" # debugging only
        tstamp = "8:"+tstamp.split(":")[1]
        data_dict = {}
        data_dict["S.N."] = SENSOR_NO
        data_dict["Location"] = LOCATION
        data_dict["Weekday"] = wday
        data_dict["Date"] = dstamp
        data_dict["Time"] = tstamp
        data_dict["Entrances"] = entrances
        data_dict["Exits"] = exits
        
        print(data_dict)

        # Send data
        try:
            post("http://"+SERVER_ADDR, data=str(data_dict))
            print("Sent successfully.")
            led_server_success.value(1)          

        except Exception as e:
            # Connection Failed:
            print("Connection failed.")
            print("Exception raised: "+str(e))
            led_server_failure.value(1)

        sleep(TRNSMT_INTERVAL)
        entrances += 1
