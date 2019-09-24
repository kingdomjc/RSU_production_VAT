#encoding:utf-8
'''
ZXRIS 8801发卡器
'''
from hhplt.deviceresource import TestResource

import os
from os.path import abspath,dirname
from ctypes import windll,create_string_buffer,byref,c_int
import binascii


class PsamCmdException(Exception):
    def __init__(self, str):
        self.error = str
    
    def __str__(self):
        return self.error

class ObuCmdException(Exception):
    def __init__(self, str):
        self.error = str

    def __str__(self):
        return self.error

class DeviceException(Exception):
    def __init__(self, str):
        self.error = str
    
    def __str__(self):
        return self.error

class Zxris8801(TestResource):
    def __init__(self):
        dll_path = "RSUComm.dll"
        print os.path.exists(dll_path)
        self.rid_dll = windll.LoadLibrary(dll_path)
        self.recv_buf = create_string_buffer(1024)
        self.beacon_id = 1

    def initResource(self):
        '''初始化资源'''
        self.open()
        
    def retrive(self):
        '''回收资源'''
        self.close()
        
    def open(self):
        self.reader_fd = self.rid_dll.RSU_Open(2, '', 0)
        return self.reader_fd
    
    def close(self):
        self.rid_dll.RSU_Close(self.reader_fd)

    def config_device(self):
        time = '\x53\xFE\xC5\x9A'
        bst_interval = 5
        retry_interval = 5
        tx_power = 30
        pll_channel = 0
        timeout = 500
        ret = self.rid_dll.RSU_INIT_rq(self.reader_fd, time, bst_interval, retry_interval, tx_power, pll_channel, timeout)
        if ret != 0:
            raise DeviceException("send Config device command fail! %d" % ret)
        c_status = c_int(0)
        c_rsu_info = create_string_buffer(128)
        ret = self.rid_dll.RSU_INIT_rs(self.reader_fd, byref(c_status), byref(c_rsu_info), timeout)
        if ret != 0:
            raise DeviceException("receive Config device response fail! %d" % ret)
        self.rsu_info = c_rsu_info.value
        
        
    
    def active_psam(self, slot):        
        ret = self.rid_dll.PSAM_Reset_rq(self.reader_fd, slot, 0, 1000)
        if ret:
            raise PsamCmdException("active psam fail! errcode: " + str(ret))
        ret = self.rid_dll.PSAM_Reset_rs(self.reader_fd, slot, byref(self.recv_buf), 1000)
        if ret:
            raise PsamCmdException("active psam fail! errcode: " + str(ret))
    
    def exchange_apdu(self, slot, cmd):
        cmd_len  = len(cmd)/2        
        len_string = "%02X" % cmd_len
        
        print 'psam APDU:%s'%(len_string+cmd)
        ret = self.rid_dll.PSAM_CHANNEL_rq(self.reader_fd, slot, 1, len_string+cmd, 5000)
        apdu_list = c_int(0)
        ret = self.rid_dll.PSAM_CHANNEL_rs(self.reader_fd, slot, byref(apdu_list), byref(self.recv_buf), 5000)
        print "PSAM response:%s"%self.recv_buf.value
        if ret == 0:
            if(self.recv_buf.value[-4:] != "9000"):
                raise PsamCmdException("psam cmd return not 9000, errcode is "+ self.recv_buf.value[-4:])
            return self.recv_buf.value[2:]   
        else:
            raise PsamCmdException("psam cmd return errcode: " + str(ret))

    def __getBeaconId(self):
        self.beacon_id = self.beacon_id + 1
        if self.beacon_id > 99999990:
            self.beacon_id = 0
        return "{0:08X}".format(self.beacon_id)

    def invent_obu(self, timeout):
        self.nowObuId = None
        self.nowContractSerial = None
        beacon_id = self.__getBeaconId()
        time = '53FEC59A'
        profile = 0
        mand_application_list = 1
        mand_application =  '4183292020002b'
        profile_list = 0
        ret = self.rid_dll.INITIALISATION_rq(self.reader_fd, beacon_id, time, profile, mand_application_list,\
                                             mand_application, profile_list, timeout)
        if ret != 0:
            raise ObuCmdException("send bst fail %d " % ret)
        c_status = c_int(0)
        c_profile = c_int(0)
        c_application_list = c_int(0)
        c_application = create_string_buffer(128)
        c_obu_configuration = create_string_buffer(128)       
       
        ret = self.rid_dll.INITIALISATION_rs(self.reader_fd, byref(c_status), byref(c_profile), \
                                            byref(c_application_list), byref(c_application), byref(c_obu_configuration), timeout)
        if ret != 0:
            raise ObuCmdException("receive vst fail %d " % ret)
        #self.log()
        self.nowObuId = c_obu_configuration.value[0:8] #当前的MAC地址
        self.nowContractSerial = c_application.value[24:40]  #合同序列号
        self.nowEsamVersion = c_application.value[22:24]    #当前ESAM版本
        self.districtCode = c_application.value[4:12]

    def get_secure(self):
        ret = self.rid_dll.GetSecure_rq (self.reader_fd, 0, 1, 1, 0, 1, 0x01, 0, 0x10, "ed506a24c9ad1d92", 0, 0, 500)
        if ret != 0:
            raise ObuCmdException("send get_secure fail %d " % ret)

        did = c_int(0)
        fid = c_int(0)
        length = c_int(0)
        pfile = create_string_buffer(128)
        authenticator = create_string_buffer(128)
        status = c_int(0)        
        ret = self.rid_dll.GetSecure_rs(self.reader_fd, byref(did), byref(fid), byref(length), byref(pfile),\
                                        byref(authenticator), byref(status), 500)
        if(ret != 0):
            raise ObuCmdException("receive get_secure response faile %d " % ret)
        if(status.value != 0):
            raise ObuCmdException("get_secure status error %d " % status.value)
        return pfile.value

    def transfer_channel(self, apdu_size, apdu,channelId=1):
        ret = self.rid_dll.TransferChannel_rq(self.reader_fd, 1, 1, channelId,  apdu_size, apdu, 500)
        if ret != 0:
            raise ObuCmdException("send transfer_channel fail %d " % ret)
        did = c_int(0)
        channel_id = c_int(0)
        apdu_size = c_int(0)
        apdu = create_string_buffer(256)
        status = c_int(0)
        ret = self.rid_dll.TransferChannel_rs(self.reader_fd, byref(did), byref(channel_id), byref(apdu_size),
                       byref(apdu), byref(status), 500)
        if(ret != 0):
            raise ObuCmdException("receive transfer_channel response fail %d " % ret)
        if(status.value != 0):
            raise ObuCmdException("receive transfer_channel status error %d " % status.value)
        res_list = []
        pos = 0
        apdu_str = apdu.value
        for x in range(apdu_size.value):
            len = ord(binascii.unhexlify(apdu_str[pos*2 : (pos+1)*2]))
            ack = apdu_str[((pos+1)*2):((pos+len+1))*2]
            res_list.append(ack)
            pos += (len+1)
        return res_list

    def set_mmi(self):
        ret = self.rid_dll.SetMMI_rq(self.reader_fd, 1, 1, 0, 500)
        if ret != 0:
            raise ObuCmdException("send setmmi fail %d " % ret)
        did = c_int(0)
        status = c_int(0)
        ret = self.rid_dll.SetMMI_rs(self.reader_fd, byref(did), byref(status), 500)
        if(ret != 0):
            raise ObuCmdException("receive setmmi fail %d " % ret)
        if(status.value != 0):
            raise ObuCmdException("receive setmmi status error %d " % status.value)

