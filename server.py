import logging
import csv
from ast import literal_eval
from http.server import HTTPServer, BaseHTTPRequestHandler
from os.path import splitext
from typing import Dict, List
from jinja2 import Template

HOST = "192.168.1.215"
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
                            "Harman Science Library - Floor 2 (Loud),0,100",
                            "Harman Science Library - Floor 2 (Quiet),0,50",
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
    
    # Read load stats DB and make a dictionary with the averages in load percentage:
    load_averages = {}
    try:
        with open(stats, 'r', newline='') as ls:
            reader = csv.DictReader(ls)
            for d in reader: 
                key = d['Location'].replace(" ","").replace("-",'_').replace('(','').replace(')','')
                key += d['Weekday']
                key += d['Start Time'].split(':')[0]
                value = d['Average']
                load_averages[key] = value
    except IOError:
        logger.error(f"An I/O error has occurred when writing to {stats}.")

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
                                CSEAquariumC100Sun8 = str(load_averages['CSEAquariumC100Sun8']),
                                CSEAquariumC100Sun10 = str(load_averages['CSEAquariumC100Sun10']),
                                CSEAquariumC100Sun12 = str(load_averages['CSEAquariumC100Sun12']),
                                CSEAquariumC100Sun14 = str(load_averages['CSEAquariumC100Sun14']),
                                CSEAquariumC100Sun16 = str(load_averages['CSEAquariumC100Sun16']),
                                CSEAquariumC100Sun18 = str(load_averages['CSEAquariumC100Sun18']),
                                CSEAquariumC100Mon8 = str(load_averages['CSEAquariumC100Mon8']),
                                CSEAquariumC100Mon10 = str(load_averages['CSEAquariumC100Mon10']),
                                CSEAquariumC100Mon12 = str(load_averages['CSEAquariumC100Mon12']),
                                CSEAquariumC100Mon14 = str(load_averages['CSEAquariumC100Mon14']),
                                CSEAquariumC100Mon16 = str(load_averages['CSEAquariumC100Mon16']),
                                CSEAquariumC100Mon18 = str(load_averages['CSEAquariumC100Mon18']),
                                CSEAquariumC100Tue8 = str(load_averages['CSEAquariumC100Tue8']),
                                CSEAquariumC100Tue10 = str(load_averages['CSEAquariumC100Tue10']),
                                CSEAquariumC100Tue12 = str(load_averages['CSEAquariumC100Tue12']),
                                CSEAquariumC100Tue14 = str(load_averages['CSEAquariumC100Tue14']),
                                CSEAquariumC100Tue16 = str(load_averages['CSEAquariumC100Tue16']),
                                CSEAquariumC100Tue18 = str(load_averages['CSEAquariumC100Tue18']),
                                CSEAquariumC100Wed8 = str(load_averages['CSEAquariumC100Wed8']),
                                CSEAquariumC100Wed10 = str(load_averages['CSEAquariumC100Wed10']),
                                CSEAquariumC100Wed12 = str(load_averages['CSEAquariumC100Wed12']),
                                CSEAquariumC100Wed14 = str(load_averages['CSEAquariumC100Wed14']),
                                CSEAquariumC100Wed16 = str(load_averages['CSEAquariumC100Wed16']),
                                CSEAquariumC100Wed18 = str(load_averages['CSEAquariumC100Wed18']),
                                CSEAquariumC100Thu8 = str(load_averages['CSEAquariumC100Thu8']),
                                CSEAquariumC100Thu10 = str(load_averages['CSEAquariumC100Thu10']),
                                CSEAquariumC100Thu12 = str(load_averages['CSEAquariumC100Thu12']),
                                CSEAquariumC100Thu14 = str(load_averages['CSEAquariumC100Thu14']),
                                CSEAquariumC100Thu16 = str(load_averages['CSEAquariumC100Thu16']),
                                CSEAquariumC100Thu18 = str(load_averages['CSEAquariumC100Thu18']),
                                CSEAquariumB100Sun8 = str(load_averages['CSEAquariumB100Sun8']),
                                CSEAquariumB100Sun10 = str(load_averages['CSEAquariumB100Sun10']),
                                CSEAquariumB100Sun12 = str(load_averages['CSEAquariumB100Sun12']),
                                CSEAquariumB100Sun14 = str(load_averages['CSEAquariumB100Sun14']),
                                CSEAquariumB100Sun16 = str(load_averages['CSEAquariumB100Sun16']),
                                CSEAquariumB100Sun18 = str(load_averages['CSEAquariumB100Sun18']),
                                CSEAquariumB100Mon8 = str(load_averages['CSEAquariumB100Mon8']),
                                CSEAquariumB100Mon10 = str(load_averages['CSEAquariumB100Mon10']),
                                CSEAquariumB100Mon12 = str(load_averages['CSEAquariumB100Mon12']),
                                CSEAquariumB100Mon14 = str(load_averages['CSEAquariumB100Mon14']),
                                CSEAquariumB100Mon16 = str(load_averages['CSEAquariumB100Mon16']),
                                CSEAquariumB100Mon18 = str(load_averages['CSEAquariumB100Mon18']),
                                CSEAquariumB100Tue8 = str(load_averages['CSEAquariumB100Tue8']),
                                CSEAquariumB100Tue10 = str(load_averages['CSEAquariumB100Tue10']),
                                CSEAquariumB100Tue12 = str(load_averages['CSEAquariumB100Tue12']),
                                CSEAquariumB100Tue14 = str(load_averages['CSEAquariumB100Tue14']),
                                CSEAquariumB100Tue16 = str(load_averages['CSEAquariumB100Tue16']),
                                CSEAquariumB100Tue18 = str(load_averages['CSEAquariumB100Tue18']),
                                CSEAquariumB100Wed8 = str(load_averages['CSEAquariumB100Wed8']),
                                CSEAquariumB100Wed10 = str(load_averages['CSEAquariumB100Wed10']),
                                CSEAquariumB100Wed12 = str(load_averages['CSEAquariumB100Wed12']),
                                CSEAquariumB100Wed14 = str(load_averages['CSEAquariumB100Wed14']),
                                CSEAquariumB100Wed16 = str(load_averages['CSEAquariumB100Wed16']),
                                CSEAquariumB100Wed18 = str(load_averages['CSEAquariumB100Wed18']),
                                CSEAquariumB100Thu8 = str(load_averages['CSEAquariumB100Thu8']),
                                CSEAquariumB100Thu10 = str(load_averages['CSEAquariumB100Thu10']),
                                CSEAquariumB100Thu12 = str(load_averages['CSEAquariumB100Thu12']),
                                CSEAquariumB100Thu14 = str(load_averages['CSEAquariumB100Thu14']),
                                CSEAquariumB100Thu16 = str(load_averages['CSEAquariumB100Thu16']),
                                CSEAquariumB100Thu18 = str(load_averages['CSEAquariumB100Thu18']),
                                CSEAquariumA100Sun8 = str(load_averages['CSEAquariumA100Sun8']),
                                CSEAquariumA100Sun10 = str(load_averages['CSEAquariumA100Sun10']),
                                CSEAquariumA100Sun12 = str(load_averages['CSEAquariumA100Sun12']),
                                CSEAquariumA100Sun14 = str(load_averages['CSEAquariumA100Sun14']),
                                CSEAquariumA100Sun16 = str(load_averages['CSEAquariumA100Sun16']),
                                CSEAquariumA100Sun18 = str(load_averages['CSEAquariumA100Sun18']),
                                CSEAquariumA100Mon8 = str(load_averages['CSEAquariumA100Mon8']),
                                CSEAquariumA100Mon10 = str(load_averages['CSEAquariumA100Mon10']),
                                CSEAquariumA100Mon12 = str(load_averages['CSEAquariumA100Mon12']),
                                CSEAquariumA100Mon14 = str(load_averages['CSEAquariumA100Mon14']),
                                CSEAquariumA100Mon16 = str(load_averages['CSEAquariumA100Mon16']),
                                CSEAquariumA100Mon18 = str(load_averages['CSEAquariumA100Mon18']),
                                CSEAquariumA100Tue8 = str(load_averages['CSEAquariumA100Tue8']),
                                CSEAquariumA100Tue10 = str(load_averages['CSEAquariumA100Tue10']),
                                CSEAquariumA100Tue12 = str(load_averages['CSEAquariumA100Tue12']),
                                CSEAquariumA100Tue14 = str(load_averages['CSEAquariumA100Tue14']),
                                CSEAquariumA100Tue16 = str(load_averages['CSEAquariumA100Tue16']),
                                CSEAquariumA100Tue18 = str(load_averages['CSEAquariumA100Tue18']),
                                CSEAquariumA100Wed8 = str(load_averages['CSEAquariumA100Wed8']),
                                CSEAquariumA100Wed10 = str(load_averages['CSEAquariumA100Wed10']),
                                CSEAquariumA100Wed12 = str(load_averages['CSEAquariumA100Wed12']),
                                CSEAquariumA100Wed14 = str(load_averages['CSEAquariumA100Wed14']),
                                CSEAquariumA100Wed16 = str(load_averages['CSEAquariumA100Wed16']),
                                CSEAquariumA100Wed18 = str(load_averages['CSEAquariumA100Wed18']),
                                CSEAquariumA100Thu8 = str(load_averages['CSEAquariumA100Thu8']),
                                CSEAquariumA100Thu10 = str(load_averages['CSEAquariumA100Thu10']),
                                CSEAquariumA100Thu12 = str(load_averages['CSEAquariumA100Thu12']),
                                CSEAquariumA100Thu14 = str(load_averages['CSEAquariumA100Thu14']),
                                CSEAquariumA100Thu16 = str(load_averages['CSEAquariumA100Thu16']),
                                CSEAquariumA100Thu18 = str(load_averages['CSEAquariumA100Thu18']),
                                EinsteinInstituteMathLibrarySun8 = str(load_averages['EinsteinInstituteMathLibrarySun8']),
                                EinsteinInstituteMathLibrarySun10 = str(load_averages['EinsteinInstituteMathLibrarySun10']),
                                EinsteinInstituteMathLibrarySun12 = str(load_averages['EinsteinInstituteMathLibrarySun12']),
                                EinsteinInstituteMathLibrarySun14 = str(load_averages['EinsteinInstituteMathLibrarySun14']),
                                EinsteinInstituteMathLibrarySun16 = str(load_averages['EinsteinInstituteMathLibrarySun16']),
                                EinsteinInstituteMathLibrarySun18 = str(load_averages['EinsteinInstituteMathLibrarySun18']),
                                EinsteinInstituteMathLibraryMon8 = str(load_averages['EinsteinInstituteMathLibraryMon8']),
                                EinsteinInstituteMathLibraryMon10 = str(load_averages['EinsteinInstituteMathLibraryMon10']),
                                EinsteinInstituteMathLibraryMon12 = str(load_averages['EinsteinInstituteMathLibraryMon12']),
                                EinsteinInstituteMathLibraryMon14 = str(load_averages['EinsteinInstituteMathLibraryMon14']),
                                EinsteinInstituteMathLibraryMon16 = str(load_averages['EinsteinInstituteMathLibraryMon16']),
                                EinsteinInstituteMathLibraryMon18 = str(load_averages['EinsteinInstituteMathLibraryMon18']),
                                EinsteinInstituteMathLibraryTue8 = str(load_averages['EinsteinInstituteMathLibraryTue8']),
                                EinsteinInstituteMathLibraryTue10 = str(load_averages['EinsteinInstituteMathLibraryTue10']),
                                EinsteinInstituteMathLibraryTue12 = str(load_averages['EinsteinInstituteMathLibraryTue12']),
                                EinsteinInstituteMathLibraryTue14 = str(load_averages['EinsteinInstituteMathLibraryTue14']),
                                EinsteinInstituteMathLibraryTue16 = str(load_averages['EinsteinInstituteMathLibraryTue16']),
                                EinsteinInstituteMathLibraryTue18 = str(load_averages['EinsteinInstituteMathLibraryTue18']),
                                EinsteinInstituteMathLibraryWed8 = str(load_averages['EinsteinInstituteMathLibraryWed8']),
                                EinsteinInstituteMathLibraryWed10 = str(load_averages['EinsteinInstituteMathLibraryWed10']),
                                EinsteinInstituteMathLibraryWed12 = str(load_averages['EinsteinInstituteMathLibraryWed12']),
                                EinsteinInstituteMathLibraryWed14 = str(load_averages['EinsteinInstituteMathLibraryWed14']),
                                EinsteinInstituteMathLibraryWed16 = str(load_averages['EinsteinInstituteMathLibraryWed16']),
                                EinsteinInstituteMathLibraryWed18 = str(load_averages['EinsteinInstituteMathLibraryWed18']),
                                EinsteinInstituteMathLibraryThu8 = str(load_averages['EinsteinInstituteMathLibraryThu8']),
                                EinsteinInstituteMathLibraryThu10 = str(load_averages['EinsteinInstituteMathLibraryThu10']),
                                EinsteinInstituteMathLibraryThu12 = str(load_averages['EinsteinInstituteMathLibraryThu12']),
                                EinsteinInstituteMathLibraryThu14 = str(load_averages['EinsteinInstituteMathLibraryThu14']),
                                EinsteinInstituteMathLibraryThu16 = str(load_averages['EinsteinInstituteMathLibraryThu16']),
                                EinsteinInstituteMathLibraryThu18 = str(load_averages['EinsteinInstituteMathLibraryThu18']),
                                HarmanScienceLibrary_Floor2QuietSun8 = str(load_averages['HarmanScienceLibrary_Floor2QuietSun8']),
                                HarmanScienceLibrary_Floor2QuietSun10 = str(load_averages['HarmanScienceLibrary_Floor2QuietSun10']),
                                HarmanScienceLibrary_Floor2QuietSun12 = str(load_averages['HarmanScienceLibrary_Floor2QuietSun12']),
                                HarmanScienceLibrary_Floor2QuietSun14 = str(load_averages['HarmanScienceLibrary_Floor2QuietSun14']),
                                HarmanScienceLibrary_Floor2QuietSun16 = str(load_averages['HarmanScienceLibrary_Floor2QuietSun16']),
                                HarmanScienceLibrary_Floor2QuietSun18 = str(load_averages['HarmanScienceLibrary_Floor2QuietSun18']),
                                HarmanScienceLibrary_Floor2QuietMon8 = str(load_averages['HarmanScienceLibrary_Floor2QuietMon8']),
                                HarmanScienceLibrary_Floor2QuietMon10 = str(load_averages['HarmanScienceLibrary_Floor2QuietMon10']),
                                HarmanScienceLibrary_Floor2QuietMon12 = str(load_averages['HarmanScienceLibrary_Floor2QuietMon12']),
                                HarmanScienceLibrary_Floor2QuietMon14 = str(load_averages['HarmanScienceLibrary_Floor2QuietMon14']),
                                HarmanScienceLibrary_Floor2QuietMon16 = str(load_averages['HarmanScienceLibrary_Floor2QuietMon16']),
                                HarmanScienceLibrary_Floor2QuietMon18 = str(load_averages['HarmanScienceLibrary_Floor2QuietMon18']),
                                HarmanScienceLibrary_Floor2QuietTue8 = str(load_averages['HarmanScienceLibrary_Floor2QuietTue8']),
                                HarmanScienceLibrary_Floor2QuietTue10 = str(load_averages['HarmanScienceLibrary_Floor2QuietTue10']),
                                HarmanScienceLibrary_Floor2QuietTue12 = str(load_averages['HarmanScienceLibrary_Floor2QuietTue12']),
                                HarmanScienceLibrary_Floor2QuietTue14 = str(load_averages['HarmanScienceLibrary_Floor2QuietTue14']),
                                HarmanScienceLibrary_Floor2QuietTue16 = str(load_averages['HarmanScienceLibrary_Floor2QuietTue16']),
                                HarmanScienceLibrary_Floor2QuietTue18 = str(load_averages['HarmanScienceLibrary_Floor2QuietTue18']),
                                HarmanScienceLibrary_Floor2QuietWed8 = str(load_averages['HarmanScienceLibrary_Floor2QuietWed8']),
                                HarmanScienceLibrary_Floor2QuietWed10 = str(load_averages['HarmanScienceLibrary_Floor2QuietWed10']),
                                HarmanScienceLibrary_Floor2QuietWed12 = str(load_averages['HarmanScienceLibrary_Floor2QuietWed12']),
                                HarmanScienceLibrary_Floor2QuietWed14 = str(load_averages['HarmanScienceLibrary_Floor2QuietWed14']),
                                HarmanScienceLibrary_Floor2QuietWed16 = str(load_averages['HarmanScienceLibrary_Floor2QuietWed16']),
                                HarmanScienceLibrary_Floor2QuietWed18 = str(load_averages['HarmanScienceLibrary_Floor2QuietWed18']),
                                HarmanScienceLibrary_Floor2QuietThu8 = str(load_averages['HarmanScienceLibrary_Floor2QuietThu8']),
                                HarmanScienceLibrary_Floor2QuietThu10 = str(load_averages['HarmanScienceLibrary_Floor2QuietThu10']),
                                HarmanScienceLibrary_Floor2QuietThu12 = str(load_averages['HarmanScienceLibrary_Floor2QuietThu12']),
                                HarmanScienceLibrary_Floor2QuietThu14 = str(load_averages['HarmanScienceLibrary_Floor2QuietThu14']),
                                HarmanScienceLibrary_Floor2QuietThu16 = str(load_averages['HarmanScienceLibrary_Floor2QuietThu16']),
                                HarmanScienceLibrary_Floor2QuietThu18 = str(load_averages['HarmanScienceLibrary_Floor2QuietThu18']),
                                HarmanScienceLibrary_Floor2LoudSun8 = str(load_averages['HarmanScienceLibrary_Floor2LoudSun8']),
                                HarmanScienceLibrary_Floor2LoudSun10 = str(load_averages['HarmanScienceLibrary_Floor2LoudSun10']),
                                HarmanScienceLibrary_Floor2LoudSun12 = str(load_averages['HarmanScienceLibrary_Floor2LoudSun12']),
                                HarmanScienceLibrary_Floor2LoudSun14 = str(load_averages['HarmanScienceLibrary_Floor2LoudSun14']),
                                HarmanScienceLibrary_Floor2LoudSun16 = str(load_averages['HarmanScienceLibrary_Floor2LoudSun16']),
                                HarmanScienceLibrary_Floor2LoudSun18 = str(load_averages['HarmanScienceLibrary_Floor2LoudSun18']),
                                HarmanScienceLibrary_Floor2LoudMon8 = str(load_averages['HarmanScienceLibrary_Floor2LoudMon8']),
                                HarmanScienceLibrary_Floor2LoudMon10 = str(load_averages['HarmanScienceLibrary_Floor2LoudMon10']),
                                HarmanScienceLibrary_Floor2LoudMon12 = str(load_averages['HarmanScienceLibrary_Floor2LoudMon12']),
                                HarmanScienceLibrary_Floor2LoudMon14 = str(load_averages['HarmanScienceLibrary_Floor2LoudMon14']),
                                HarmanScienceLibrary_Floor2LoudMon16 = str(load_averages['HarmanScienceLibrary_Floor2LoudMon16']),
                                HarmanScienceLibrary_Floor2LoudMon18 = str(load_averages['HarmanScienceLibrary_Floor2LoudMon18']),
                                HarmanScienceLibrary_Floor2LoudTue8 = str(load_averages['HarmanScienceLibrary_Floor2LoudTue8']),
                                HarmanScienceLibrary_Floor2LoudTue10 = str(load_averages['HarmanScienceLibrary_Floor2LoudTue10']),
                                HarmanScienceLibrary_Floor2LoudTue12 = str(load_averages['HarmanScienceLibrary_Floor2LoudTue12']),
                                HarmanScienceLibrary_Floor2LoudTue14 = str(load_averages['HarmanScienceLibrary_Floor2LoudTue14']),
                                HarmanScienceLibrary_Floor2LoudTue16 = str(load_averages['HarmanScienceLibrary_Floor2LoudTue16']),
                                HarmanScienceLibrary_Floor2LoudTue18 = str(load_averages['HarmanScienceLibrary_Floor2LoudTue18']),
                                HarmanScienceLibrary_Floor2LoudWed8 = str(load_averages['HarmanScienceLibrary_Floor2LoudWed8']),
                                HarmanScienceLibrary_Floor2LoudWed10 = str(load_averages['HarmanScienceLibrary_Floor2LoudWed10']),
                                HarmanScienceLibrary_Floor2LoudWed12 = str(load_averages['HarmanScienceLibrary_Floor2LoudWed12']),
                                HarmanScienceLibrary_Floor2LoudWed14 = str(load_averages['HarmanScienceLibrary_Floor2LoudWed14']),
                                HarmanScienceLibrary_Floor2LoudWed16 = str(load_averages['HarmanScienceLibrary_Floor2LoudWed16']),
                                HarmanScienceLibrary_Floor2LoudWed18 = str(load_averages['HarmanScienceLibrary_Floor2LoudWed18']),
                                HarmanScienceLibrary_Floor2LoudThu8 = str(load_averages['HarmanScienceLibrary_Floor2LoudThu8']),
                                HarmanScienceLibrary_Floor2LoudThu10 = str(load_averages['HarmanScienceLibrary_Floor2LoudThu10']),
                                HarmanScienceLibrary_Floor2LoudThu12 = str(load_averages['HarmanScienceLibrary_Floor2LoudThu12']),
                                HarmanScienceLibrary_Floor2LoudThu14 = str(load_averages['HarmanScienceLibrary_Floor2LoudThu14']),
                                HarmanScienceLibrary_Floor2LoudThu16 = str(load_averages['HarmanScienceLibrary_Floor2LoudThu16']),
                                HarmanScienceLibrary_Floor2LoudThu18 = str(load_averages['HarmanScienceLibrary_Floor2LoudThu18']),
                                HarmanScienceLibrary_Floor_1Sun8 = str(load_averages['HarmanScienceLibrary_Floor_1Sun8']),
                                HarmanScienceLibrary_Floor_1Sun10 = str(load_averages['HarmanScienceLibrary_Floor_1Sun10']),
                                HarmanScienceLibrary_Floor_1Sun12 = str(load_averages['HarmanScienceLibrary_Floor_1Sun12']),
                                HarmanScienceLibrary_Floor_1Sun14 = str(load_averages['HarmanScienceLibrary_Floor_1Sun14']),
                                HarmanScienceLibrary_Floor_1Sun16 = str(load_averages['HarmanScienceLibrary_Floor_1Sun16']),
                                HarmanScienceLibrary_Floor_1Sun18 = str(load_averages['HarmanScienceLibrary_Floor_1Sun18']),
                                HarmanScienceLibrary_Floor_1Mon8 = str(load_averages['HarmanScienceLibrary_Floor_1Mon8']),
                                HarmanScienceLibrary_Floor_1Mon10 = str(load_averages['HarmanScienceLibrary_Floor_1Mon10']),
                                HarmanScienceLibrary_Floor_1Mon12 = str(load_averages['HarmanScienceLibrary_Floor_1Mon12']),
                                HarmanScienceLibrary_Floor_1Mon14 = str(load_averages['HarmanScienceLibrary_Floor_1Mon14']),
                                HarmanScienceLibrary_Floor_1Mon16 = str(load_averages['HarmanScienceLibrary_Floor_1Mon16']),
                                HarmanScienceLibrary_Floor_1Mon18 = str(load_averages['HarmanScienceLibrary_Floor_1Mon18']),
                                HarmanScienceLibrary_Floor_1Tue8 = str(load_averages['HarmanScienceLibrary_Floor_1Tue8']),
                                HarmanScienceLibrary_Floor_1Tue10 = str(load_averages['HarmanScienceLibrary_Floor_1Tue10']),
                                HarmanScienceLibrary_Floor_1Tue12 = str(load_averages['HarmanScienceLibrary_Floor_1Tue12']),
                                HarmanScienceLibrary_Floor_1Tue14 = str(load_averages['HarmanScienceLibrary_Floor_1Tue14']),
                                HarmanScienceLibrary_Floor_1Tue16 = str(load_averages['HarmanScienceLibrary_Floor_1Tue16']),
                                HarmanScienceLibrary_Floor_1Tue18 = str(load_averages['HarmanScienceLibrary_Floor_1Tue18']),
                                HarmanScienceLibrary_Floor_1Wed8 = str(load_averages['HarmanScienceLibrary_Floor_1Wed8']),
                                HarmanScienceLibrary_Floor_1Wed10 = str(load_averages['HarmanScienceLibrary_Floor_1Wed10']),
                                HarmanScienceLibrary_Floor_1Wed12 = str(load_averages['HarmanScienceLibrary_Floor_1Wed12']),
                                HarmanScienceLibrary_Floor_1Wed14 = str(load_averages['HarmanScienceLibrary_Floor_1Wed14']),
                                HarmanScienceLibrary_Floor_1Wed16 = str(load_averages['HarmanScienceLibrary_Floor_1Wed16']),
                                HarmanScienceLibrary_Floor_1Wed18 = str(load_averages['HarmanScienceLibrary_Floor_1Wed18']),
                                HarmanScienceLibrary_Floor_1Thu8 = str(load_averages['HarmanScienceLibrary_Floor_1Thu8']),
                                HarmanScienceLibrary_Floor_1Thu10 = str(load_averages['HarmanScienceLibrary_Floor_1Thu10']),
                                HarmanScienceLibrary_Floor_1Thu12 = str(load_averages['HarmanScienceLibrary_Floor_1Thu12']),
                                HarmanScienceLibrary_Floor_1Thu14 = str(load_averages['HarmanScienceLibrary_Floor_1Thu14']),
                                HarmanScienceLibrary_Floor_1Thu16 = str(load_averages['HarmanScienceLibrary_Floor_1Thu16']),
                                HarmanScienceLibrary_Floor_1Thu18 = str(load_averages['HarmanScienceLibrary_Floor_1Thu18']),
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
