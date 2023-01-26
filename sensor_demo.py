# This code SHOULD be simulated on Micropython

from requests import post # Should be changed to urequests on Micropython
from time import sleep, localtime

SERVER_ADDR = "127.0.0.1"
PORT = 80
SENSOR_NO = 1
LOCATION = "Harman Science Library - Floor -1"
SLEEP_INTERVAL = 10

if __name__ == "__main__":
    # Get data from sensors
    entrances = 30
    exits = 20

    while(True):

        # Get time data
        t = localtime()
        wday = ""
        if t.tm_wday == 0:
            wday = "Mon"
        elif t.tm_wday == 1:
            wday = "Tue"
        elif t.tm_wday == 2:
            wday = "Wed"
        elif t.tm_wday == 3:
            wday = "Thu"
        elif t.tm_wday == 4:
            wday = "Fri"
        elif t.tm_wday == 5:
            wday = "Sat"
        elif t.tm_wday == 6:
            wday = "Sun"

        # Only on python
        dstamp = f"{t.tm_mday:02d}/{t.tm_mon:02d}/{t.tm_year}"  
        tstamp = f"{t.tm_hour:02d}:{t.tm_min:02d}"

        # # Only on Micropython
        # wday = ""
        # if t[6] == 0:
        #     wday = "Mon"
        # elif t[6] == 1:
        #     wday = "Tue"
        # elif t[6] == 2:
        #     wday = "Wed"
        # elif t[6] == 3:
        #     wday = "Thu"
        # elif t[6] == 4:
        #     wday = "Fri"
        # elif t[6] == 5:
        #     wday = "Sat"
        # elif t[6] == 6:
        #     wday = "Sun"
        # dstamp = f"{t[2]:02d}/{t[1]:02d}/{t[0]}"
        # tstamp = f"{t[3]:02d}:{t[4]:02d}"

        # Collect data:
        wday = "Tue" # debugging only
        tstamp = "11:"+tstamp.split(":")[1] # debugging only
        data_dict = {   "S.N.": SENSOR_NO,
                        "Location": LOCATION,
                        "Weekday": wday,
                        "Date": dstamp,
                        "Time": tstamp,
                        "Entrances": entrances,
                        "Exits": exits}
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