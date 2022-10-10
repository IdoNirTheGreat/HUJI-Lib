# This code SHOULD be simulated on Micropython

import socket
from time import sleep, localtime

SERVER_ADDR = "127.0.0.1"
PORT = 80
SENSOR_NO = 1
LOCATION = "Harman Science Library"

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((SERVER_ADDR, PORT))
        except:
            print("Connection failed.")
            # Make red LED light up or something

        while(True):
            # Get data from sensors
            entrances = 30
            exits = 20

            # Get time data
            t = localtime()
            tstamp = f"{t.tm_mday}/{t.tm_mon}/{t.tm_year} {t.tm_hour}:{t.tm_min}:{t.tm_sec}" # Only on python
            # tstamp = f"{t[2]}/{t[1]}/{t[0]}, {t[3]}:{t[4]}:{t[5]}" # Only on Micropython

            # Send data
            data = {"S.N.": SENSOR_NO,
                    "Location": LOCATION,
                    "Time": tstamp,
                    "Entrances": entrances,
                    "Exits": exits}

            print(data)
            try:
                s.send(str(data).encode())
                print("Sent successfully.")
                s.close()
                print("Connection terminated.")
                # Make green LED light up or something
            except:
                # Make red LED light up or something
                print("Transmission failed.")
            sleep(60)

except:
    # Connection Failed:
    print("Socket failed.")
    # Make red LED light up or something
