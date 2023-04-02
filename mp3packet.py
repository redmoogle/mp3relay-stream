import enums
import math

class MP3Packet:
    def __init__(self):
        self.mpeg: float = None
        self.layer: int = None
        self.crc: bool = None
        self.bitrate: float = None
        self.samplerate: int = None
        self.padding: bool = None
        self.private: bool = None
        self.stereo: str = None
        self.copyrighted: bool = None
        self.original: bool = None

        self.raw_header = None

    def __repr__(self):
        return f'''        MPEG Version: v{self.mpeg} | Layer: {self.layer}
        Bitrate: {self.bitrate/1000}kbps | Sample Rate: {self.samplerate}Hz
        {"Private" if self.private else "Public"} | {"Copyrighted" if self.copyrighted else "Uncopyrighted"} | {"Original" if self.original else "Copied"} | {self.stereo}

        Extras:
        CRC: {self.crc} | Padding: {self.padding} | Next Header in {self.next_header()} Bytes
        '''

    def isHeader(self, bytesIn: bytes):
        funnyInt = bytesIn.hex()
        if(len(funnyInt) != 8):
            print("uh oh")
        return (int.from_bytes(bytesIn, "big") & 4292870144) == 4292870144

    def fromHex(self, bytesIn):
        """
        Takes a hexadecimal input and converts it to mp3 data
        """
        self.raw_header = bytesIn
        bytesIn = int.from_bytes(bytesIn, "big")
        bytesIn >>= 2 # Shift the emphasis bits out
        self.original = (bytesIn & 1) == 1
        bytesIn >>= 1 # Shift the orignal bit out
        self.copyrighted = (bytesIn & 1) == 1
        bytesIn >>= 3 # Shift the copyright bit out & mode bits out
        self.stereo = enums.STEREO[bytesIn & 3]
        bytesIn >>= 2 # Shift the audio mode out
        self.private = (bytesIn & 1) == 1
        bytesIn >>= 1 # Shift the private bit out
        self.padding = (bytesIn & 1) == 1
        bytesIn >>= 1 # Shift the padding bit out

        _sampleratebits = bytesIn & 3
        bytesIn >>= 2 # Shift the sampling rate bits out

        # Hold on to the value temporarily
        _bitratebits = bytesIn & 15
        bytesIn >>= 4 # Shift the bitrate bits out

        self.crc = (bytesIn & 1) == 0
        bytesIn >>= 1 # Shift the crc bit out
        self.layer = 4 - (bytesIn & 3)
        bytesIn >>= 2 # Shift the layer bits out
        self.mpeg = enums.MPEG_ID[bytesIn & 3]

        self.samplerate = enums.SAMPLE_FREQ[_sampleratebits].get(self.mpeg, 0)
        self.bitrate = enums.BITRATE[_bitratebits].get(self.mpeg, {}).get(self.layer, 0)
        return True

    def getHeader(self):
        return self.raw_header

    def nextHeader(self):
        """
        Finds where the next header will show up
        """
        # Layer I 32 bits ; Layer II & III 8 bits
        # For Layer I files us this formula:
        # FrameLengthInBytes = (12 * BitRate / SampleRate + Padding) * 4
        # For Layer II & III files use this formula:
        # FrameLengthInBytes = 144 * BitRate / SampleRate + Padding
        if(self.bitrate == 0 or self.samplerate == 0):
            return 0
        
        padding_add = 0
        crc_add = 0
        if self.crc == True:
            crc_add = 2

        if(self.layer == 1):
            if self.padding == True:
                padding_add = 4

            return math.floor((12 * (self.bitrate/self.samplerate) + padding_add) * 4) + crc_add
        elif (self.layer == 2) or (self.layer == 3):
            if self.padding == True:
                padding_add = 1

            return math.floor(144 * (self.bitrate/self.samplerate) + padding_add) + crc_add
        return 8

    def getDuration(self):
        """
        Duration of this frame
        """
        return self.nextHeader()/self.bitrate

    def getEmpty(self):
        return self.raw_header + (b"\x00" * (self.next_header() - 4))