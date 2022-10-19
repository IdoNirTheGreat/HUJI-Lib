from email.policy import default
import logging
import csv
from ast import literal_eval
from http.server import HTTPServer, BaseHTTPRequestHandler
from os.path import splitext
from typing import Dict
from jinja2 import Template

ALLOWED_HOSTS = "127.0.0.1"
HOST = "127.0.0.1"
PORT = 80
MAX_CONNECTIONS = 5
REQ_SIZE = 1024
HEBREW_ENCODING = "iso-8859-1" # An encoding that supports Hebrew on HTML)
CURRENT_STATE_DB = 'current_state.csv'
TRANSMISSION_LOG_DB = 'transmission_log.csv'
HOMEPAGE_FILENAME = 'webpage.html'
LOCATION_LIST = [   "CSE Aquarium C100",
                    "CSE Aquarium B100",
                    "CSE Aquarium A100",
                    "Einstein Institute Math Library",
                    "Harman Science Library - Floor 2 (Quiet)",
                    "Harman Science Library - Floor 2 (Loud)",
                    "Harman Science Library - Floor -1",
                ]
TRANSMISSION_FIELDS = [ "S.N.",
                        "Location",
                        "Time",
                        "Entrances",
                        "Exits",
        ]
CURRENT_STATE_DEFAULTS = [  "CSE Aquarium C100,0,90",
                            "CSE Aquarium B100,0,55",
                            "CSE Aquarium A100,0,55",
                            "Harman Science Library - Floor 2 (Loud),50,100",
                            "Harman Science Library - Floor 2 (Quiet),50,50",
                            "Harman Science Library - Floor -1,0,150",
                            "Einstein Institute Math Library,0,50",
                            
                        ]
CURRENT_STATE_FIELDS = [    "Location",
                            "Current Amount",
                            "Max Amount",
                        ]

