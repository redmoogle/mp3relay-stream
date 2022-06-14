from re import M
from tkinter.messagebox import NO
from turtle import st
import urllib.request as urlreq
import urllib
import socket
import threading
import time
import datetime
from wsgiref import headers

clients = set()
to_add = set()
buffer = None
changeovertime = datetime.datetime.now()+datetime.timedelta(hours=1)

url = "https://hitradio-maroc.ice.infomaniak.ch/hitradio-maroc-128.mp3"

MPEG_ID = {
    '00': "MPEG Version 2.5",
    '01': "Invalid/Reserved Version",
    '10': "MPEG Version 2",
    '11': "MPEG Version 1"
}

LAYER_ID = {
    '00': "Invalid/Reserved Layer",
    '01': "Layer III",
    '10': "Layer II",
    '11': "Layer I"
}

CRC_MODE = {
    '0': "CRC ON",
    '1': "CRC OFF"
}

# Hell
BITRATE = {
    '0000': {
        '00': { # V2.5
            '01': 'Variable/Free', # L3
            '10': 'Variable/Free', # L2
            '11': 'Variable/Free'  # L1
        },
        '10': { # V2
            '01': 'Variable/Free', # L3
            '10': 'Variable/Free', # L2
            '11': 'Variable/Free'  # L1
        },
        '11': { # V1
            '01': 'Variable/Free', # L3
            '10': 'Variable/Free', # L2
            '11': 'Variable/Free'  # L1
        },
    },
    '0001': {
        '00': { # V2.5
            '01': '8Kbps', # L3
            '10': '8Kbps', # L2
            '11': '32Kbps' # L1
        },
        '10': { # V2
            '01': '8Kbps', # L3
            '10': '8Kbps', # L2
            '11': '32Kbps' # L1
        },
        '11': { # V1
            '01': '32Kbps', # L3
            '10': '32Kbps', # L2
            '11': '32Kbps'  # L1
        },
    },
    '0010': {
        '00': { # V2.5
            '01': '16Kbps', # L3
            '10': '16Kbps', # L2
            '11': '48Kbps' # L1
        },
        '10': { # V2
            '01': '16Kbps', # L3
            '10': '16Kbps', # L2
            '11': '48Kbps' # L1
        },
        '11': { # V1
            '01': '40Kbps', # L3
            '10': '48Kbps', # L2
            '11': '64Kbps'  # L1
        },
    },
    '0011': {
        '00': { # V2.5
            '01': '24Kbps', # L3
            '10': '24Kbps', # L2
            '11': '56Kbps' # L1
        },
        '10': { # V2
            '01': '24Kbps', # L3
            '10': '24Kbps', # L2
            '11': '56Kbps' # L1
        },
        '11': { # V1
            '01': '48Kbps', # L3
            '10': '56Kbps', # L2
            '11': '96Kbps'  # L1
        },
    },
    '0100': {
        '00': { # V2.5
            '01': '32Kbps', # L3
            '10': '32Kbps', # L2
            '11': '64Kbps' # L1
        },
        '10': { # V2
            '01': '32Kbps', # L3
            '10': '32Kbps', # L2
            '11': '64Kbps' # L1
        },
        '11': { # V1
            '01': '56Kbps', # L3
            '10': '64Kbps', # L2
            '11': '128Kbps'  # L1
        },
    },
    '0101': {
        '00': { # V2.5
            '01': '40Kbps', # L3
            '10': '40Kbps', # L2
            '11': '80Kbps' # L1
        },
        '10': { # V2
            '01': '40Kbps', # L3
            '10': '40Kbps', # L2
            '11': '80Kbps' # L1
        },
        '11': { # V1
            '01': '64Kbps', # L3
            '10': '80Kbps', # L2
            '11': '160Kbps'  # L1
        },
    },
    '0110': {
        '00': { # V2.5
            '01': '48Kbps', # L3
            '10': '48Kbps', # L2
            '11': '96Kbps' # L1
        },
        '10': { # V2
            '01': '48Kbps', # L3
            '10': '48Kbps', # L2
            '11': '96Kbps' # L1
        },
        '11': { # V1
            '01': '80Kbps', # L3
            '10': '96Kbps', # L2
            '11': '192Kbps'  # L1
        },
    },
    '0111': {
        '00': { # V2.5
            '01': '56Kbps', # L3
            '10': '56Kbps', # L2
            '11': '112Kbps' # L1
        },
        '10': { # V2
            '01': '56Kbps', # L3
            '10': '56Kbps', # L2
            '11': '112Kbps' # L1
        },
        '11': { # V1
            '01': '96Kbps', # L3
            '10': '112Kbps', # L2
            '11': '224Kbps'  # L1
        },
    },
    '1000': {
        '00': { # V2.5
            '01': '64Kbps', # L3
            '10': '64Kbps', # L2
            '11': '128Kbps' # L1
        },
        '10': { # V2
            '01': '64Kbps', # L3
            '10': '64Kbps', # L2
            '11': '128Kbps' # L1
        },
        '11': { # V1
            '01': '112Kbps', # L3
            '10': '128Kbps', # L2
            '11': '256Kbps'  # L1
        },
    },
    '1001': {
        '00': { # V2.5
            '01': '80Kbps', # L3
            '10': '80Kbps', # L2
            '11': '144Kbps' # L1
        },
        '10': { # V2
            '01': '80Kbps', # L3
            '10': '80Kbps', # L2
            '11': '144Kbps' # L1
        },
        '11': { # V1
            '01': '128Kbps', # L3
            '10': '160Kbps', # L2
            '11': '288Kbps'  # L1
        },
    },
    '1010': {
        '00': { # V2.5
            '01': '96Kbps', # L3
            '10': '96Kbps', # L2
            '11': '160Kbps' # L1
        },
        '10': { # V2
            '01': '96Kbps', # L3
            '10': '96Kbps', # L2
            '11': '160Kbps' # L1
        },
        '11': { # V1
            '01': '160Kbps', # L3
            '10': '192Kbps', # L2
            '11': '320Kbps'  # L1
        },
    },
    '1011': {
        '00': { # V2.5
            '01': '112Kbps', # L3
            '10': '112Kbps', # L2
            '11': '176Kbps' # L1
        },
        '10': { # V2
            '01': '112Kbps', # L3
            '10': '112Kbps', # L2
            '11': '176Kbps' # L1
        },
        '11': { # V1
            '01': '192Kbps', # L3
            '10': '224Kbps', # L2
            '11': '352Kbps'  # L1
        },
    },
    '1100': {
        '00': { # V2.5
            '01': '128Kbps', # L3
            '10': '128Kbps', # L2
            '11': '192Kbps' # L1
        },
        '10': { # V2
            '01': '128Kbps', # L3
            '10': '128Kbps', # L2
            '11': '192Kbps' # L1
        },
        '11': { # V1
            '01': '224Kbps', # L3
            '10': '256Kbps', # L2
            '11': '384Kbps'  # L1
        },
    },
    '1101': {
        '00': { # V2.5
            '01': '144Kbps', # L3
            '10': '144Kbps', # L2
            '11': '224Kbps' # L1
        },
        '10': { # V2
            '01': '144Kbps', # L3
            '10': '144Kbps', # L2
            '11': '224Kbps' # L1
        },
        '11': { # V1
            '01': '256Kbps', # L3
            '10': '320Kbps', # L2
            '11': '416Kbps'  # L1
        },
    },
    '1110': {
        '00': { # V2.5
            '01': '160Kbps', # L3
            '10': '160Kbps', # L2
            '11': '256Kbps' # L1
        },
        '10': { # V2
            '01': '160Kbps', # L3
            '10': '160Kbps', # L2
            '11': '256Kbps' # L1
        },
        '11': { # V1
            '01': '320Kbps', # L3
            '10': '384Kbps', # L2
            '11': '448Kbps'  # L1
        },
    },
    '1111': {
        '00': { # V2.5
            '01': 'Invalid Bitrate', # L3
            '10': 'Invalid Bitrate', # L2
            '11': 'Invalid Bitrate' # L1
        },
        '10': { # V2
            '01': 'Invalid Bitrate', # L3
            '10': 'Invalid Bitrate', # L2
            '11': 'Invalid Bitrate' # L1
        },
        '11': { # V1
            '01': 'Invalid Bitrate', # L3
            '10': 'Invalid Bitrate', # L2
            '11': 'Invalid Bitrate'  # L1
        },
    }
}

