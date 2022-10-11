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
<html lang="en" scroll-behavior: smooth;>

    <head>
        <title>HUJI-Lib</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <!-- Favicon-->
        <link rel="icon" type="image/x-icon" href="assets/35872213.jpg">
        <!-- Bootstrap icons-->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.4.1/font/bootstrap-icons.css" rel="stylesheet">
        <!-- Core theme CSS-->
        <link href="css/styles.css" rel="stylesheet">

        <!--progress bar-->
        <style media="screen">
            .circle-wrap {
              margin: 80px auto;
              width: 150px;
              height: 100px;
              background: #fefcff;
              border-radius: 50%;  
            }  
            .circle-wrap .circle .mask,
            .circle-wrap .circle .fill {
              width: 150px;
              height: 150px;
              position: absolute;
              border-radius: 50%;
            }
            .circle-wrap .circle .mask {
              clip: rect(0px, 150px, 150px, 75px);
            }
            .circle-wrap .inside-circle {
              width: 122px;
              height: 122px;
              border-radius: 50%;
              background: white;
              line-height: 120px;
              text-align: center;
              margin-top: 14px;
              margin-left: 14px;
              position: absolute;
              z-index: 100;
              font-weight: 700;
              font-size: 2em;
            }
            .mask .fill {
              clip: rect(0px, 75px, 150px, 0px);
              background-color: #227ded;
            }
            .mask.full,
            .circle .fill {
              animation: fill ease-in-out 3s;
              transform: rotate(180deg);
            }
            @keyframes fill{0% {transform: rotate(0deg);}
              100% {transform: rotate(180deg);}
            }
            
            
            .accordion-button{align-items: center;}
        </style>
    </head>


    <body>
        <!-- Responsive navbar-->
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container px-lg-5">
                <a class="navbar-brand" href="#!"><i class="bi bi-book"></i>HUJI-Lib</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation"><span class="navbar-toggler-icon"></span></button>
                <div class="collapse navbar-collapse" id="navbarSupportedContent">
                    <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
                        <li class="nav-item"><a class="nav-link active" aria-current="page" href="#">Home</a></li>
                        <li class="nav-item"><a class="nav-link" href="#section1">current status & weakly statistics</a></li>
                        <li class="nav-item"><a class="nav-link" href="#!">reservations</a></li>
                        <li class="nav-item"><a class="nav-link" href="#!">alternative locations</a></li>
                    </ul>
                </div>
            </div>
        </nav>
        <!-- Header-->
        <header class="py-5">
            <div class="container px-lg-5" id="section0">
                <div class="p-4 p-lg-5 bg-light rounded-3 text-center">
                    <div class="m-4 m-lg-5">
                        <h1 class="display-5 fw-bold">welcome to <i class="bi bi-book"></i>HUJI-lib</h1>
                        <p class="fs-4">a platform created by students for students to help you find the right space to study around the campus</p>
                    </div>
                </div>
            </div>
        </header>
        <!-- locations-->
        <div class="container px-lg-5" id="section0">
          <div class="p-4 p-lg-5 bg-light rounded-3 text-center">
              <div class="m-4 m-lg-5">
                  <h3>available locations</h3>
                  <div class="container text-center">
                    <div class="row row-cols-3">
                      


                      <div class="col">
                        <div class="card" style="width: 18rem;">
                          <img src="assets/herman_library.jpg" class="card-img-top" style="height: 150px;">
                          <div class="card-body">
                            <h5 class="card-title">herman library</h5>
                            <div class="accordion" id="accordionPanelsStayOpenExample">
                              <div class="accordion-item">
                                <h2 class="accordion-header" id="panelsStayOpen-headingOne">
                                  <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#panelsStayOpen-collapseOne" aria-expanded="true" aria-controls="panelsStayOpen-collapseOne">
                                      קומה עליונה חדר מרכזי
                                  </button>
                                </h2>
                                <div id="panelsStayOpen-collapseOne" class="accordion-collapse collapse show" aria-labelledby="panelsStayOpen-headingOne">
                                  <div class="accordion-body">
                                    <!--progress bar herman-->
                                      <div class="circle-wrap">
                                          <div class="circle">
                                          <div class="mask full">
                                              <div class="fill"></div>
                                          </div>
                                          <div class="mask half">
                                              <div class="fill"></div>
                                          </div>
                                          <div class="inside-circle"> 100% </div>
                                          </div>
                                      </div> 
                                  </div>
                                </div>


                              </div>
                              <div class="accordion-item">
                                <h2 class="accordion-header" id="panelsStayOpen-headingTwo">
                                  <button class="accordion-button collapsed" type="button" data-bs-target="#panelsStayOpen-collapseTwo" aria-expanded="false" aria-controls="panelsStayOpen-collapseTwo">
                                      קומה עליונה חדר שקט
                                  </button>
                                </h2>
                                <div id="panelsStayOpen-collapseTwo" class="accordion-collapse collapse" aria-labelledby="panelsStayOpen-headingTwo">
                                  <div class="accordion-body">
                                      <p>coming soon</p>
                                  </div>
                                </div>
                              </div>
                              <div class="accordion-item">
                                <h2 class="accordion-header" id="panelsStayOpen-headingThree">
                                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#panelsStayOpen-collapseThree" aria-expanded="false" aria-controls="panelsStayOpen-collapseThree">
                                      קומה תחתונה חדר מרכזי
                                  </button>
                                </h2>
                                <div id="panelsStayOpen-collapseThree" class="accordion-collapse collapse" aria-labelledby="panelsStayOpen-headingThree">
                                  <div class="accordion-body">
                                      <p>coming soon</p>
                                  </div>
                                </div>
                              </div>
                              <div class="accordion-item">
                                <h2 class="accordion-header" id="panelsStayOpen-headingThree">
                                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#panelsStayOpen-collapseThree" aria-expanded="false" aria-controls="panelsStayOpen-collapseThree">
                                      קומה תחתונה חדר שקט
                                  </button>
                                </h2>
                                <div id="panelsStayOpen-collapseThree" class="accordion-collapse collapse" aria-labelledby="panelsStayOpen-headingThree">
                                  <div class="accordion-body">
                                      <p>coming soon</p>
                                  </div>
                                </div>
                              </div>
                            </div> 
                          </div>
                        </div>
                      </div>

                      <div class="col">
                        <div class="card" style="width: 18rem; ">
                          <img src="assets/mtmtyqh.jpg" class="card-img-top" style="height: 150px;">
                          <div class="card-body">
                            <h5 class="card-title">mathematics library</h5>
                            <div class="accordion" id="accordionPanelsStayOpenExample">
                              <div class="accordion-item">
                                <h2 class="accordion-header" id="panelsStayOpen-headingOne">
                                  <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#panelsStayOpen-collapseOne" aria-expanded="true" aria-controls="panelsStayOpen-collapseOne">
                                      קומה עליונה חדר מרכזי
                                  </button>
                                </h2>
                                <div id="panelsStayOpen-collapseOne" class="accordion-collapse collapse show" aria-labelledby="panelsStayOpen-headingOne">
                                  <div class="accordion-body">
                                    coming soon
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                              

                      <div class="col">
                        <div class="card" style="width: 18rem; ">
                          <img src="assets/aquarium.jpg" class="card-img-top" style="height: 150px;">
                          <div class="card-body">
                            <h5 class="card-title">the aquarium</h5>
                            <div class="accordion" id="accordionPanelsStayOpenExample">
                              <div class="accordion-item">
                                <h2 class="accordion-header" id="panelsStayOpen-headingOne">
                                  <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#panelsStayOpen-collapseOne" aria-expanded="true" aria-controls="panelsStayOpen-collapseOne">
                                      c100
                                  </button>
                                </h2>
                                <div id="panelsStayOpen-collapseOne" class="accordion-collapse collapse show" aria-labelledby="panelsStayOpen-headingOne">
                                  <div class="accordion-body">
                                    coming soon
                                  </div>



                                  <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#panelsStayOpen-collapseOne" aria-expanded="true" aria-controls="panelsStayOpen-collapseOne">
                                    c100
                                </button>
                              </h2>
                              <div id="panelsStayOpen-collapseOne" class="accordion-collapse collapse show" aria-labelledby="panelsStayOpen-headingOne">
                                <div class="accordion-body">
                                  coming soon
                                  
                                </div>
                                </div>
                              </div>
                            </div>
                        </div>
                      </div>
                  </div>
          </div>
        </div>
      </div>
    </div>
  </div>

        <section class="pt-4">
            <div class="container px-lg-5">
                
                <!-- Page Features-->
                <div class="row gx-lg-5" id="section1">
                    <div class="col-lg-6 col-xxl-4 mb-5" >
                        <div class="card bg-light border-0 h-100">
                            <div class="card-body text-center p-4 p-lg-5 pt-0 pt-lg-0">
                                <div class="feature bg-primary bg-gradient text-white rounded-3 mb-4 mt-n4"><i class="bi bi-compass-fill"></i></div>
                                <h2 class="fs-4 fw-bold">current state</h2>



                                                         
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-6 col-xxl-4 mb-5">
                        <div class="card bg-light border-0 h-100">
                            <div class="card-body text-center p-4 p-lg-5 pt-0 pt-lg-0">
                                <div class="feature bg-primary bg-gradient text-white rounded-3 mb-4 mt-n4"><i class="bi bi-bar-chart-fill"></i></div>
                                <h2 class="fs-4 fw-bold">weakly statistics</h2>
                                <!--weakly chart-->
                                
                                <div><i class="fas fa-chart-area me-1"></i>עומס במהלך השבוע</div>
                                    <div><canvas id="myAreaChart" width="100%" height="60"></canvas></div>  
                            </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        <!-- Footer-->
        <footer class="py-5 bg-dark">
            <div class="container"><p class="m-0 text-center text-white">Copyright &copy; Your Website 2022</p></div>
        </footer>
        <!-- Bootstrap core JS-->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <!-- Core theme JS-->
        <script src="js/scripts.js"></script>
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
        