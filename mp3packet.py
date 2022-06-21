import enums
import math

class MP3Packet:
    def __init__(self):
        self.mpeg = None
        self.layer = None
        self.crc = None
        self.bitrate = None
        self.samplerate = None
        self.padding = None
        self.private = None
        self.stereo = None
        self.copyrighted = None
        self.original = None

    def __repr__(self):
        return f'''
        MPEG Version: v{self.mpeg} | Layer: {self.layer}
        Bitrate: {self.bitrate/1000}kbps | Sample Rate: {self.samplerate}Hz
        {self.private} | {self.copyrighted} | {self.original} | {self.stereo}

        Extras:
        CRC: {self.crc} | Padding: {self.padding} | Next Header in {self.next_header()} Bytes
        '''
    
    def _hex2bin(self, hexa):
        return "{:011b}".format(int(hexa.hex(), 16))

    def IsHeader(self, hexa):
        return self._hex2bin(hexa)[0:11] == '11111111111'

    def decode_from_hex(self, hexa):
        """
        Takes a hexadecimal input and converts it to mp3 data
        """
        #int(hexa.hex(), 16)
        binary = "{:08b}".format(int(hexa.hex(), 16))[11:32]
        self.mpeg = enums.MPEG_ID[binary[0:2]]
        self.layer = enums.LAYER_ID[binary[2:4]]
        self.crc = enums.CRC_MODE[binary[4]]
        self.bitrate = enums.BITRATE[binary[5:9]][self.mpeg][self.layer]
        self.samplerate = enums.SAMPLE_FREQ[binary[9:11]][self.mpeg]
        self.padding = enums.PADDING[binary[11]]
        self.private = enums.PRIVATE[binary[12]]
        self.stereo = enums.STEREO[binary[13:15]] # 15-17 contain some random joint stero stuff
        self.copyrighted = enums.COPYRIGHT[binary[17]]
        self.original = enums.ORIGINAL[binary[18]]
        return True

    def next_header(self):
        """
        Finds where the next header will show up
        """
        # Layer I 32 bits ; Layer II & III 8 bits
        # For Layer I files us this formula:
        # FrameLengthInBytes = (12 * BitRate / SampleRate + Padding) * 4
        # For Layer II & III files use this formula:
        # FrameLengthInBytes = 144 * BitRate / SampleRate + Padding
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