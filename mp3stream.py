from urllib.error import HTTPError, URLError
import urllib.request as urlreq
import socket
import threading
import time
import math
import logging
import mp3packet

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

clients = set()
to_add = set()
buffer = None
extconn = None
mp3_head = None
next = 0

url = "https://hitradio-maroc.ice.infomaniak.ch/hitradio-maroc-128.mp3"

def on_new_client(conn, addr):
    global to_add
    conn.send(bytes('HTTP/1.1 200 OK\r\n', 'utf-8')) # HTTP requests expect a 200 OK before any header or data
    conn.send(bytes("Content-Type: audio/mpeg\n\n", 'utf-8')) # Specify its a mp3 stream
    to_add.add(conn)

def reconnect():
    global extconn
    global mp3_head
    global next
    if(extconn):
        extconn.close()
        extconn = None
    syncs = 0 # Make sure we have the right header

    while extconn == None:
        try:
            extconn = urlreq.urlopen(url, timeout=60)
        except (HTTPError, URLError, ConnectionError) as err:
            logging.error(err)
            extconn = None
            time.sleep(5)

    logging.info("Waiting for MP3 Sync")
    packet = mp3packet.MP3Packet()
    while(syncs < 20):
        buffer = extconn.read(4) # Read the mp3 header
        header = "{:08b}".format(int(buffer[0:4].hex(), 16))
        if(header[0:11] == '11111111111'):
            packet.decode_from_hex(buffer)
            next = packet.next_header()
            mp3_head = buffer
            syncs += 1
        extconn.read(next-4) # This will mess up any invalid headers

    print(packet)

def bufferio():
    """
    Grabs the data from the url in extconn and broadcast it to all listening clients
    """
    to_remove = set()

    global buffer
    global clients
    global extconn
    global to_add
    global next

    reconnect()

    logging.info("Beginning MP3 Relay Playback")
    while(True):
        try:
            buffer = extconn.read(next) # Recieve 30 mp3 packets
            if(buffer == b""):
                logging.warn('Detecting empty data stream... Reconnecting')
                reconnect()
                continue
        except (HTTPError, ConnectionError, URLError) as err:
            logging.error(err)
            reconnect()
            continue

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