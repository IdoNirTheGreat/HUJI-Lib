import socket
import logging
import csv
from ast import literal_eval

ALLOWED_HOSTS = "127.0.0.1"
PORT = 80
MAX_CONNECTIONS = 5
REQ_SIZE = 1024
DB_FILENAME = 'current_status.csv'
RAW_DATA_FILENAME = 'all_sensor_transmissions.csv'
LOCATION_LIST = [   "Harman Science Library", 
                    "Einstein Institute Math Library",
                    "Harman Science Library - Floor 2 (Quiet)",
                    "CSE Aquarium C100",
                    "Harman Science Library - Floor 2 (Loud)",
                ]
FIELDS = [  "S.N.",
            "Location",
            "Time",
            "Entrances",
            "Exits"
        ]

def build_webpage():
    page = """
    <html>
        <style>
            a:visited
            {
                color: yellow;
            }
            body 
            {
            font-family: courier, serif;
            color: rgb(16, 16, 236);
            background: rgb(0, 0, 0);
            }
            </style>

        <title>
            Library Project
        </title>

        <head>   
        <meta content="width=device-width, initial-scale=1" name="viewport"></meta>   
        </head>   

        <body>
            <br></br>

            <center><h1>Library Project</h1></center>
            <br></br> 

            <center>
                <h2>Library Status</h2>
                <h3>Harman Science Library ספריית הרמן למדע</h3>
                <a  href="https://www.google.com/maps/place/Harman+Science+Library/@31.7762469,35.1962321,15z/data=!4m5!3m4!1s0x0:0x976933b668603686!8m2!3d31.7765422!4d35.1956818"
                    target="_blank">
                    <img    class="lu-fs"
                            height="160"
                            id="lu_map"
                            src="https://www.google.com/maps/vt/data=2Gg6lDK-Ci_csXy4ooB7HY3z3OD5M72cJpuqxgBut-j4hf5II4i74YjIvdTHwymV1_ndigc94sVyNi5WJcaKgAPrBBD5ipRKocwV45VoHvipyIW_ivbx7wOohW9rp-HrXcZdqpUg6DFOXiqacMxq9kKSTamjNZdqJAz1HjlF-kj3HmT-bd1rb9zY3xXj5R7sN7pIlyjivtASSQ&amp;w=182&amp;h=160"
                            width="182" 
                            title="Map of Harman Science Library"
                            alt="Map of Harman Science Library"
                            data-atf="1"
                            data-frt="0"
                            style="display: block;">
                    </img>
                </a>
                    
                <!-- <script>
                    let d = new Date();
                    alert("Today's date is " + d);
                </script> -->
            
            </center>

            <center><h2>Useful Links:</h2></center>
                <a  href="https://www.huji.ac.il/rooms/" 
                    target="_blank"> 
                    1. Reserve study rooms 
                </a>
            <br></br>

            <center><p>Created by Ido Nir and Noam Peled.</p></center>
            <br></br>
        </body>

    </html>
    """
    
    return page

def create_csv(filename, headers):
    try:
        with open(filename, 'w') as db:
            w = csv.DictWriter(db, fieldnames=headers)
            w.writeheader()
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {filename}.")

def insert_to_csv(filename, dict_data, logger):
    try:
        with open(filename, 'a', newline='') as db:
            w = csv.DictWriter(db, fieldnames=FIELDS)
            w.writerow(dict_data)
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {filename}.")

def update_current_status(filename, dict_data):
    pass
    

if __name__ == '__main__':
    # Logger setup:
    logging.basicConfig(filename="server.log",
                        filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        level=logging.INFO,
                        )
    logger = logging.getLogger()
    logger.info("Server has started running.")

    # DB setup:
    create_csv(RAW_DATA_FILENAME, FIELDS)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as est_sock:
            # Establish a connection with a socket designated only for making connections:
            try:
                est_sock.bind((ALLOWED_HOSTS, PORT))
                est_sock.listen(MAX_CONNECTIONS)
            except:
                logging.error("Socket bind or listening failed.")

            while(True):
                # Create a new socket with a client, and save client's address:
                cli_sock, cli_addr = est_sock.accept()

                # Recieve request:
                req = cli_sock.recv(REQ_SIZE)
                req = str(req)[2:-1] # The slice is to delete the 'b' indicating binary stream
                print(f"\nRequest:\n {req}\n\n")
                
                # Send response according to the request:
                # If sensor sent request:
                if  "GET" not in req and \
                    type(literal_eval(req)) is dict and \
                    FIELDS == list(literal_eval(req).keys()):
                    
                    sensor_data = literal_eval(req)
                    logger.info("Sensor " + str(sensor_data['S.N.']) + " has transmitted.")
                    insert_to_csv(RAW_DATA_FILENAME, sensor_data, logger)

                # If HTTP client requested to download webpage:
                elif "GET" in req:
                    res = build_webpage().encode("Windows-1255") # Windows-1255 encoding is to support Hebrew on HTML
                    cli_sock.send(b'HTTP/2.0 200 OK\n')
                    cli_sock.send(b'Accept-Language: he-IL\n')
                    cli_sock.send(b'Content-Type: text/html\n')
                    cli_sock.send(b'Accept-Encoding: gzip, deflate\n')
                    cli_sock.send(b'Connection: close\n\n')
                    cli_sock.sendall(res)

                else:
                    # If another type of request was made, do something:
                    logger.warning("An unknown type of request was sent: \n{req}\n")

                # Close client socket:
                cli_sock.close()

    except:
        logger.error("Socket creation failed.")
        