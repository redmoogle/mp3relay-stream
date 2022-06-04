
import urllib.request as urlreq
import socket
import threading
clients = set()

extconn = urlreq.urlopen('STREAMLINK', timeout=60)

def on_new_client(conn, addr):
    conn.send(bytes('HTTP/1.1 200 OK\r\n', 'utf-8')) # HTTP requests expect a 200 OK before any header or data
    conn.send(bytes("Content-Type: audio/mpeg\n\n", 'utf-8')) # Specify its a mp3 stream

def bufferio():
    """
    Grabs the data from the url in extconn and broadcast it to all listening clients
    """
    to_remove = set()
    buffer = None
    while(True):
        buffer = extconn.read(16384) # Read 16kb of data from the stream
        for c in clients: # broadcast to all clients
            try:
                c.send(buffer)
            except ConnectionAbortedError: # Client disconnected
                to_remove.add(c)
        if len(to_remove) != 0:
            for c in to_remove:
                _tmp = c.getpeername()
                print("Disconnection from " + _tmp[0]+":"+str(_tmp[1]))
                clients.remove(c)
            to_remove = set()

threading.Thread(target=bufferio).start()
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind(("127.0.0.1", 5222)) # Listen on localhost on port 5222
    server_socket.listen(50)
    while True:
        conn, address = server_socket.accept()
        print("Connection from " + address[0] + ":" + str(address[1]))
        clients.add(conn)
        threading.Thread(target=on_new_client, kwargs={'conn': conn, 'addr': address}).start()