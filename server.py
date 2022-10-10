import socket

ALLOWED_HOSTS = ""
PORT = 80
MAX_CONNECTIONS = 5
REQ_SIZE = 1024

def build_webpage():
    page = \
        """
        <html>
            <head>

            </head>

            <body>

            </body>
        </html>
        """
    
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

    except:
        raise("Socket creation failed.")
        