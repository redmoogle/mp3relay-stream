import urllib.request as urlreq
import urllib
import socket
import threading
import time
clients = set()
buffer = None

url = "https://hitradio-maroc.ice.infomaniak.ch/hitradio-maroc-128.mp3"

def on_new_client(conn, addr):
    conn.send(bytes('HTTP/1.1 200 OK\r\n', 'utf-8')) # HTTP requests expect a 200 OK before any header or data
    conn.send(bytes("Content-Type: audio/mpeg\n\n", 'utf-8')) # Specify its a mp3 stream
    conn.send(buffer)

def bufferio():
    """
    Grabs the data from the url in extconn and broadcast it to all listening clients
    """
    extconn = urlreq.urlopen(url, timeout=60)
    to_remove = set()
    global buffer
    while(True):
        try:
            buffer = extconn.read(16384) # Read 16kb of data from the stream
        except ConnectionResetError:
            extconn = None
            while extconn == None:
                try:
                    time.sleep(5)
                    extconn = urlreq.urlopen(url, timeout=60)
                    buffer = extconn.read(16384)
                except urllib.error.URLError:
                    pass
        for c in clients: # broadcast to all clients
            try:
                c.send(buffer)
            except ConnectionAbortedError: # Client disconnected
                to_remove.add(c)
            except BrokenPipeError:
                to_remove.add(c)
        if len(to_remove) != 0:
            for c in to_remove:
                clients.remove(c)
            to_remove = set()

threading.Thread(target=bufferio).start()
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    addr, port = '0.0.0.0', 5222
    server_socket.bind((addr, port)) # Listen on localhost on port 5222
    server_socket.listen(50)
    print(f'listening to {addr} on port {port}')
    while True:
        conn, address = server_socket.accept()
        print("Connection from " + address[0] + ":" + str(address[1]))
        clients.add(conn)
        threading.Thread(target=on_new_client, kwargs={'conn': conn, 'addr': address}).start()