SAMPLE_FREQ = {
    '00' : {
        '00': '11025Hz', # L2.5
        '10': '22050Hz', # L2
        '11': '44100Hz'  # L1
    },
    '01': {
        '00': '12000Hz', # L2.5
        '10': '24000Hz', # L2
        '11': '48000Hz'  # L1
    },
    '10': {
        '00': '8000Hz', # L2.5
        '10': '16000Hz', # L2
        '11': '32000Hz'  # L1
    },
    '11': {
        '00': 'Reserved Sampling Frequency', # L2.5
        '10': 'Reserved Sampling Frequency', # L2
        '11': 'Reserved Sampling Frequency'  # L1
    }
}

PADDING = {
    '1': 'Padded Frame',
    '0': 'Unpadded Frame'
}

PRIVATE = {
    '1': 'Private Stream',
    '0': 'Public Stream'
}

STEREO = {
    '00': 'Stereo',
    '01': 'Joint Stereo',
    '10': 'Dual Channel (Dual Mono)',
    '11': 'Mono'
}

COPYRIGHT = {
    '1': 'Copyrighted Stream',
    '0': 'Uncopyrighted Stream'
}

ORIGINAL = {
    '1': 'Original Media',
    '0': 'Copied Media'
}

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
    global changeovertime

    while(True):
        try:
            buffer = extconn.read(1024*16) # Read 16kb of data from the stream
            header = "{:08b}".format(int(buffer[0:4].hex(), 16))
            if(header[0:11] == '11111111111'):
                header = header[11:34] # 21 Bits Remain
                print('MP3 STREAM DETECTED')
                mpeg = header[0:2]
                layer = header[2:4]
                bitrate = BITRATE[header[5:9]][mpeg][layer] # Skip CRC bit
                samplerate = SAMPLE_FREQ[header[9:11]][mpeg]
                private = PRIVATE[header[13]] # Skip Padding bit
                stereo = STEREO[header[13:15]]
                copyrighted = COPYRIGHT[header[17]]
                original = ORIGINAL[header[18]]
                print(f'{MPEG_ID[mpeg]} | {LAYER_ID[layer]}')
                print(f'{bitrate} | {samplerate}')
                print(f'{private} | {original} | {copyrighted}')
                print(f'{stereo}')

            if(buffer == b""):
                _tmpconn = urlreq.urlopen(url, timeout=60)
                extconn.close()
                extconn = _tmpconn
                print('Detecting empty buffer restarting stream')
                changeovertime = datetime.datetime.now()+datetime.timedelta(hours=1)
            if(datetime.datetime.now() > changeovertime):
                _tmpconn = urlreq.urlopen(url, timeout=60)
                extconn.close()
                extconn = _tmpconn
                print('Streams have been changed over')
                changeovertime = datetime.datetime.now()+datetime.timedelta(hours=1)
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