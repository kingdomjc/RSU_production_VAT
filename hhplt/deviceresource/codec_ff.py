# coding=utf8
import binascii


class CodecState(object):

    def __init__(self, codec):
        self.codec = codec


class CodecStateInit(CodecState):

    def next(self, ch):
        self.codec.recv_buf = []
        if ch == '\xFF':
            self.codec.state = CodecStateRSCTL(self.codec)
        return ""


class CodecStateFF(CodecState):

    def next(self, ch):
        if ch == '\xFF':
            self.codec.state = CodecStateRSCTL(self.codec)
        else:
            self.codec.state = CodecStateInit(self.codec)
        return ""


class CodecStateRSCTL(CodecState):

    def next(self, ch):
        if ch != '\xFF':
            self.codec.state = CodecStateData(self.codec)
        


class CodecStateData(CodecState):

    def next(self, ch):
        if ch == '\xff':
            self.codec.state = CodecStateInit(self.codec)
            return str(bytearray(self.codec.recv_buf[:-1]))
        elif ch == '\xfe':
            self.codec.state = CodecStateDecode(self.codec)
        else:
            self.codec.recv_buf.append(ch)
        return ""


class CodecStateDecode(CodecState):

    def next(self, ch):
        if ch == '\x01':
            self.codec.recv_buf.append('\xFF')
            self.codec.state = CodecStateData(self.codec)
        elif ch == '\x00':
            self.codec.recv_buf.append('\xFE')
            self.codec.state = CodecStateData(self.codec)
        else:
            self.codec.state = CodecStateInit(self.codec)


class CodecStateBCC(CodecState):

    def next(self, ch):
        # print "CodecStateBCC next is called ch is "+binascii.hexlify(ch)
        # print "decode frame is ",
        # binascii.hexlify(bytearray(self.codec.recv_buf))
        self.codec.state = CodecStateInit(self.codec)
        return str(bytearray(self.codec.recv_buf))


def calc_bcc(source, init=0):
    bcc = init
    for x in source:
        bcc ^= x
    return bcc


class EtcCodec(object):

    def __init__(self):
        self.state = CodecStateInit(self)
        self.recv_buf = []
        self.RSCTL = '\x82'
        self.frame_len = 0

    def encode(self, source):
        encode_len = len(source)
        #rsctl = chr(((ord(self.RSCTL)>>4)|(ord(self.RSCTL)<<4))&0xff)
        #rsctl = chr((ord(self.RSCTL))%8)
        rsctl = self.RSCTL
        temp = ['\xFF', rsctl]
        bcc = ord(rsctl)
        for ch in source:
            bcc ^= ord(ch)
            if ch == '\xFF':
                temp.append('\xFE')
                temp.append('\x01')
            elif ch == '\xFE':
                temp.append('\xFE')
                temp.append('\x00')
            else:
                temp.append(ch)

        if bcc == 255:
            temp.append('\xFE')
            temp.append('\x01')
        elif bcc == 254:
            temp.append('\xFE')
            temp.append('\x00')
        else:
            temp.append(chr(bcc))
        temp.append('\xff')
        # print "encoded frame is ", binascii.hexlify(bytearray(temp))
        return str(bytearray(temp))

    def decode(self, source):
        ret = ""
        # print "etc codec decode is called
        for ch in source:
            decoded = self.state.next(ch)
            if decoded:
                ret = decoded
        return ret

    def close(self):
        self.state = CodecStateInit(self)
        self.RSCTL = '\x82'
        self.frame_len = 0
