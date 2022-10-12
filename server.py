import logging
import csv
from ast import literal_eval
from http.server import HTTPServer, BaseHTTPRequestHandler

ALLOWED_HOSTS = "127.0.0.1"
HOST = "127.0.0.1"
PORT = 80
MAX_CONNECTIONS = 5
REQ_SIZE = 1024
HEBREW_ENCODING = "iso-8859-1" #"Windows-1255"  # Windows-1255 encoding is to support Hebrew on HTML)
DB_FILENAME = 'current_status.csv'
RAW_DATA_FILENAME = 'all_sensor_transmissions.csv'
HOMEPAGE_FILENAME = 'webpage.html'
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


class hujilib_http(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Accept-Language', 'he-IL')

        self.end_headers()

        self.wfile.write(file_to_string(HOMEPAGE_FILENAME))

def file_to_string(filename: str, encoder: str=HEBREW_ENCODING) -> str:
    """ Recieves a filename and an encoder and returns the file 
        as a binary stream with the requested encoding.
        Writes to the logger if an error has occurred."""
    try:
        with open(filename, 'r', encoding=encoder) as f:
            buffer = f.read()
            return buffer.encode(encoder)

    except IOError:
        logger.error(f"An I/O error has occurred when reading {filename}.")

def create_csv(csv_filename: str, headers: str, logger: logging.Logger) -> None:
    """ Receives a filename and headers and creates a csv 
        file with the desired headers."""
    try:
        with open(csv_filename, 'w') as db:
            w = csv.DictWriter(db, fieldnames=headers)
            w.writeheader()
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {csv_filename}.")

def insert_to_csv(filename, dict_data, logger):
    """ Recieves the filename of a csv file, a dictionary and
        a logger, and appends the corresponding values of the 
        csv fields in a new row in the csv file.
        Writes to the logger if an error has occurred.
        """
    try:
        with open(filename, 'a', newline='') as db:
            w = csv.DictWriter(db, fieldnames=FIELDS)
            w.writerow(dict_data)
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {filename}.")

def update_current_status(filename, dict_data):
    pass
    
def fetch_filename(req):
    """
    Fetch filename from an HTTP request and return it.
    """
    req = req[4:] # Skip ' GET '
    filename = "."

    for c in req:
        if c is ' ': break
        else: filename += c

    return filename

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
    create_csv(RAW_DATA_FILENAME, FIELDS, logger)

    server = HTTPServer((HOST, PORT), hujilib_http)
    server.serve_forever()
    logger.info("The server has started running.")
    server.server_close()
    logger.info("The server has finished running.")

    # Old code:
    """
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
                print(f"File requested: {fetch_filename(req)}\n\n")
                
                # Send response according to the request:
                # If sensor sent request:
                if  "GET" not in req and \
                    type(literal_eval(req)) is dict and \
                    FIELDS == list(literal_eval(req).keys()):
                    
                    sensor_data = literal_eval(req)
                    logger.info("Sensor " + str(sensor_data['S.N.']) + " has transmitted.")
                    insert_to_csv(RAW_DATA_FILENAME, sensor_data, logger)

                # If HTTP client requested to download webpage and its elements:
                elif "GET" in req:
                    cli_sock.send(b'HTTP/1.1 200 OK\n')
                    cli_sock.send(b'Accept-Language: he-IL\n')
                    cli_sock.send(b'Content-Type: text/html\n')
                    cli_sock.send(b'Accept-Encoding: gzip, deflate\n')
                    cli_sock.send(b'Connection: close\n\n')
                    req_file = fetch_filename(req)
                    
                    if req_file == "./":
                        res = build_webpage().encode("Windows-1255") # Windows-1255 encoding is to support Hebrew on HTML
                        cli_sock.sendall(res)
                    
                    else:
                        try:
                            with open(req_file, 'r') as f:
                                f_stream = str(f.readlines())
                                print(type(f_stream))
                                res = f_stream.encode("Windows-1255")
                                cli_sock.sendall(res)
                        
                        except:
                            print(f"The file '{req_file}' does not exist.")


                else:
                    # If another type of request was made, do something:
                    logger.warning("An unknown type of request was sent: \n{req}\n")

                # Close client socket:
                cli_sock.close()

    except:
        logger.error("Socket creation failed.")
    """
