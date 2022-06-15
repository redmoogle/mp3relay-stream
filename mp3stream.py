from urllib.error import HTTPError, URLError
import urllib.request as urlreq
import socket
import threading
import time
import math
import logging

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
            '01': 8000, # L3
            '10': 8000, # L2
            '11': 32000 # L1
        },
        '10': { # V2
            '01': 8000, # L3
            '10': 8000, # L2
            '11': 32000 # L1
        },
        '11': { # V1
            '01': 32000, # L3
            '10': 32000, # L2
            '11': 32000  # L1
        },
    },
    '0010': {
        '00': { # V2.5
            '01': 16000, # L3
            '10': 16000, # L2
            '11': 48000 # L1
        },
        '10': { # V2
            '01': 16000, # L3
            '10': 16000, # L2
            '11': 48000 # L1
        },
        '11': { # V1
            '01': 40000, # L3
            '10': 48000, # L2
            '11': 64000  # L1
        },
    },
    '0011': {
        '00': { # V2.5
            '01': 24000, # L3
            '10': 24000, # L2
            '11': 56000 # L1
        },
        '10': { # V2
            '01': 24000, # L3
            '10': 24000, # L2
            '11': 56000 # L1
        },
        '11': { # V1
            '01': 48000, # L3
            '10': 56000, # L2
            '11': 96000  # L1
        },
    },
    '0100': {
        '00': { # V2.5
            '01': 32000, # L3
            '10': 32000, # L2
            '11': 64000 # L1
        },
        '10': { # V2
            '01': 32000, # L3
            '10': 32000, # L2
            '11': 64000 # L1
        },
        '11': { # V1
            '01': 56000, # L3
            '10': 64000, # L2
            '11': 128000  # L1
        },
    },
    '0101': {
        '00': { # V2.5
            '01': 40000, # L3
            '10': 40000, # L2
            '11': 80000 # L1
        },
        '10': { # V2
            '01': 40000, # L3
            '10': 40000, # L2
            '11': 80000 # L1
        },
        '11': { # V1
            '01': 64000, # L3
            '10': 80000, # L2
            '11': 160000  # L1
        },
    },
    '0110': {
        '00': { # V2.5
            '01': 48000, # L3
            '10': 48000, # L2
            '11': 96000 # L1
        },
        '10': { # V2
            '01': 48000, # L3
            '10': 48000, # L2
            '11': 96000 # L1
        },
        '11': { # V1
            '01': 80000, # L3
            '10': 96000, # L2
            '11': 192000  # L1
        },
    },
    '0111': {
        '00': { # V2.5
            '01': 56000, # L3
            '10': 56000, # L2
            '11': 112000 # L1
        },
        '10': { # V2
            '01': 56000, # L3
            '10': 56000, # L2
            '11': 112000 # L1
        },
        '11': { # V1
            '01': 96000, # L3
            '10': 112000, # L2
            '11': 224000  # L1
        },
    },
    '1000': {
        '00': { # V2.5
            '01': 64000, # L3
            '10': 64000, # L2
            '11': 128000 # L1
        },
        '10': { # V2
            '01': 64000, # L3
            '10': 64000, # L2
            '11': 128000 # L1
        },
        '11': { # V1
            '01': 112000, # L3
            '10': 128000, # L2
            '11': 256000  # L1
        },
    },
    '1001': {
        '00': { # V2.5
            '01': 80000, # L3
            '10': 80000, # L2
            '11': 144000 # L1
        },
        '10': { # V2
            '01': 80000, # L3
            '10': 80000, # L2
            '11': 144000 # L1
        },
        '11': { # V1
            '01': 128000, # L3
            '10': 160000, # L2
            '11': 288000  # L1
        },
    },
    '1010': {
        '00': { # V2.5
            '01': 96000, # L3
            '10': 96000, # L2
            '11': 160000 # L1
        },
        '10': { # V2
            '01': 96000, # L3
            '10': 96000, # L2
            '11': 160000 # L1
        },
        '11': { # V1
            '01': 160000, # L3
            '10': 192000, # L2
            '11': 320000  # L1
        },
    },
    '1011': {
        '00': { # V2.5
            '01': 112000, # L3
            '10': 112000, # L2
            '11': 176000 # L1
        },
        '10': { # V2
            '01': 112000, # L3
            '10': 112000, # L2
            '11': 176000 # L1
        },
        '11': { # V1
            '01': 192000, # L3
            '10': 224000, # L2
            '11': 352000  # L1
        },
    },
    '1100': {
        '00': { # V2.5
            '01': 128000, # L3
            '10': 128000, # L2
            '11': 192000 # L1
        },
        '10': { # V2
            '01': 128000, # L3
            '10': 128000, # L2
            '11': 192000 # L1
        },
        '11': { # V1
            '01': 224000, # L3
            '10': 256000, # L2
            '11': 384000  # L1
        },
    },
    '1101': {
        '00': { # V2.5
            '01': 144000, # L3
            '10': 144000, # L2
            '11': 224000 # L1
        },
        '10': { # V2
            '01': 144000, # L3
            '10': 144000, # L2
            '11': 224000 # L1
        },
        '11': { # V1
            '01': 256000, # L3
            '10': 320000, # L2
            '11': 416000  # L1
        },
    },
    '1110': {
        '00': { # V2.5
            '01': 160000, # L3
            '10': 160000, # L2
            '11': 256000 # L1
        },
        '10': { # V2
            '01': 160000, # L3
            '10': 160000, # L2
            '11': 256000 # L1
        },
        '11': { # V1
            '01': 320000, # L3
            '10': 384000, # L2
            '11': 448000  # L1
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
        '00': 11025, # L2.5
        '10': 22050, # L2
        '11': 44100  # L1
    },
    '01': {
        '00': 12000, # L2.5
        '10': 24000, # L2
        '11': 48000  # L1
    },
    '10': {
        '00': 8000, # L2.5
        '10': 16000, # L2
        '11': 32000  # L1
    },
    '11': {
        '00': 'Reserved Sampling Frequency', # L2.5
        '10': 'Reserved Sampling Frequency', # L2
        '11': 'Reserved Sampling Frequency'  # L1
    }
}