class hujilib_http(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Accept-Language', 'he-IL')
       
        # If a specific file was requested:
        if len(self.path[1:]): 
            extension = splitext(self.path[1:])[1]
            if extension == '.css':
                self.send_header('Content-Type', 'text/css')
                self.end_headers()
                self.wfile.write(file_to_string(self.path[1:]))
            elif extension == '.js':
                self.send_header('Content-Type', 'application/javascript')
                self.end_headers()
                self.wfile.write(file_to_string(self.path[1:]))
            elif extension == '.jpg':
                self.send_header('Content-Type', 'image/jpg')
                self.end_headers()
                self.wfile.write(open_image(self.path[1:]))

        # If no file was specified, send the mainpage html:
        else:
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(file_to_string_html(HOMEPAGE_FILENAME))

    def do_POST(self):
        # Get data dictionary from request and send response:
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        # print(post_data.decode())
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()

        # Update transmission log:
        data_dict = literal_eval(str(post_data)[2:-1])
        logger.info("Sensor " + str(data_dict['S.N.']) + " has transmitted.")
        insert_to_csv(TRANSMISSION_LOG_DB, data_dict, logger)

        # Update current state data:
        update_current_state(data_dict, logger)

def file_to_string(filename: str, encoder: str=HEBREW_ENCODING) -> bytes:
    """ Recieves a filename and an encoder and returns the file 
        as a binary stream with the requested encoding.
        Writes to the logger if an error has occurred."""
    try:
        with open(filename, 'r', encoding=encoder) as f:
            buffer = f.read()
            return buffer.encode(encoder)

    except IOError:
        logger.error(f"An I/O error has occurred when opening {filename}.")

def file_to_string_html(filename: str, encoder: str=HEBREW_ENCODING) -> bytes:
    """ Recieves specifically an html filename and an encoder and returns the file 
        as a binary stream with the requested encoding.
        Writes to the logger if an error has occurred."""
    
    # Read current state DB:
    rows = []
    try:
        with open('current_state.csv', 'r', newline='') as db:
            reader = csv.reader(db)
            for row in reader: rows.append(row)
    except IOError:
        logger.error(f"An I/O error has occurred when opening {filename}.")
    # Read webpage file Html:
    try:
        with open(filename, 'r', encoding=encoder) as f:
            buffer = f.read()
            tm = Template(buffer)
            sub = str(tm.render(parm_1=str(int(int(rows[5][1]) / int(rows[5][2]) * 100)), herman_top=str(int(int(rows[5][1]) / int(rows[5][2]) * 180)),
            parm_2=str(int(int(rows[6][1]) / int(rows[6][2]) * 100)), herman_top_quiet= str(int(int(rows[6][1]) / int(rows[6][2])*180)))) # all the parameters that should be substituted according to the current_state.csv
            return sub.encode(encoder)
    except IOError:
        logger.error(f"An I/O error has occurred when opening {filename}.")

def open_image(filename: str) -> bytes:
    """ Recieves an image filename and an encoder and returns
        the image as a binary stream with the requested 
        encoding. 
        Writes to the logger if an error has occurred."""
    try:
        with open(filename, 'rb') as img:
            return img.read()
    except IOError:
        logger.error(f"An I/O error has occurred when opening {filename}.")

def create_csv(csv_filename: str, headers: str, logger: logging.Logger) -> None:
    """ Receives a filename and headers and creates a csv 
        file with the desired headers."""
    try:
        with open(csv_filename, 'w') as db:
            w = csv.DictWriter(db, fieldnames=headers)
            w.writeheader()
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {csv_filename}.")

def insert_to_csv(filename: str, data_dict: Dict, logger: logging.Logger) -> None:
    """ Recieves the filename of a csv file, a dictionary and
        a logger, and appends the corresponding values of the 
        csv fields in a new row in the csv file.
        Writes to the logger if an error has occurred.
        """
    try:
        with open(filename, 'a', newline='') as db:
            writer = csv.DictWriter(db, fieldnames=TRANSMISSION_FIELDS)
            writer.writerow(data_dict)
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {filename}.")

def update_current_state(data_dict: Dict, logger: logging.Logger, filename: str=CURRENT_STATE_DB, is_setup: bool=False) -> None:
    ''' Recieves a dictionary dataset sent from a sensor,
        the server's logger, then updates the current status 
        in the file. 
        Set 'is_setup_ to true only when inputting the 
        default values into the DB (is used to reset current 
        people amount in a selected location to zero).
        Writes to the logger if an error has occurred.'''
    
    # Read current state DB:
    reader_rows = []
    try:
        with open(filename, 'r', newline='') as db:
            reader = csv.reader(db)
            for row in reader: reader_rows.append(row)
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {filename}.")

    # Takes csv fields and values and puts them in a list of dicts:
    current_state_dicts = [{field: value for (field, value) in zip(reader_rows[0], row)} for row in reader_rows[2:]]
    
    # Update the current state according to the new data:
    found = False
    for location_dict in current_state_dicts:
        if location_dict['Location'] == data_dict['Location']:
            location_dict['Current Amount'] = str(int(data_dict['Entrances']) - int(data_dict['Exits']))
            found = True
            break

    # If the new location wasn't found in the DB, notify error and stop running this function:  
    if not found:
        logger.error(f"Current state DB could not be updated according to sensor {data_dict['S.N.']}'s data, because the location name {data_dict['Location']} could not be found in {filename}.")
    
    # Else, rewrite the DB:
    else:
        create_csv(CURRENT_STATE_DB, CURRENT_STATE_FIELDS, logger)
        try:
            with open(filename, 'a', newline='') as db:
                writer = csv.DictWriter(db, fieldnames=CURRENT_STATE_FIELDS)
                for location_dict in current_state_dicts:  
                    writer.writerow(location_dict)
            logger.info(f"Current state DB was updated according to sensor {data_dict['S.N.']}'s data.")

        except IOError:
            logger.error(f"An I/O error has occurred when writing to {filename}.")

if __name__ == '__main__':
    # Logger setup:
    logging.basicConfig(filename="server.log",
                        filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        level=logging.INFO,
                        )
    logger = logging.getLogger()
    logger.info("Server has started running.")

    # DBs setup:
    create_csv(TRANSMISSION_LOG_DB, TRANSMISSION_FIELDS, logger)
    create_csv(CURRENT_STATE_DB, CURRENT_STATE_FIELDS, logger)
    try:
        with open(CURRENT_STATE_DB, 'a') as f:
            for line in CURRENT_STATE_DEFAULTS:
                f.write(line + '\n')
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {CURRENT_STATE_DB}.")
    logger.info("DBs were created and set to default.")

    # HTTP handling:
    server = HTTPServer((HOST, PORT), hujilib_http)
    try:
        server.serve_forever()
        logger.info("The server has started running.")
    except KeyboardInterrupt:
        logger.warning("The server has catched a keyboard interrupt.")
    server.server_close()
    logger.info("The server has finished running.")
