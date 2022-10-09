# This code SHOULD be simulated on Micropython

import socket
from time import sleep, localtime

SERVER_ADDR = "127.0.0.1"
PORT = 50000
SENSOR_NO = 1

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((SERVER_ADDR, PORT))
        except:
            print("Connection failed.")
            # Make red LED light up or something

        while(True):
            # Get data from sensors

            # Get time data
            t = localtime()
            tstamp = f"{t.tm_mday}/{t.tm_mon}/{t.tm_year} {t.tm_hour}:{t.tm_min}:{t.tm_sec}"

            # Send data
            data = {"S.N.":SENSOR_NO, "Time":tstamp, "In":30, "Out":20}
            print(data)
            try:
                s.send(str(data).encode())
                print("Sent successfully.")
            except:
                print("Transmission failed.")
            sleep(60)

except:
    # Connection Failed:
    print("Socket failed.")
    # Make red LED light up or something
