import logging
import csv
from ast import literal_eval
from http.server import HTTPServer, BaseHTTPRequestHandler
from os.path import splitext
from typing import Dict, List
from jinja2 import Template

HOST = "127.0.0.1"
PORT = 80
MAX_CONNECTIONS = 5
REQ_SIZE = 1024
HEBREW_ENCODING = "iso-8859-1" # An encoding that supports Hebrew on HTML)
CURRENT_STATE_DB = 'current_state.csv'
TRANSMISSION_LOG_DB = 'transmission_log.csv'
LOAD_STATS_DB = "load_stats.csv"
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
                        "Weekday",
                        "Date",
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
LOAD_STATS_FIELDS = [   "Location",
                        "Weekday",
                        "Start Time",
                        "End Time",
                        "Average",
                        "No. of Occurences",
                    ]
WEEKDAYS = [    "Sun",
                "Mon",
                "Tue",
                "Wed",
                "Thu",
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
        insert_to_csv(TRANSMISSION_LOG_DB, data_dict, TRANSMISSION_FIELDS, logger)

        # Update current state data:
        update_current_state(data_dict, logger)

        # Update load stats:
        update_load_stats(data_dict, logger)

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

def file_to_string_html(html: str, encoder: str=HEBREW_ENCODING, current_state: str=CURRENT_STATE_DB, stats: str=LOAD_STATS_DB) -> bytes:
    """ Recieves the filenames of the webpage's HTML, the 
        current state csv file and an encoder, build the html
        according to the current state in the studyrooms, and
        returns the HTML as a binary stream with the 
        requested encoding.
        Writes to the logger if an error has occurred."""
    
    # Read current state DB:
    current_state_dicts = []
    try:
        with open(current_state, 'r', newline='') as cs:
            reader = csv.DictReader(cs)
            for d in reader: current_state_dicts.append(d)
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {current_state}.")
    
    # Read load stats DB:
    load_stats_dicts = []
    try:
        with open(stats, 'r', newline='') as ls:
            reader = csv.DictReader(ls)
            for d in reader: load_stats_dicts.append(d)
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {stats}.")
    
    # Read webpage file HTML:
    try:
        with open(html, 'r', encoding=encoder) as f:
            buffer = f.read()
            tm = Template(buffer)

            # Create a new dict in which each item is {Location: *Ratio between current amount and max amount*}
            ratio_dict = {}
            for d in current_state_dicts:
                ratio_dict[d['Location']] = int(d['Current Amount']) / int(d['Max Amount'])
            
            sub = str(tm.render(HarmanScienceLibraryFloor2LoudP = str(int(ratio_dict["Harman Science Library - Floor 2 (Loud)"] * 100)),
                                HarmanScienceLibraryFloor2LoudD = str(int(ratio_dict["Harman Science Library - Floor 2 (Loud)"] * 180)),
                                HarmanScienceLibraryFloor2QuietP = str(int(ratio_dict["Harman Science Library - Floor 2 (Quiet)"] * 100)),
                                HarmanScienceLibraryFloor2QuietD = str(int(ratio_dict["Harman Science Library - Floor 2 (Quiet)"] * 180)),
                                HarmanScienceLibraryFloor_1P = str(int(ratio_dict["Harman Science Library - Floor -1"] * 100)),
                                HarmanScienceLibraryFloor_1D = str(int(ratio_dict["Harman Science Library - Floor -1"] * 180)),
                                CSEAquariumC100P = str(int(ratio_dict["CSE Aquarium C100"] * 100)),
                                CSEAquariumC100D = str(int(ratio_dict["CSE Aquarium C100"] * 180)),
                                CSEAquariumB100P = str(int(ratio_dict["CSE Aquarium B100"] * 100)),
                                CSEAquariumB100D = str(int(ratio_dict["CSE Aquarium B100"] * 180)),
                                CSEAquariumA100P = str(int(ratio_dict["CSE Aquarium A100"] * 100)),
                                CSEAquariumA100D = str(int(ratio_dict["CSE Aquarium A100"] * 180)),
                                EinsteinInstituteMathLibraryP = str(int(ratio_dict["Einstein Institute Math Library"] * 100)),
                                EinsteinInstituteMathLibraryD = str(int(ratio_dict["Einstein Institute Math Library"] * 180)),
                                )
                    )
            return sub.encode(encoder)
    except IOError:
        logger.error(f"An I/O error has occurred when opening {html}.")

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

def create_csv(filename: str, headers: str, logger: logging.Logger) -> None:
    """ Receives a filename and headers and creates a csv 
        file with the desired headers."""
    try:
        with open(filename, 'w', newline="") as db:
            w = csv.DictWriter(db, fieldnames=headers)
            w.writeheader()
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {filename}.")

def insert_to_csv(filename: str, data_dict: Dict, fields: List[str], logger: logging.Logger) -> None:
    """ Recieves the filename of a csv file, a dictionary, a 
        list of fields and a logger, and appends the 
        corresponding values of the csv fields in a new row 
        in the csv file.
        Writes to the logger if an error has occurred.
        """
    try:
        with open(filename, 'a', newline='') as db:
            writer = csv.DictWriter(db, fieldnames=fields)
            writer.writerow(data_dict)
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {filename}.")

def update_current_state(data_dict: Dict, logger: logging.Logger, filename: str=CURRENT_STATE_DB) -> None:
    ''' Recieves a dictionary dataset sent from a sensor,
        the server's logger, then updates the current status 
        in the file.
        Writes to the logger if an error has occurred.'''
    
    # Read current state DB:
    current_state_dicts = []
    try:
        with open(filename, 'r', newline='') as db:
            reader = csv.DictReader(db)
            for d in reader: current_state_dicts.append(d)
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {filename}.")
    
    # Update the current state according to the new data:
    found = False
    for location_dict in current_state_dicts:
        if location_dict['Location'] == data_dict['Location']:
            location_dict['Current Amount'] = str(int(data_dict['Entrances']) - int(data_dict['Exits']))
            found = True
            break

    # Rewrite the DB if the new location was found:
    if found:
        create_csv(filename, CURRENT_STATE_FIELDS, logger)
        for d in current_state_dicts:
            insert_to_csv(filename, d, CURRENT_STATE_FIELDS, logger)
        # try:
        #     with open(filename, 'a', newline='') as db:
        #         writer = csv.DictWriter(db, fieldnames=CURRENT_STATE_FIELDS)
        #         for location_dict in current_state_dicts:  
        #             writer.writerow(location_dict)
        #     logger.info(f"Current state DB was updated according to sensor {data_dict['S.N.']}'s data.")

        # except IOError:
        #     logger.error(f"An I/O error has occurred when writing to {filename}.")
    
    # Else the new location wasn't found in the DB, notify error and stop running this function:  
    else:
        logger.error(f"Current state DB could not be updated according to sensor {data_dict['S.N.']}'s data, because the location name {data_dict['Location']} could not be found in {filename}.")

def update_load_stats(transmission: Dict, logger: logging.Logger, stats: str=LOAD_STATS_DB, current_state: str=CURRENT_STATE_DB) -> None:
    """ Recieves the sensor's transmission, the server's 
        logger, the load stats DB filename and the current
        state DB filename and updates the load average of the
        location and corresponding time interval mentioned in
        the transmission.
    """
    # Find current state of transmission's location:
    try:
        with open(current_state, 'r', newline='') as current_state_db:
            reader = csv.DictReader(current_state_db)
            for d in reader:
                if d['Location'] == transmission['Location']:
                    current_state_dict = d

        if current_state_dict is None:
            logger.error(f"The current state values of the location {transmission['Location']} was not found.")
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {current_state}.")

    # Read the load stats DB:
    load_stats_dicts = []
    try:
        with open(stats, 'r', newline='') as db:
            reader = csv.DictReader(db)
            for d in reader: load_stats_dicts.append(d)
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {stats}.")

    # Search for the right dictionary in load stats DB:
    found = False
    for stat_dict in load_stats_dicts: 
                # Search for a row with the same location and weekday, and a matching time interval:
                if  stat_dict['Location'] == transmission['Location'] and \
                    stat_dict['Weekday'] == transmission['Weekday'] and \
                    int(stat_dict['Start Time'].split(':')[0]) <= int(transmission['Time'].split(':')[0]) and \
                    int(stat_dict['End Time'].split(':')[0]) > int(transmission['Time'].split(':')[0]):
                        
                        average, n = float(stat_dict['Average']), int(stat_dict['No. of Occurences'])
                        cur_amount, total_amount = int(current_state_dict['Current Amount']), int(current_state_dict['Max Amount'])
                        # print(f"Current percentage = {(cur_amount / total_amount) * 100} %")
                        stat_dict['Average'] = str(round((average * n) / (n + 1) + (cur_amount / total_amount) * 100 / (n + 1), 2))
                        stat_dict['No. of Occurences'] = str(n + 1)
                        # print(f"Old average: {average}, new average: {stat_dict['Average']}, occurences: {stat_dict['No. of Occurences']}")
                        found = True
                        break

    # Rewrite load stats DB:
    if found:
        create_csv(stats, LOAD_STATS_FIELDS, logger)
        for d in load_stats_dicts:
            insert_to_csv(stats, d, LOAD_STATS_FIELDS, logger)

    # Else write an error in the logger:
    else:
        logger.error(f"The transmission of sensor {transmission['S.N.']} does not belong to the load stats DB.")

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

    create_csv(LOAD_STATS_DB, LOAD_STATS_FIELDS, logger)
    try:
        with open(LOAD_STATS_DB, 'a') as f:
            for location in LOCATION_LIST:
                for day in WEEKDAYS:
                    for hour in range(8, 20, 2):
                        f.write(f"{location},{day},{str(hour)}:00,{str(hour+2)}:00,0,0\n")
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {LOAD_STATS_DB}.")

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
