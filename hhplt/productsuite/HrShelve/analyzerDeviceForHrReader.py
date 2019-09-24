#encoding:utf-8
"""
模块: 海尔测试阅读器单板使用的频谱仪
用于读取功率

@author:zws
"""
import socket,time

from hhplt.deviceresource import TestResource, TestResourceInitException

#频谱仪设备初始化脚本-阅读器
from hhplt.parameters import PARAM

SPECTRUM_DEVICE_CONFIG_SCRIPT =''':SYSTem:PRESet
:SENSe:FREQuency:CENTer 13560000
:SENSe:FREQuency:SPAN 0
:SENSe:BWIDth:RESolution 8000000
:DISPlay:WINDow:TRACe:Y:SCALe:RLEVel:OFFSet %(rel_ampl)f
:SENSe:SWEep:TIME 1e-05
:DISPlay:WINDow:TRACe:Y:SCALe:RLEVel 45
:TRIGger:SEQuence:RFBurst:LEVel:ABSolute 30
:TRIGger:SEQuence:RFBurst:DELay 1e-05
:TRIGger:SEQuence:RFBurst:DELay:STATe 1
:TRIGger:SEQuence:RF:SOURce RFBurst
:CALCulate:MARKer1:MODE POSition
:CALCulate:MARKer1:X 5e-06'''


#矢量网络分析仪初始化脚本-功分器
VECTOR_NETWORK_ANALYZER_CONFIG_SCRIPT_FOR_DIVIDER = ''':MMEMory:LOAD:STATe "%(file)s"
:SENSe1:FREQuency:CENTer 13560000
:SENSe1:FREQuency:SPAN 10000000
:CALCulate1:SELected:MARKer1:ACTivate
:CALCulate1:SELected:MARKer1:X 13560000
:DISPlay:WINDow:SPLit D12_34
:CALCulate1:PARameter1:COUNt 3
:DISPlay:TABLe:TYPE MARKer
:DISPlay:TABLe:STATe 1'''


#矢量网络分析仪初始化脚本-天线
VECTOR_NETWORK_ANALYZER_CONFIG_SCRIPT_FOR_ANTENNA = ''':MMEMory:LOAD:STATe "%(file)s"
:SENSe1:FREQuency:CENTer 13560000
:SENSe1:FREQuency:SPAN 10000000
:CALCulate1:PARameter1:SELect
:DISPlay:WINDow:SPLit D1X1
:CALCulate1:PARameter1:COUNt 1'''


class VisaDeviceOnNetwork(TestResource):
    # 符合VISA标准的分析设备，基于TCPIP的
    INIT_DEVICE_SCRIPT = None
    DEVICE_NAME = u"基础设备"
    CMD_SPLITER = '\r\n'

    def __init__(self,ip,port):
        self.ip = ip
        self.port = port
        self.con = None    # 通信对象

    def __initDeviceConfig(self):
        for cmd in self.INIT_DEVICE_SCRIPT.split("\n"):
            self.con.send(cmd+self.CMD_SPLITER)
            time.sleep(2)
            print cmd
            self.con.send(":SYST:ERR?\n")
            try:
                print self.con.recv(64)
            except:
                pass

    def initResource(self):
        try:
            self.con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.con.settimeout(5)
            self.con.connect((self.ip, self.port))
            self.__initDeviceConfig()
        except Exception,e:
            import traceback
            print traceback.format_exc()
            raise TestResourceInitException(u"初始化%s失败:%s"%(self.DEVICE_NAME,e))

    def retrive(self):
        self.con.close()

    @staticmethod
    def transGDigitalToNumber(value):
        # 将科学计数法表示的数字字符串转换成数字
        a,b = value.split("E")
        return float(a)*(10**int(b))

    def readValue(self,readCmd):
        self.con.send(readCmd)
        try:
            rcvCmd = self.con.recv(64)
        except:
            pass
        print rcvCmd
        return rcvCmd



