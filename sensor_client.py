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
        tstamp = f"{t.tm_mday:02d}/{t.tm_mon:02d}/{t.tm_year} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}" # Only on python
        # tstamp = f"{t[2]:02d}/{t[1]:02d}/{t[0]}, {t[3]:02d}:{t[4]:02d}:{t[5]:02d}" # Only on Micropython

        # Collect data
        data_dict = {"S.N.": SENSOR_NO,
                "Location": LOCATION,
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
