import socket
from time import sleep, strftime, localtime

SERVER_ADDR = "127.0.0.1"
PORT = 50000
SENSOR_NO = 1

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((SERVER_ADDR, PORT))

    while(True):
        # Get data from sensors

        # Get time data
        tstamp = strftime("%x, %X", localtime())

        # Send data
        data = {"S.N.":SENSOR_NO, "Time":tstamp, "In":30, "Out":20}
        
        try:
            s.send(str(data).encode())
            print("Sent successfully.")
        except Exception:
            print("Transmission failed.")
        sleep(60)
