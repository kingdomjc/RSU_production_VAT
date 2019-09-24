#encoding:utf-8
'''
Created on 2015-3-30
产线交易测试
@author: user
'''
import time
from binascii import *
from pyDes import *

def tdes(key, ori):    
    '''triple des caculation'''
    k = triple_des(unhexlify(key), ECB, pad='\x00', padmode=PAD_NORMAL)
    new_ori = unhexlify(ori + '80')
    d = k.encrypt(new_ori)
    return hexlify(d)

def tdes_raw(key, ori):
    k = triple_des(unhexlify(key), ECB, pad='\x00', padmode=PAD_NORMAL)
    new_ori = unhexlify(ori)
    d = k.encrypt(new_ori)
    return hexlify(d)

def t_mac(key, init, data):
    '''triple mac caculation'''
    if(len(init) == 8):
        init += '00000000'    
    k = triple_des(unhexlify(key), CBC, unhexlify(init), pad='\x00', padmode=PAD_NORMAL)
    data += '80'
    d = k.encrypt(unhexlify(data))
    mac = hexlify(d)
    return mac[-16:-8]

def invert_str(data):
    y = bytearray()
    for x in data:
        y.append(chr(255-ord(x)))
    return str(y)

def t_deliver_key(key, data):
    k = triple_des(unhexlify(key), ECB, pad='\x00', padmode=PAD_NORMAL)
    data_u = unhexlify(data)
    left = k.encrypt(data_u)
    data_v = invert_str(data_u)
    right = k.encrypt(data_v)
    return hexlify(left+right)

def single_mac(key, init, data):
    '''single mac caculation'''
    if(len(init) == 8):
        init += '00000000'
    k = des(unhexlify(key), CBC, unhexlify(init), pad="\x00", padmode = PAD_NORMAL)
    data += '80'
    d = k.encrypt(unhexlify(data))
    mac = hexlify(d)
    print "single mac is "+mac
    return mac[-16:-8]
    

from RSU import RSU
reader = RSU()
reader.setTimeout(1000)

psam_res_map = {}
bst_res_map = {}
transfer_channel_res_map = {}
terminal_trade_sn = "00011569"
trade_time = "20150413160419"
terminal_number = "0151000119f8"

class CommandExecuteException(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return self.msg


def openDevice():
#    reader.RSU_Open(0,'COM1', 0)
    reader.RSU_Open(2,0, 0)

def closeDevice():
    reader.RSU_Close()

def activePasm():
    ret,rlen,Data = reader.PSAM_Reset(0, 0)
    print 'activePasm\t\t ret=%d,rlen=%d,data=%s'%(ret,rlen,Data)
    if ret != 0 :raise CommandExecuteException("ret not 0!")

def read0016File():
    APDU = "0500B0960006"
    ret,APDUList,Data = reader.PSAM_CHANNEL(0, 1, APDU)
    print "read0016File\t\t ret=%d,APDUList=%d,Data=%s"%(ret,APDUList,Data)
    apduLength = int(Data[:2],16)
    if Data[2:][apduLength*2-4:apduLength*2] != "9000":
        raise CommandExecuteException("read0016file ret code is %s"%Data[-4:])
    psam_res_map["psam_terminal_id"] = Data[2:14]
    print "psam_terminal_id = %s" % psam_res_map["psam_terminal_id"] 
    if ret != 0 :raise CommandExecuteException("ret not 0!")

def selectDf01():
    APDU = "0700A4000002DF01"
    reader.setTimeout(5000)
    ret,APDUList,Data = reader.PSAM_CHANNEL(0, 1, APDU)
    print "selectDf01\t\t ret=%d,APDUList=%d,Data=%s"%(ret,APDUList,Data)
    
#    if "612B" in Data:
#        ret,APDUList,Data = reader.PSAM_CHANNEL(0, 1, "0500c000002b")
#        print "selectDf01 - STEP2 \t\t ret=%d,APDUList=%d,Data=%s"%(ret,APDUList,Data)

    if ret != 0 :raise CommandExecuteException("ret not 0!")
    
def bst():
    BeaconID = "03000203"
    Time = "54150556"
    Profile = 1
    MandApplicationlist = 1
    MandApplication = "41af29201a002b"
    Profilelist = 0
    ret,ReturnStatus, Profile, Applicationlist,Application,ObuConfiguration = \
        reader.INITIALISATION(BeaconID, Time, Profile, MandApplicationlist, \
            MandApplication, Profilelist,timeout=3000)
    print "bst\t\t ret=%d,ReturnStatus=%d, Profile=%d, Applicationlist=%d\n,Application=%s\n,ObuConfiguration=%s\n"%\
        (ret,ReturnStatus, Profile, Applicationlist,Application,ObuConfiguration)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    bst_res_map["mac"] = ObuConfiguration[0:8]
    bst_res_map["districtCode"] = Application[4:12]
    bst_res_map["contractSerial"] = Application[24:40]
    bst_res_map["nowEsamVersion"] = Application[22:24]
    print "mac = %s,contractSerial = %s"%(bst_res_map["mac"],bst_res_map["contractSerial"])

def getSecureProc():
    accessCredentialsOp = 0;
    mode = 1;
    DID = 1;
    AccessCredentials="0000000000000000";
    keyIdForEncryptOp = 1;
    FID = 1;
    offset = 0;
    length = 16;
    RandRSU = "ed506a24c9ad1d92";
    KeyIdForAuthen = 0;
    KeyIdForEncrypt = 0;
    ret,DID,FID,length,File,authenticator,ReturnStatus = \
        reader.GetSecure(accessCredentialsOp, mode, DID, \
            AccessCredentials, keyIdForEncryptOp, FID, offset, length, RandRSU, KeyIdForAuthen, KeyIdForEncrypt)
    print "getSecure\t\t ret=%d,DID=%d,FID=%d,length=%d,\nFile=%s,\nauthenticator=%s,ReturnStatus=%d\n"%\
        (ret,DID,FID,length,File,authenticator,ReturnStatus)
    if ret != 0 :raise CommandExecuteException("ret not 0!")

def readIccInfo():
    # ret,DID,ChannelID,APDULIST,Data,ReturnStatus =  reader.TransferChannel(1, 1, 1, 3, "0500b201cc2b"+ "05805c000204" + "0500b0952b06")
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = reader.TransferChannel(1, 1, 1, 2, "0500b095002b" + "0500b201cc2b"+ "05805c000204")
    print "readIccInfo\t\t ret=%d,DID=%d,ChannelID=%d,APDULIST=%d\n,Data=%s\n,ReturnStatus=%d\n"%\
        (ret,DID,ChannelID,APDULIST,Data,ReturnStatus)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    transfer_channel_res_map["icc_card_sn"] = Data[2:][24:40]
    transfer_channel_res_map["icc_card_provider"] =  Data[2:][0:8] *2
    print "icc_card_sn = %s,icc_card_provider = %s"%(transfer_channel_res_map["icc_card_sn"],transfer_channel_res_map["icc_card_provider"])
    if ReturnStatus != 0:raise CommandExecuteException(u"READ ICC INFO失败,ReturnStatus=%d"%ReturnStatus)

def readPathInfo():
    print "read path info"
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 1, "0500b084005c")
    print "readIccInfo\t\t ret=%d,DID=%d,ChannelID=%d,APDULIST=%d\n,Data=%s\n,ReturnStatus=%d\n"%\
        (ret,DID,ChannelID,APDULIST,Data,ReturnStatus)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    print Data

