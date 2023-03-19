import socket
import asyncio
from threading import Thread
from urllib.error import HTTPError, URLError
import urllib.request as urlreq
import mp3packet
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

url = "https://hitradio-maroc.ice.infomaniak.ch/hitradio-maroc-128.mp3"

class MP3Relay:
    def __init__(self) -> None:
        # Address to bind to
        self.bind_address = None
        # Port to broadcast on
        self.port = None
        # Link to the stream
        self.stream = None
        # List of listening clients
        self.clients = []
        # Running thread
        self.loop = None
        # Socket of the server
        self.socket: socket = None
        # Socket of the remote stream
        self.remote_socket: socket = None
        # Size of the mp3 packet
        self.packetsize = 0
        # Mp3 packet for emulating header
        self.packet: mp3packet = None
        # Waiting to add
        self.adding = []
        # Waiting to remove
        self.removing = []
        # Name of the relay
        self.name = "Unknown Relay"

    def __repr__(self) -> str:
        return f"{self.name} ({len(self.clients)} Listeners)"

    def background_loop(self, loop: asyncio.AbstractEventLoop):
        asyncio.set_event_loop(loop)
        asyncio.ensure_future(self.connection_loop(), loop=loop)
        asyncio.ensure_future(self.bufferinput(), loop=loop)
        loop.run_forever()

    async def handle_clients(self, buffer):
        self.clients += self.adding
        self.adding.clear()

        for client in self.clients:
            try:
                client.send(buffer)
            except (HTTPError, URLError, ConnectionError, socket.timeout, TimeoutError) as err: # TODO remove this horrifyingly bad code
                self.removing.append(client)
                self.relay_report("A Client Disconnected")

        for client in self.removing:
            self.clients.remove(client)
        self.removing.clear()

    async def bufferinput(self):
        """
        Waits until the buffer is filled then sends it
        """
        await self.connect()
        while(True):
            try:
                await asyncio.sleep(self.packet.duration()*9) # Give time for other things
                buffer = self.remote_socket.read(self.packetsize*10) # Recieve 10 mp3 packets about 0.26s of audio
                if(buffer == b""):
                    self.relay_report("Detected an empty buffer; Reconnecting to the stream")
                    await self.connect()
                    continue
            except (HTTPError, ConnectionError, URLError, socket.timeout, TimeoutError) as err:
                self.relay_report(f"{err}")
                await self.connect()
                continue

            await self.handle_clients(buffer)

    async def connect(self):
        """
        Re/Connects to the remote stream
        """
        if(self.remote_socket is not None):
            self.remote_socket.close()
            self.remote_socket = None
        while self.remote_socket is None:
            try:
                self.remote_socket = urlreq.urlopen(self.stream, timeout=5)
            except (HTTPError, URLError, ConnectionError, socket.timeout, TimeoutError) as err:
                self.remote_socket = None
                if(self.packet):
                    await self.handle_clients(self.packet.getEmpty() * 100)
                else:
                    await self.handle_clients(None)

        self.packet = mp3packet.MP3Packet()
        syncs = 0
        while(syncs < 5): # Align to the mp3 stream (need to be able to emulate packets when connection drops)
            buffer = self.remote_socket.read(4) # Read the mp3 header
            if self.packet.IsHeader(buffer):
                self.packet.decode_from_hex(buffer)
                self.packetsize = self.packet.next_header()
                self.remote_socket.read(self.packetsize-4)
                buffer = self.remote_socket.read(4)
                if self.packet.IsHeader(buffer):
                    self.packet.decode_from_hex(buffer)
                    self.packetsize = self.packet.next_header()
                    syncs += 1
                    self.remote_socket.read(self.packetsize-4)
                else:
                    syncs = max(0, syncs - 1) # garbage data

        self.relay_report("Synchronized with the mp3 stream")

    async def initiate_client(self, conn, addr):
        """
        Give clients basic info about the relay (aka that its a mp3 stream)
        """
        conn.send(bytes('HTTP/1.1 200 OK\r\n', 'utf-8')) # HTTP requests expect a 200 OK before any header or data
        conn.send(bytes("Content-Type: audio/mpeg\n\n", 'utf-8')) # Specify its a mp3 stream
        self.adding.append(conn)
        self.relay_report("A Client Connected")

    async def connection_loop(self):
        """
        Accepts incoming connections and initializes clients
        """
        while True:
            conn, address = await self.loop.sock_accept(self.socket)
            await self.initiate_client(conn, address)

    def start_relay(self):
        """
        Start up the relay
        """
        self.loop = asyncio.new_event_loop()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.bind_address, self.port)) # Start listening
        self.socket.listen(5)
        self.socket.setblocking(False)

        asyncloop = Thread(target=self.background_loop, args=(self.loop,))
        asyncloop.start()

    def stop_relay(self):
        """
        Close down the relay
        """
        clientcopy = self.clients.copy()
        self.clients = []
        for client in clientcopy:
            client.shutdown(socket.SHUT_RDWR)
            client.close()

    def relay_report(self, message):
        print(f"\nRelay: {self} reports - {message}")


if __name__ == '__main__':
    try:
        relay: MP3Relay = MP3Relay()
        relay.stream = "https://hitradio-maroc.ice.infomaniak.ch/hitradio-maroc-128.mp3"
        relay.port = 5222
        relay.bind_address = "127.0.0.1"
        relay.start_relay()
    except (KeyboardInterrupt, SystemExit):
        pass