PADDING = {
    '1': 'Padded',
    '0': 'Unpadded'
}

PRIVATE = {
    '1': 'Private',
    '0': 'Public'
}

STEREO = {
    '00': 'Stereo',
    '01': 'Joint Stereo',
    '10': 'Dual Channel (Dual Mono)',
    '11': 'Mono'
}

COPYRIGHT = {
    '1': 'Copyrighted',
    '0': 'Uncopyrighted'
}

ORIGINAL = {
    '1': 'Original',
    '0': 'Copied'
}

def on_new_client(conn, addr):
    global to_add
    conn.send(bytes('HTTP/1.1 200 OK\r\n', 'utf-8')) # HTTP requests expect a 200 OK before any header or data
    conn.send(bytes("Content-Type: audio/mpeg\n\n", 'utf-8')) # Specify its a mp3 stream
    conn.send(buffer)
    to_add.add(conn)

def mp3_decode(header):
    header = header[11:34] # 21 Bits Remain
    mpeg = header[0:2]
    layer = header[2:4]
    bitrate = BITRATE[header[5:9]][mpeg][layer] # Skip CRC bit
    samplerate = SAMPLE_FREQ[header[9:11]][mpeg]
    padding = header[12]
    return LAYER_ID[layer], bitrate, samplerate, padding

def mp3_display(header):
    header = header[11:34] # 21 Bits Remain
    mpeg = header[0:2]
    layer = header[2:4]
    bitrate = BITRATE[header[5:9]][mpeg][layer] # Skip CRC bit
    samplerate = SAMPLE_FREQ[header[9:11]][mpeg]
    private = PRIVATE[header[13]]
    stereo = STEREO[header[13:15]]
    copyrighted = COPYRIGHT[header[17]]
    original = ORIGINAL[header[18]]

    print('\nMP3 STREAM DETECTED\n')
    print(f'{MPEG_ID[mpeg]} | {LAYER_ID[layer]}')
    print(f'{bitrate/1000}kbps | {samplerate}Hz')
    print(f'{private} | {original} | {copyrighted}')
    print(f'{stereo}\n')

def mp3_next_header(layer, padding, bitrate, samplerate):
    # Layer I 32 bits ; Layer II & III 8 bits
    # For Layer I files us this formula:
    # FrameLengthInBytes = (12 * BitRate / SampleRate + Padding) * 4
    # For Layer II & III files use this formula:
    # FrameLengthInBytes = 144 * BitRate / SampleRate + Padding

    if(layer == 'Layer I'):
        padding_add = 0
        if padding == '1':
            padding_add = 32
        
        return math.floor((12 * (bitrate/samplerate) + padding_add) * 4)
    elif (layer == 'Layer II') or (layer == 'Layer III'):
        padding_add = 0
        if padding == '1':
            padding_add = 8
        
        return math.floor(144 * (bitrate/samplerate) + padding_add)

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
    while(syncs < 20):
        buffer = extconn.read(4) # Read the mp3 header
        header = "{:08b}".format(int(buffer[0:4].hex(), 16))
        if(header[0:11] == '11111111111'):
            layer, bitrate, samplerate, padding = mp3_decode(header) # were going to forge our own packets
            next = mp3_next_header(layer, padding, bitrate, samplerate)
            mp3_head = buffer
            syncs += 1
        extconn.read(next-4) # This will mess up any invalid headers

    mp3_display("{:08b}".format(int(mp3_head.hex(), 16)))

def bufferio():
    """
    Grabs the data from the url in extconn and broadcast it to all listening clients
    """
    to_remove = set()

    global buffer
    global clients
    global extconn
    global to_add

    reconnect()

    logging.info("Beginning MP3 Relay Playback")
    while(True):
        try:
            buffer = extconn.read(next*20) # Recieve 20 mp3 packets
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
    addr, port = '127.0.0.1', 5222
    server_socket.bind((addr, port)) # Listen on localhost on port 5222
    server_socket.listen(50)
    print(f'listening to {addr} on port {port}')
    while True:
        conn, address = server_socket.accept()
        print("Connection from " + address[0] + ":" + str(address[1]))
        threading.Thread(target=on_new_client, kwargs={'conn': conn, 'addr': address}).start()