#encoding:utf-8
'''
Created on 2014-10-8
GS10的BSL方式工装板

侯哥编写，大部分直接整合
这里面的逻辑，不完全都是BSL的，也有普通串口的。


@author: 张文硕
'''

from msp430.bsl5.uart import *
from msp430.bsl5 import bsl5
from msp430 import memory
import time
from hhplt.deviceresource import TestResource
from hhplt.parameters import PARAM
from hhplt.testengine.testcase import uiLog,superUiLog

ET_TX_LEVEL_78DB = 0
ET_TX_LEVEL_72DB = 1
ET_TX_LEVEL_62DB = 2
ET_TX_LEVEL_51DB = 3
ET_TX_LEVEL_35DB = 4
ET_TX_LEVEL_12DB = 5
ET_TX_LEVEL_N2DB = 6
ET_TX_LEVEL_N7DB = 7

MODE_SEND_SMALL_POWER = 0
MODE_TEST_SEND_POWER = 1
MODE_SEND_BIG_POWER = 2
MODE_TEST_RECV_POWER = 3

__PASSWORD_FILE_MAP={}
def _getPasswordFromFile(filename):
    '''从文件获得密码，做一层缓存以加快效率'''
    global __PASSWORD_FILE_MAP
    if filename is None:
        return "\xFF"*32
    if filename in __PASSWORD_FILE_MAP:
        return __PASSWORD_FILE_MAP[filename]
    passwd = memory.load(filename).get_range(0xffe0, 0xffff)
    __PASSWORD_FILE_MAP[filename] = passwd
    return passwd


class PlateDevice(SerialBSL5,TestResource):
    
    ##########Override from TestResource#############
    def initResource(self):
        '''初始化资源'''
        if not self.isOpen:
            self.open()
            self.isOpen = True
            time.sleep(1)
    
    def retrive(self):
        '''回收资源'''
        if self.isOpen:
            self.close()
            self.isOpen = False
            time.sleep(1)
    #################################################
    
    def setCableComsuption(self,cable_comsuption):
        '''设置线缆损耗'''
        self.cable_comsuption = cable_comsuption
    
    def __init__(self,com_port):
        super(PlateDevice, self).__init__()
        self.com_port = com_port
        self.cable_comsuption = 1
        self.isOpen = False #add by zhangwenshuo，是否已打开，做一个标志位，避免频繁开关
        
        #下面这个表以后有可能变，后续考虑是不是需要提到配置文件中
        self.datt_ref_table = {-52:34, -51:36, -50:38, -49:40, -48:42, -47:44, -46:46, 
                               -45:48, -44:50, -43:52, -42:54, -41:56, -40:58, -39:60,
                                -38:62, -37:63}
        
    def open(self):
        super(PlateDevice, self).open(self.com_port, 115200)
        self.serial.parity=serial.PARITY_NONE