def initPurcheAndWriteUnionFile():
    init_purchase_cmd = "10805003020b" +"01" + "00000000"+ terminal_number
    write_union_cmd = "3080dcaac82baa29000026043133552be903040301010100000007218400099902b4a84930303032340000000000000000"
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 2, init_purchase_cmd+write_union_cmd)
    print "initPurcheAndWriteUnionFile\t\t ret=%d,DID=%d,ChannelID=%d,APDULIST=%d\n,Data=%s\n,ReturnStatus=%d\n"%\
        (ret,DID,ChannelID,APDULIST,Data,ReturnStatus)
    if ret != 0 :raise CommandExecuteException("ret not 0!")   
    transfer_channel_res_map["icc_random_for_mac1"] = Data[2:][22:30]
    transfer_channel_res_map["icc_trade_sn"] = Data[2:][8:12]
    transfer_channel_res_map["icc_trade_key_version"] = Data[2:][18:20]
    transfer_channel_res_map["icc_trade_key_id"] = Data[2:][20:22]    
    #上面取的都是0的指令返回结果，所以就直接跳过一个字节（长度），后面的取不到，也先不管了；
    print "icc_random_for_mac1 = %s,icc_trade_sn = %s,icc_trade_key_version = %s,icc_trade_key_id = %s"\
        %(transfer_channel_res_map["icc_random_for_mac1"],transfer_channel_res_map["icc_trade_sn"],
          transfer_channel_res_map["icc_trade_key_version"],transfer_channel_res_map["icc_trade_key_id"])
    if ReturnStatus != 0:raise CommandExecuteException(u"initPurcheAndWriteUnionFile失败，ReturnStatus=%d"%ReturnStatus)


def chiperMac1():
    trade_time = "20140916214018"
    debit_money = "00000000"
    random = "00000000"
    icc_trade_sn = "0001"
    debit_money = "00000000"
    trade_type = "09"
    key_version = "01"
    key_id = "00"
    icc_card_sn = "1122334455667788"
    icc_card_provider = "BAFEC4CF" + "BAFEC4CF"

    cmd = "8070000024" + random + icc_trade_sn + debit_money + trade_type + trade_time + key_version + key_id + icc_card_sn + icc_card_provider + "08"
    APDU = "%.2x%s"%(len(cmd)/2,cmd)
    print 'chiperMac APDU = %s'%APDU
    ret,APDUList,Data = reader.PSAM_CHANNEL(0, 1, APDU)
    print "chiperMac1\t\t ret=%d,APDUList=%d,Data=%s"%(ret,APDUList,Data)
    if ret != 0 :raise CommandExecuteException("ret not 0!")

