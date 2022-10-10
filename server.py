import socket

ALLOWED_HOSTS = ""
PORT = 80
MAX_CONNECTIONS = 5
REQ_SIZE = 1024

def build_webpage():
    led_state = 1
    page = """
    <html>   
      <head>   
       <meta content="width=device-width, initial-scale=1" name="viewport"></meta>   
      </head>   
      <body>   
        <center><h2>ESP32 Web Server in MicroPython </h2></center>   
        <center>   
         <form>   
          <button name="LED" type="submit" value="1"> LED ON </button>   
          <button name="LED" type="submit" value="0"> LED OFF </button>   
         </form>   
        </center>   
        <center><p>LED is now <strong>""" + str(led_state) + """</strong>.</p></center>   
      </body>   
    </html>"""

    # page = \
    #     """s
    #     <html>
    #         <head>

    #         </head>

    #         <body>

    #         </body>
    #     </html>
    #     """
    
    return page

if __name__ == '__main__':
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as est_sock:
            # Establish a connection with a socket designated only for making connections:
            try:
                est_sock.bind((ALLOWED_HOSTS, PORT))
                est_sock.listen(MAX_CONNECTIONS)
            except:
                raise("Socket bind or listening failed.")

            while(True):
                # Create a new socket with a client, and save client's address:
                cli_sock, cli_addr = est_sock.accept()

                # Recieve request:
                req = cli_sock.recv(REQ_SIZE)
                req = str(req)
                print(f"\nRequest:\n {req}\n\n\n")

                # Send response:
                res = build_webpage().encode()
                cli_sock.send(b'HTTP/1.1 200 OK\n')
                cli_sock.send(b'Content-Type: text/html\n')
                cli_sock.send(b'Connection: close\n\n')
                cli_sock.sendall(res)

                # Close client socket:
                cli_sock.close()


    except:
        raise("Socket creation failed.")
        