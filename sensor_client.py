import network
from urequests import post
from time import sleep, localtime

SERVER_ADDR = "192.168.1.215"
PORT = 80
SENSOR_NO = 1
LOCATION = "Harman Science Library - Floor 2 (Quiet)"
SLEEP_INTERVAL = 10
WIFI_SSID = "Nir 2"
WIFI_PD = "Pn0547436227"

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(WIFI_SSID, WIFI_PD)

prnt_count = 0
while not station.isconnected():
    if prnt_count > 3:
        prnt_count = 0
    print("Connecting", end='')
    print(prnt_count * '.', end='\r')
    prnt_count += 1
    sleep(.25)

print("Connected to WiFi.")

# Get data from sensors
entrances = 30
exits = 20

while(True):
    # Only on Micropython
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
    wday = "Tue" # debugging only
    tstamp = "11:"+tstamp.split(":")[1]
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
        # Make green LED light up or something            

    except Exception as e:
        # Connection Failed:
        print("Connection failed.")
        print("Exception raised: "+str(e))
        # Make red LED light up or something

    sleep(SLEEP_INTERVAL)
    entrances += 1
    
network.WLAN.disconnect()
station.active(False)
print("Disconnected from WiFi.")