def calc_mac1():
    #dpk_01 = "696F968EACB7F538D9701F558448B186"
#    dpk_01 = "EC7D409E75101DB6F17C74C557BF301E"
    dpk_01 = "00000000000000000000000000000000"
    
    icc_trade_sn = transfer_channel_res_map["icc_trade_sn"]
    random = transfer_channel_res_map["icc_random_for_mac1"]
    print "icc_trade_sn is ", icc_trade_sn
    print "terminal_trade_sn is ", terminal_trade_sn
    input = random + icc_trade_sn + terminal_trade_sn[4:]
    sespk = tdes_raw(dpk_01, input)
    print "sespk is ", sespk
    data = "00000000" + "09" + terminal_number + trade_time
    mac1 = single_mac(sespk, "00000000", data) 
    return mac1

def debitPurche():
    #trade_time = "20140916214018"
    #debit_purche = "14805401000f" + psam_res_map["terminal_trade_sn_and_mac1_ack"][0:8] + \
    #                trade_time + psam_res_map["terminal_trade_sn_and_mac1_ack"][8:16]
    mac1 = calc_mac1()
    debit_purche =  "14805401000f"+ terminal_trade_sn +  trade_time + mac1
    #write_04file = "0a00d6840005220003fffc"

    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 1, debit_purche)
    print "debitPurche\t\t ret=%d,DID=%d,ChannelID=%d,APDULIST=%d\n,Data=%s\n,ReturnStatus=%d\n"%\
        (ret,DID,ChannelID,APDULIST,Data,ReturnStatus)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    transfer_channel_res_map["mac2_tac"] = Data[2:][0:8]
    print "mac2_tac = %s"%transfer_channel_res_map["mac2_tac"]
    if ReturnStatus != 0:raise CommandExecuteException(u"debitPurche失败，ReturnStatus=%d"%ReturnStatus)

def setMMIProc():
    ret,DID,ReturnStatus = reader.SetMMI(1, 1, 0)
    print "ret=%d,DID=%d,ReturnStatus=%d"%(ret,DID,ReturnStatus)
    if ret != 0 :raise CommandExecuteException("set mmi ret not 0!")


def enter_1001():
    cmd = "00a40000021001"
    APDU = "%.2x%s"%(len(cmd)/2,cmd)
    print '%s'%APDU
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 1, APDU)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    print Data

def ext_auth():
    cmd = "0084000008"
    APDU = "%.2x%s"%(len(cmd)/2,cmd)
    print '%s'%APDU
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 1, APDU)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    print APDULIST, Data[2:22]
    random = Data[2:18]
    key = "D24F8DB41A45A9728CE5E9F5C13B4F89"
    crypt = tdes(key, random)
    print crypt
    cmd = "0082000008" + crypt[0:16]
    APDU = "%.2x%s"%(len(cmd)/2,cmd)
    print '%s'%APDU
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 1, APDU)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    print ret, Data

def create_0003():
    cmd = "80E0000307280400F0F0FFFF"
    APDU = "%.2x%s"%(len(cmd)/2,cmd)
    print '%s'%APDU
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 1, APDU)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    print APDULIST, Data[2:22]


def create_0004():
    cmd = "80E0000407280200F0F0FFFF"
    APDU = "%.2x%s"%(len(cmd)/2,cmd)
    print '%s'%APDU
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 1, APDU)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    print APDULIST, Data[2:22]


def create_0009():
    cmd = "80E0000907280100F0F0FFFF"
    APDU = "%.2x%s"%(len(cmd)/2,cmd)
    print '%s'%APDU
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 1, APDU)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    print APDULIST, Data[2:22]

def read_0009():
    cmd = "00b0890020"
    APDU = "%.2x%s"%(len(cmd)/2,cmd)
    print '%s'%APDU
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 1, APDU)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    print APDULIST, Data[2:]

def write_0009():
    cmd = "00d689000151"
    APDU = "%.2x%s"%(len(cmd)/2,cmd)
    print '%s'%APDU
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 1, APDU)
    if ret != 0 :raise CommandExecuteException("ret not 0!")
    print APDULIST, Data[2:22]


def write_0004():
    cmd = "00d6840005110003fffc"
    APDU = "%.2x%s"%(len(cmd)/2,cmd)
    print '%s'%APDU
    ret,DID,ChannelID,APDULIST,Data,ReturnStatus = \
        reader.TransferChannel(1, 1, 1, 1, APDU)
    if ret != 0 :raise CommandExecuteException("write_0004 ret not 0!")
    print APDULIST, Data[2:22]


if __name__ == "__main__":
    openDevice()
    try:
        bst()
        getSecureProc()
        readIccInfo()
        initPurcheAndWriteUnionFile()
        debitPurche()
        setMMIProc()

    finally:
        closeDevice()