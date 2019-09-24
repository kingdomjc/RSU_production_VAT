from functools import wraps
from IS13 import *
from pyDes import *
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


IS13 = IS13()
PSAM_SLOT = 0


class SmartCardError(Exception):

    def __init__(self, msg):
        super(self, SmartCardError)
        self.msg = msg

    def __str__(self):
        return self.msg


def logit(func):
    @wraps(func)
    def with_logging(*args, **kwargs):
        fp = func.__name__
        for p in args:
            fp += " " + str(p)
        try:
            ret = func(*args, **kwargs)
        except Exception as e:
            fp += " " + str(e)
            ret = None
        else:
            fp += " " + str(ret)
        logger.debug(fp)
        return ret

    return with_logging


@logit
def OPEN_READER(com):
    IS13.open(com)

def CLOSE_READER():
    IS13.close()

@logit
def OPEN_HFCARD():
    ret = IS13.hfInvent()
    return ret

def CLOSE_HFCARD():
    IS13.hfclose()
    print 'CLOSE_HFCARD\n'

def BEEP_Audio():
    IS13.beep()

@logit
def SET_PSAM_SLOT(slot):
    global PSAM_SLOT
    PSAM_SLOT = slot


@logit
def OPEN_PSAM():
    ret = IS13.resetPsam(PSAM_SLOT)
    return ret


@logit
def HFCARD_COMMAND(command):
    ret = IS13.hfExchangeApdu(command)    
    if ret[0][0:4] != "9000":
        raise StandardError(ret[0] + " command fail ")
    return ret[0][4:]


@logit
def PSAM_COMMAND(command):
    frame = "%02x" % (len(command) / 2)
    frame += command
    ret = IS13.psamExchangeApdu(PSAM_SLOT, 1, frame)
    if ret[0][-4:] != "9000":
        raise StandardError(ret[0] + " command fail ")
    return ret[0][:-4]


@logit
def OPEN_ESAM():
    ret = IS13.inventObu()
    return None


@logit
def ESAM_COMMAND(command):
    frame = "%02x" % (len(command) / 2)
    frame += command
    ret = IS13.transferChannel(2, 1, frame)
    if ret[0][-4:] != "9000":
        raise StandardError(ret[0] + " command fail ")
    return ret[0][:-4]

@logit
def OPEN_ICC():
    ret = IS13.inventObu()
    return None


@logit
def ICC_COMMAND(command):
    frame = "%02x" % (len(command) / 2)
    frame += command
    ret = IS13.transferChannel(1, 1, frame)
    if ret[0][-4:] != "9000":
        raise StandardError(ret[0] + " command fail ")
    return ret[0][:-4]