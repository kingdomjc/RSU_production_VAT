from pyDes import *
from binascii import *


def invert_str(data):
    y = bytearray()
    for x in data:
        y.append(chr(255 - ord(x)))
    return str(y)


'''
def MAC(key, init, data):
    #triple mac caculation
    if(len(init) == 8):
        init += '00000000'
    k = triple_des(unhexlify(key), CBC, unhexlify(init), pad='\x00', padmode=PAD_NORMAL)
    data += '80'
    d = k.encrypt(unhexlify(data))
    mac = hexlify(d)
    print mac
    return mac[-16:-8]
'''


def MAC(key, init, data):
    if len(init) != 16:
        print "init should be 16 bytes"
        return None
    keyl = key[0:16]
    keyr = key[16:]
    data += "80"
    if len(data)%16 != 0:
        data += (8 - (len(data)%16)/2)*"00"
    kl_cbc = des(unhexlify(keyl), CBC, unhexlify(init))
    kr = des(unhexlify(keyr))
    blocks = kl_cbc.encrypt(unhexlify(data))
    d = blocks[-8:]
    t = kr.decrypt(d)    
    kl = des(unhexlify(keyl))
    e = kl.encrypt(t)
    return hexlify(e[0:4])


def SMAC(key, init, data):
    if len(init) != 16:
        print "init should be 16 bytes"
        return None 
    if len(key) != 16:
        print "key should be 16 bytes"
        return None 
    data += "80"
    if len(data)%16 != 0:
        data += (8 - (len(data)%16)/2)*"00"
    key_cbc = des(unhexlify(key), CBC, unhexlify(init))
    blocks = key_cbc.encrypt(unhexlify(data))
    return hexlify(blocks[-8:-4])




def TDES(key, ori):
    k = triple_des(unhexlify(key), ECB, pad='\x00', padmode=PAD_NORMAL)
    new_ori = unhexlify(ori)
    d = k.encrypt(new_ori)
    return hexlify(d)


def DELIVER_KEY(key, data):
    k = triple_des(unhexlify(key), ECB, pad='\x00', padmode=PAD_NORMAL)
    data_u = unhexlify(data)
    left = k.encrypt(data_u)
    data_v = invert_str(data_u)
    right = k.encrypt(data_v)
    return hexlify(left + right)
