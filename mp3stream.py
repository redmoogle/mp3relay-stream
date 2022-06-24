from urllib.error import HTTPError, URLError
import urllib.request as urlreq
import socket
import threading
import time
import logging
import mp3packet
import subprocess

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

clients = set()
to_add = set()
to_remove = set()
buffer = None
extconn = None
head = None
next = 0

url = "https://hitradio-maroc.ice.infomaniak.ch/hitradio-maroc-128.mp3"

# MP3 Chunks to OPUS Chunks
cmd = "ffmpeg -i stream.mp3 -b:a 48k processed.opus"

def on_new_client(conn, addr):
    global to_add
    conn.send(bytes('HTTP/1.1 200 OK\r\n', 'utf-8')) # HTTP requests expect a 200 OK before any header or data
    conn.send(bytes("Content-Type: audio/opus\n\n", 'utf-8')) # Specify its a mp3 stream
    to_add.add(conn)

def reconnect():
    global extconn
    global next
    global head

    if(extconn):
        extconn.close()
        extconn = None
    syncs = 0 # Make sure we have the right header

    while extconn == None:
        try:
            extconn = urlreq.urlopen(url, timeout=5)
        except (HTTPError, URLError, ConnectionError, TimeoutError) as err:
            logging.error(err)
            time.sleep(3)
            extconn = None
            if(head):
                handle_clients(packet.header()+(b"\00"*(next-4))) # Send some fake data

    logging.info("Waiting for MP3 Sync")
    packet = mp3packet.MP3Packet()
    while(syncs < 5):
        buffer = extconn.read(4) # Read the mp3 header
        if packet.IsHeader(buffer):
            packet.decode_from_hex(buffer)
            next = packet.next_header()
            time.sleep(0.05) # Buffer depletion prevention
            extconn.read(next-4)
            buffer = extconn.read(4)
            if packet.IsHeader(buffer):
                packet.decode_from_hex(buffer)
                next = packet.next_header()
                syncs += 1
                extconn.read(next-4)
                if(head):
                    handle_clients(packet.header()+(b"\00"*(next-4))) # Send some fake data
    print(packet)

def handle_clients(data):
    global clients
    global to_add
    global to_remove

    if len(to_add) != 0:
        for c in to_add:
            clients.add(c)
        to_add = set()

    for c in clients: # broadcast to all clients
        try:
            c.send(data)
        except (ConnectionAbortedError, BrokenPipeError): # Client disconnected
            to_remove.add(c)

    if len(to_remove) != 0:
        for c in to_remove:
            clients.remove(c)
            logging.info('Disconnection')
        to_remove = set()


def bufferio():
    """
    Grabs the data from the url in extconn and broadcast it to all listening clients
    """
    global buffer
    global extconn

    reconnect()

    logging.info("Beginning MP3 Relay Playback")
    while(True):
        try:
            buffer = extconn.read(next*45) # Recieve a mp3 packet
            if(buffer == b""):
                logging.warning('Detecting empty data stream... Reconnecting')
                reconnect()
                continue
        except (HTTPError, ConnectionError, URLError, TimeoutError) as err:
            logging.error(err)
            reconnect()
            continue

        with open("stream.mp3", "wb+") as filebuffer:
            filebuffer.write(buffer)
        subprocess.Popen([cmd], shell=True).wait()
        with open("processed.opus", "rb") as filebuffer:
            handle_clients(filebuffer.read())

def relay_start():
    iothread = threading.Thread(target=bufferio)
    iothread.daemon = True
    iothread.start()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        addr, port = '127.0.0.1', 5222
        server_socket.bind((addr, port)) # Listen on localhost on port 5222
        server_socket.listen(5)
        server_socket.settimeout(0.5)
        print(f'listening to {addr} on port {port}')
        while True:
            try:
                conn, address = server_socket.accept()
                logging.info("Connection from " + address[0] + ":" + str(address[1]))
                thread = threading.Thread(target=on_new_client, kwargs={'conn': conn, 'addr': address})
                thread.daemon = True
                thread.start()
            except socket.timeout:
                pass

def relay_exit():
    global clients
    print('Relay Shutdown')
    _tmp = clients # Prevents threads from calling None.send()
    clients = set()
    for c in _tmp:
        c.shutdown(socket.SHUT_RDWR)
        c.close()
        quit()

if __name__ == '__main__':
    try:
        relay_start()
    except (KeyboardInterrupt, SystemExit):
        relay_exit()