class SpectrumAnalyzerForHrReader(VisaDeviceOnNetwork):
    INIT_DEVICE_SCRIPT = SPECTRUM_DEVICE_CONFIG_SCRIPT
    DEVICE_NAME = u"频谱仪"

    def __init__(self,param):
        self.INIT_DEVICE_SCRIPT = SPECTRUM_DEVICE_CONFIG_SCRIPT%({"rel_ampl":PARAM["saRelAmpl"]})
        VisaDeviceOnNetwork.__init__(self,param["spectrumAnalyzerIp"],param["spectrumAnalyzerPort"])

    def resetForRead(self):
        self.con.send(":TRIGger:SEQuence:RF:SOURce IMMediate\r\n")
        self.con.send(":TRIGger:SEQuence:RF:SOURce RFBurst\r\n")

    def setForIdleRead(self):
        self.con.send(":TRIGger:SEQuence:RF:SOURce IMMediate\r\n")

    def readPowerValue(self):
        # 读取功率值
        pwr = self.readValue(":CALCulate:MARKer1:Y?\r\n")
        return self.transGDigitalToNumber(pwr)


class VectorNetworkAnalyzerForHrDivider(VisaDeviceOnNetwork):
    INIT_DEVICE_SCRIPT = VECTOR_NETWORK_ANALYZER_CONFIG_SCRIPT_FOR_DIVIDER
    DEVICE_NAME = u"矢量网络分析仪"
    CMD_SPLITER = "\n"

    def __init__(self,param):
        VisaDeviceOnNetwork.__init__(self,param["vectorNetworkAnalyzerIp"],param["vectorNetworkAnalyzerPort"])
        self.INIT_DEVICE_SCRIPT = VECTOR_NETWORK_ANALYZER_CONFIG_SCRIPT_FOR_DIVIDER%{"file":PARAM["VNAStateFile"]}

    def readLossAndFreq(self,trace):
        # 读取回损值、第二个参数、频率。入参是选择的trace
        self.con.send(':CALCulate1:PARameter%d:SELect\n'%trace)
        temp_values = self.readValue(':CALCulate1:SELected:MARKer1:DATA?\n')
        temp_values = temp_values.split(",")
        data0 = temp_values[0] #读取marker 回损值
        data1 = temp_values[1] #读取marker第二参数，该项测试为0，可以忽略；
        data2 = temp_values[2] #读取marker 频率值，频率显示单位为Hz，可以修改为MHz；
        return self.transGDigitalToNumber(data0),data1,self.transGDigitalToNumber(data2)


class VectorNetworkAnalyzerForHrAntenna(VisaDeviceOnNetwork):
    INIT_DEVICE_SCRIPT = VECTOR_NETWORK_ANALYZER_CONFIG_SCRIPT_FOR_ANTENNA
    DEVICE_NAME = u"矢量网络分析仪"
    # CMD_SPLITER = "\n"

    def __init__(self,param):
        VisaDeviceOnNetwork.__init__(self,param["vectorNetworkAnalyzerIp"],param["vectorNetworkAnalyzerPort"])
        self.INIT_DEVICE_SCRIPT = VECTOR_NETWORK_ANALYZER_CONFIG_SCRIPT_FOR_ANTENNA%{"file":PARAM["VNAStateFile"]}

    def readMarkerAntFreq(self,marker,freq):
        # 读取某个频点下的freq的值
        self.con.send(':CALCulate1:SELected:MARKer%d:ACTivate\n'%marker)
        self.con.send(':CALCulate1:SELected:MARKer%d:X %G\n' % (marker,freq))
        temp_values = self.readValue(':CALCulate1:SELected:MARKer%d:DATA?\n'%marker)
        temp_values = temp_values.split(",")
        data0 = temp_values[0] #读取marker 回损值
        data1 = temp_values[1] #读取marker第二参数，该项测试为0，可以忽略；
        data2 = temp_values[2] #读取marker 频率值，频率显示单位为Hz，可以修改为MHz；
        return self.transGDigitalToNumber(data0),data1,self.transGDigitalToNumber(data2)

    def readMarker6(self):
        for cmd in ''':CALCulate1:SELected:MARKer6:ACTivate
:CALCulate1:SELected:MARKer6:FUNCtion:TYPE MINimum
:CALCulate1:SELected:MARKer6:FUNCtion:EXECute
:CALCulate1:SELected:MARKer6:FUNCtion:EXECute
:CALCulate1:SELected:MARKer6:FUNCtion:EXECute'''.split("\n"):
            self.con.send(cmd.strip()+"\n")
        temp_values = self.readValue(':CALCulate1:SELected:MARKer6:DATA?\n')
        temp_values = temp_values.split(",")
        data05 = temp_values[0] #获取marker S参数值
        data15 = temp_values[1]
        data25 = temp_values[2] #获取marker 频点位置
        return self.transGDigitalToNumber(data05), data15, self.transGDigitalToNumber(data25)

