# This code SHOULD be simulated on Micropython

import socket
from time import sleep, localtime

SERVER_ADDR = "127.0.0.1"
PORT = 80
SENSOR_NO = 1
LOCATION = "Harman Science Library"
TRANSMIT_INTERVAL = 60

if __name__ == "__main__":
    while(True):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    # Connect to server
                    s.connect((SERVER_ADDR, PORT))
                    
                    # Get data from sensors
                    entrances = 30
                    exits = 20

                    # Get time data
                    t = localtime()
                    tstamp = f"{t.tm_mday:02d}/{t.tm_mon:02d}/{t.tm_year} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}" # Only on python
                    # tstamp = f"{t[2]:02d}/{t[1]:02d}/{t[0]}, {t[3]:02d}:{t[4]:02d}:{t[5]:02d}" # Only on Micropython

                    # Collect data
                    data = {"S.N.": SENSOR_NO,
                            "Location": LOCATION,
                            "Time": tstamp,
                            "Entrances": entrances,
                            "Exits": exits}
                    print(data)

                    # Send data
                    try:
                        s.send(str(data).encode())
                        print("Sent successfully.")
                        s.close()
                        print("Connection terminated.")
                        # Make green LED light up or something

                    except:
                        # Make red LED light up or something
                        print("Transmission failed.")
                    sleep(TRANSMIT_INTERVAL)
                    
                except:
                    print("Connection failed.")
                    # Make red LED light up or something

        except:
            # Connection Failed:
            print("Socket failed.")
            # Make red LED light up or something
