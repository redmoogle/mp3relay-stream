import socket
import asyncio
from threading import Thread
from urllib.error import HTTPError
import urllib.request as urlreq
import logging
from mp3packet import MP3Packet

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

url = "https://hitradio-maroc.ice.infomaniak.ch/hitradio-maroc-128.mp3"

class MP3Relay:
    def __init__(self) -> None:
        # Address to bind to
        self.bind_address: str = None
        # Port to broadcast on
        self.port: int = None
        # Link to the stream
        self.stream: str = None
        # List of listening clients
        self.clients: list = []
        # Running thread
        self.loop: asyncio.AbstractEventLoop = None
        # Socket of the server
        self.socket: socket = None
        # Socket of the remote stream
        self.remote_socket: socket = None
        # Size of the mp3 packet
        self.packetsize: int = 0
        # Mp3 packet for emulating header
        self.packet: MP3Packet = None
        # Waiting to add
        self.adding: list = []
        # Waiting to remove
        self.removing: list = []
        # Name of the relay
        self.name: str = "Unknown Relay"

    def __repr__(self) -> str:
        return f"{self.name} ({(len(self.clients) + len(self.adding)) - len(self.removing)} Listeners)"

    def setBackgroundLoop(self, loop: asyncio.AbstractEventLoop):
        asyncio.set_event_loop(loop)
        asyncio.ensure_future(self.connectionLoop(), loop=loop)
        asyncio.ensure_future(self.bufferInput(), loop=loop)
        loop.run_forever()

    async def handleClients(self, buffer):
        self.clients += self.adding
        self.adding.clear()

        for client in self.clients:
            try:
                client.send(buffer)
            except (ConnectionError, TimeoutError): # TODO find an alternative that doesn't use exceptions
                self.removing.append(client)
                self.relayReport("A Client Disconnected")
            except BlockingIOError:
                continue # Client doesnt want more data so wait (this causes the relay to crash if uncaught though)

        for client in self.removing:
            self.clients.remove(client)
        self.removing.clear()

    async def bufferInput(self):
        """
        Waits until the buffer is filled then sends it
        """
        await self.connect()
        while(True):
            try:
                await asyncio.sleep(self.packet.getDuration()*9) # Give time for other things
                if(self.remote_socket is None):
                    self.relayReport("Detected a broken socket; Reconnecting to the stream")
                    await self.connect()
                buffer = self.remote_socket.read(self.packetsize*10) # Recieve 10 mp3 packets about 0.26s of audio
                if(len(buffer) == 0):
                    self.relayReport("Detected an empty buffer; Reconnecting to the stream")
                    await self.connect()
                    continue
            except (HTTPError, ConnectionError, TimeoutError) as err:
                self.relayReport(f"Error while reading stream: {err}")
                await self.connect()
                continue

            await self.handleClients(buffer)

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
                self.relayReport("Reconnected to remote stream")
            except (HTTPError, ConnectionError, TimeoutError) as err:
                self.remote_socket = None
                self.relayReport(f"Error while connecting: {err}")
                if(self.packet):
                    await self.handleClients(self.packet.getEmpty() * 10)
                    await asyncio.sleep(self.packet.getDuration() * 75) # Prevents the client from getting killed with too much data
                else:
                    await self.handleClients(None)

        _packet = MP3Packet()
        syncs = 0
        while(syncs < 5): # Align to the mp3 stream (need to be able to emulate packets when connection drops)
            buffer = self.remote_socket.read(4) # Read the mp3 header
            if _packet.isHeader(buffer):
                _packet.fromHex(buffer)
                _packetsize = _packet.nextHeader()
                self.remote_socket.read(max(4, _packetsize - 4))
                buffer = self.remote_socket.read(4)
                if _packet.isHeader(buffer):
                    _packet.fromHex(buffer)
                    _packetsize = _packet.nextHeader()
                    syncs += 1
                    self.remote_socket.read(max(0, _packetsize - 4))
                else:
                    syncs = max(0, syncs - 1) # garbage data

        self.packet = _packet
        self.packetsize = _packetsize
        self.relayReport("Synchronized with the mp3 stream")

    async def initiateClient(self, conn):
        """
        Give clients basic info about the relay (aka that its a mp3 stream)
        """
        conn.send(bytes('HTTP/1.1 200 OK\r\n', 'utf-8')) # HTTP requests expect a 200 OK before any header or data
        conn.send(bytes("Content-Type: audio/mpeg\n\n", 'utf-8')) # Specify its a mp3 stream
        self.adding.append(conn)
        self.relayReport("A Client Connected")

    async def connectionLoop(self):
        """
        Accepts incoming connections and initializes clients
        """
        while True:
            conn, _ = await self.loop.sock_accept(self.socket)
            await self.initiateClient(conn)

    def startRelay(self):
        """
        Start up the relay
        """
        self.loop = asyncio.new_event_loop()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.bind_address, self.port,)) # Start listening
        self.socket.listen(5)
        self.socket.setblocking(False)

        asyncloop = Thread(target=self.setBackgroundLoop, args=(self.loop,))
        asyncloop.start()

    def stopRelay(self):
        """
        Close down the relay
        """
        clientcopy = self.clients.copy()
        self.clients = []
        for client in clientcopy:
            client.shutdown(socket.SHUT_RDWR)
            client.close()

    def relayReport(self, message):
        print(f"\nRelay: {self} reports - {message}")

if __name__ == '__main__': # For debugging
    relay: MP3Relay = MP3Relay()
    relay.stream = "https://hitradio-maroc.ice.infomaniak.ch/hitradio-maroc-128.mp3"
    relay.port = 5222
    relay.bind_address = "127.0.0.1"
    relay.startRelay()