#        self.serial.timeout = 5
        self.serial.setTimeout(15)
        self.invertRST = True
        self.invertTEST = True
        self.set_RST(True)
        self.set_TEST(False)
        #time.sleep(0.5)

    def forward_and_check(self, command, expect):
        self.serial.flushInput()
        self.serial.write(command)
        response = self.serial.readline(100)
        print command
        print response
        superUiLog("command:"+command.strip()+",response:"+response.strip())
        return expect in response

    def set_tx_level(self, tx_level):
        command = "SetEtTxLevel %02X\r\n" % tx_level
        if not self.forward_and_check(command, "SetTxLevelOK"):
            raise
        

    def set_datt(self, datt_key):
        command = "SetDATT %02X\r\n" % datt_key
        if not self.forward_and_check(command, "SetDATTOK"):
            raise

    def send_single(self):
        if not self.forward_and_check("EtSendSingle\r\n", "EtSendSingleOK"):
            raise

    def close_send_single(self):
        if not self.forward_and_check("EtCloseSingle\r\n", "EtCloseSingleOK"):
            raise

    def obu_send_single(self):
        if not self.forward_and_check("OBUSendSingle\r\n", "OBUSendSingleOK"):
            pass
            #raise

    def obu_close_send_single(self):
        if not self.forward_and_check("OBUCloseSendSingle\r\n", "OBUCloseSendOK"):
            pass
            #raise

    def send_14k(self, num):
        if not self.forward_and_check("EtSend14k %d\r\n" % num, "EtSend14kOK"):
            raise

    def read_adc_cable(self):  #测试obu发射功率ADC的值
        self.serial.write("TestReadADC 0 1\r\n")
        response = self.serial.readline(128)
        head, value = response.split()
        if head != "ReadADC":
            raise
        return float(value)

    def read_adc_current(self): #测试静态电流的adc值
        self.serial.write("TestReadADC 1 7\r\n")
        response = self.serial.readline(128)
        print "->TestReadADC 1 7\r\n","<-",response
        if "ReadADC" not in response:
            raise Exception("serial recv:"+response)
        value = response.split("ReadADC")[1]
        return float(value)

    def read_adc_batt(self): #测试电池电容adc的值
        self.serial.write("TestReadADC 1 6\r\n")
        response = self.serial.readline(128)
        if "ReadADC" not in response:
            raise Exception("serial recv:"+response)
        value = response.split("ReadADC")[1]
        return float(value)

    def set_test_mode(self, mode):
        if not self.forward_and_check("SetTestMode %d\r\n" % mode, "SetTestModeOK"):
            raise

    def set_batt_cap_switch(self, mode):
        if not self.forward_and_check("SetBattPowerSwitch  %d\r\n" % mode, "SetBattPowerSwitchOK"):
            raise

    def set_small_current_switch(self, mode):
        if not self.forward_and_check("SetSmallCurrentSwitch %d\r\n" % mode, "SetSmallCurrentSwitchOK"):
            raise
        
    def bsl_mass_erase(self):
        try:
            self.BSL_RX_PASSWORD(30*'\xff'+2*'\x00') 
        except:
            pass

    def bsl_reset_obu(self):
        self.set_RST(False)
        time.sleep(0.5)
        self.set_RST(True)
        time.sleep(0.5)

    def download_ver(self, old_file_path=None, new_file_path=None, mass_erase=False):
        self.forward_and_check("BSL\r\n", "BSLOK")
        self.serial.baudrate = 9600
        self.serial.parity = serial.PARITY_EVEN
        self.serial.timeout = 1        
        try:
            download_data = memory.Memory() # prepare downloaded data        
            data = memory.load(new_file_path)
            download_data.merge(data)
            self.start_bsl()
            if mass_erase:
                self.bsl_mass_erase()
                print "Mass Erase Success!\r\n"
            passwd = _getPasswordFromFile(old_file_path)
            self.BSL_RX_PASSWORD(passwd)
            self.set_baudrate(115200)
            for segment in download_data:
                print "Write segment at 0x%04x %d bytes\n" % (segment.startaddress, len(segment.data))
                uiLog(u"版本信息正在写入位置: 0x%04x %d bytes"%(segment.startaddress, len(segment.data)))
                data = segment.data
                if len(data) & 1:
                    data += '\xff'
                self.memory_write(segment.startaddress, data)
            print "version downloaded successfully, starting read and verification." 
            uiLog(u"版本写入完成，正在校验...")   
            #读回版本并验证
            for segment in download_data:
                sg = self.memory_read(segment.startaddress, len(segment.data))
                #这是bytearray对象
                if sg != segment.data:
                    raise
                print "verify %2.X OK"%segment.startaddress
            uiLog(u'版本校验成功')    
                
        except Exception as e:
            print "Program fail! " + str(e)
            superUiLog("Program fail! " + str(e))
            raise e
        else:
            print "Program OK!"
        finally:
            self.quit_bsl()
            self.quit_bsl()
            print "quit bsl"
            superUiLog("quite bsl")
            self.serial.baudrate = 115200
            self.serial.parity = serial.PARITY_NONE
            self.serial.timeout = 5
            self.set_TEST(False)

    def read_obuid(self, old_file_path):
        obuid = ""
        self.forward_and_check("BSL\r\n", "BSLOK")
        self.serial.baudrate = 9600
        self.serial.parity = serial.PARITY_EVEN
        self.serial.timeout = 1        
        try:
            self.start_bsl()
            passwd = _getPasswordFromFile(old_file_path)
            self.BSL_RX_PASSWORD(passwd)
            obuid = self.memory_read(0x1884, 4)
        except Exception as e:
            print "Read obuid fail! " + str(e)
            superUiLog("Read obuid fail! " + str(e))
            raise e
        else:
            print "Read obuid success!"
            superUiLog("Read obuid success!")
        finally:
            self.quit_bsl()
            self.quit_bsl()
            print "quit bsl"
            superUiLog("quite bsl")
            self.serial.baudrate = 115200
            self.serial.parity = serial.PARITY_NONE
            self.serial.timeout = 5
            self.set_TEST(False)
        print repr(obuid)
        return obuid

    def write_eeprom(self, offset, hex_string):
        if not self.forward_and_check("WriteEEPROM {0:d} {1:s}\r\n".format(offset, hex_string), "WriteEEPROMOK"):
            raise

    def read_eeprom(self, offset, size):
        self.serial.write("ReadEEPROM  {0:d} {1:d}\r\n".format(offset, size))
        response = self.serial.readline(128)
        head, value = response.split()
        if head != "ReadEEPROM":
            raise
        return value

    def test_if_obu_wakeup(self):
        self.serial.write("IfObuWakeUp\r\n")
        print "IfObuWakeUp\r\n"
        superUiLog("command:IfObuWakeUp")
        response = self.serial.readline(128).strip()
        print response
        superUiLog("response:"+response)
        if response == "TWFALSE":
            return False
        elif response == "TWOK":
            return True
        else:
            raise

    def set_obu_waken_sensi(self, grade, level):
        command = "SetWakenSensi 2 0x{0:02X} 0x{1:02X}\r\n".format(grade, level)
        if not self.forward_and_check(command, "SetWakenSensiOK"):
            raise 

    def read_send_power_constant(self):
        read_string = self.read_eeprom(0,8)
        if read_string[0:8] != '55AA55AA':
            raise
        constant = int(read_string[8:], 16)
        return constant

    def read_recv_power_constant(self):
        read_string = self.read_eeprom(8,8)
        if read_string[0:8] != '55AA55AA':
            raise
        constant = int(read_string[8:], 16)
        return constant

    def make_obu_enter_wakeup(self):
        if not self.forward_and_check("OBUEnterWakeUp\r\n", "OBUEnterWakeUpOK"):
            raise

    def make_obu_enter_sleep(self):
        if not self.forward_and_check("OBUEnterSleep\r\n", "OBUEnterSleepOK"):
            raise

    def send_test_frame(self, frame_num):
        command = "SendTestFrame {0}\r\n".format(frame_num)
        if not self.forward_and_check(command, "SendTestFrameOK"):
            raise

    def reset_obu(self):
        if not self.forward_and_check("ResetObu\r\n", "PowerOnSuccess"):
            raise

    def read_frame_num(self):
        self.serial.write("ReadTestFrameNum\r\n")
        print "ReadTestFrameNum\r\n"
        superUiLog("command:ReadTestFrameNum")
        response = self.serial.readline(128).strip()
        print response
        superUiLog("response:"+response)
        if not response or (len(response) < 6) or (response[0:5] != "TRNum"):
            raise
        recv_num = int(response[5:])
        return recv_num

    def calibra_target_power(self, target_power):
        '''calc target adc'''
        target_power = target_power + self.cable_comsuption
        ref_datt = 0x1f
        if(self.datt_ref_table.has_key(target_power)):
            ref_datt = self.datt_ref_table[target_power]

        read_string = self.read_eeprom(0,12)
        if read_string[0:8] != '55AA55AA':
            raise
        slope_k = float(int(read_string[8:16], 16))/1000000.0
        slope_b = float(int(read_string[16:24], 16))/1000.0
        target_adc_value = target_power*slope_k + slope_b
        self.calibra_target_adc(target_adc_value, ref_datt)
        

    def calibra_target_adc(self, target_adc_value, ref_datt):
        self.set_tx_level(ET_TX_LEVEL_72DB)
        datt = ref_datt
        self.set_datt(datt)
        self.set_test_mode(MODE_TEST_SEND_POWER)
        self.send_single() 
        time.sleep(0.2)
        adc_value = self.read_adc_cable()
        while(abs(adc_value -target_adc_value) > 5):
            if adc_value > target_adc_value:
                datt -= 1
                if datt < 0:
                    datt = 0
                    #break
                    raise
            else:
                datt += 1
                if datt > 0x3f:
                    datt = 0x3f
                    break
                    raise
            self.set_datt(datt)
            time.sleep(0.2)
            adc_value = self.read_adc_cable()
        self.close_send_single()
        if "powerSendMode" in PARAM and PARAM["powerSendMode"] == "BIG":
            print 'set test mode BIG'
            self.set_test_mode(MODE_SEND_BIG_POWER)
        else:
            self.set_test_mode(MODE_SEND_SMALL_POWER)
        return adc_value
    
    #####################################################################################
    
    def readWholeInfo(self):
        '''读取整个Info区'''
        segments = [0x1800,0x1880,0x1900,0x1980]
        wholeInfo = []
        for segmentStart in segments:
            wholeInfo.append(self.memory_read(segmentStart, 0x80))
        return wholeInfo
        
    def read_info(self,passwordFile,startAddress):
        '''读取信息区'''
        self.startBslWriting(passwordFile)
        return self.memory_read(startAddress, 0x80)
        
        
    def bslWriteData(self,addressDataList):
        '''bsl方式写入参数，入参passwd:密码，addressDataList:[[地址,数据],[地址,数据]……]，按顺序排列'''
        upload_data = memory.Memory()
        wholeStart = addressDataList[0][0]
        
        segmentStart = [0x1800,0x1880,0x1900,0x1980][int((wholeStart-0x1800)/0x80)]
        
        upload_data.append(memory.Segment(segmentStart, self.memory_read(segmentStart, 0x80)))
        
        for ad in addressDataList:
            address = ad[0]
            data = ad[1]
            upload_data.set(address, data)
        
        self.BSL_ERASE_SEGMENT(segmentStart) 
        for segment in upload_data:
            print "Write segment at 0x%04x %d bytes\n" % (segment.startaddress, len(segment.data))
            superUiLog("Write segment at 0x%04x %d bytes\n" % (segment.startaddress, len(segment.data)))
            data = segment.data
            if len(data) & 1:
                data += '\xff'
            self.memory_write(segment.startaddress, data)
            
        print 'bsl write successfully, starting read and verification.'
        uiLog(u"BSL 写入完成，正在校验...")
        for segment in upload_data:
            sg = self.memory_read(segment.startaddress, len(segment.data))
            if sg != segment.data:
                raise
            print "verify %2.X OK"%segment.startaddress
        uiLog(u"BSL校验成功")
    
    def startBslWriting(self,passwdFile):
        '''开始BSL写入'''
        uiLog(u"开始BSL方式写入...")
        self.forward_and_check("BSL\r\n", "BSLOK")
        self.serial.baudrate = 9600
        self.serial.parity = serial.PARITY_EVEN
        self.serial.timeout = 1
        self.start_bsl()
        passwd = _getPasswordFromFile(passwdFile)    
        self.BSL_RX_PASSWORD(passwd)
        self.set_baudrate(115200)
        
    def finishBslWritten(self):
        '''完成BSL写入'''
        self.quit_bsl()
        self.quit_bsl()
        print "quit bsl"
        superUiLog("quit bsl")
        self.serial.baudrate = 115200
        self.serial.parity = serial.PARITY_NONE
        self.serial.timeout = 5
        self.set_TEST(False)
        uiLog(u"BSL方式写入完成")
    
    def save_waken_sensi(self,grade_low, level_low,grade_high,level_high):
        '''设置唤醒灵敏度，入参：type类型（low/high）,grade_low:低粗调灵敏度,level_low:低细调灵敏度,low,grade_high:高粗调,level_high:高细调'''
        self.bslWriteData([[0x1900,'\x55\x55\x55\x55'],
                                    [0x1904,chr(grade_high)+chr(level_high)],
                                    [0x1906,chr(grade_low)+chr(level_low)]]),
    
    #####################################################################################

   

