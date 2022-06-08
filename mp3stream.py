import urllib.request as urlreq
import urllib
import socket
import threading
import time
import datetime

clients = set()
to_add = set()
buffer = None

buffertime = datetime.datetime.now()
changeovertime = buffertime+datetime.timedelta(0,30)

url = "LINK"

def on_new_client(conn, addr):
    global to_add
    conn.send(bytes('HTTP/1.1 200 OK\r\n', 'utf-8')) # HTTP requests expect a 200 OK before any header or data
    conn.send(bytes("Content-Type: audio/mpeg\n\n", 'utf-8')) # Specify its a mp3 stream
    conn.send(buffer)
    to_add.add(conn)

def bufferio():
    """
    Grabs the data from the url in extconn and broadcast it to all listening clients
    """
    extconn = urlreq.urlopen(url, timeout=60)
    to_remove = set()

    global buffer
    global clients
    global to_add

    while(True):
        try:
            buffer = extconn.read(16384) # Read 16kb of data from the stream
            if(datetime.datetime.now() > changeovertime):
                _tmpconn = urlreq.urlopen(url, timeout=60)
                extconn.close()
                extconn = _tmpconn
                print('Switched Streams')
        except ConnectionResetError:
            print("A connection reset error has occured. Attempting to reconnect.")
            extconn = None
            while extconn == None:
                try:
                    time.sleep(5)
                    extconn = urlreq.urlopen(url, timeout=60)
                    buffer = extconn.read(16384)
                except urllib.error.URLError as exc:
                    print(f"URL Error: {exc}")

        if len(to_add) != 0:
            for c in to_add:
                clients.add(conn)
            to_add = set()

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
        threading.Thread(target=on_new_client, kwargs={'conn': conn, 'addr': address}).start()