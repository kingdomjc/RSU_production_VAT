#encoding:utf-8
"""
模块:

@author:zws
"""
import socket
import binascii
from hhplt.parameters import PARAM
from hhplt.testengine.exceptions import TestItemFailException, AbortTestException
from hhplt.testengine.testcase import superUiLog

DEFAULT_OBU_PORT = 5000

class Fe2Rs232Obu:
    def __init__(self,ip,port):
        self.ip = ip
        self.port = port
        self.con = None

    def initSocket(self):
        try:
            if self.con is not None:
                self.con.close()
            con = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            con.settimeout(2)
            con.connect((self.ip,self.port))
            self.con = con
        except Exception,e:
            print "create socket fail for %s:%s"%(self.ip,str(e))

    def sendAndRecv(self,cmd):
        superUiLog(u"send to ip:%s,%s"%(self.ip,cmd))
        cmd += "\n"
        try:
            if self.con is None:self.initSocket()
            if self.con is None:raise AbortTestException(message = u'FE2RS232板通信失败')
            self.con.sendall(cmd)
            rcvFrame=[]
            for i in range(5):
                f = self.con.recv(64)
                rcvFrame.append(f)
                if f.endswith("\n"):
                    if "PowerOnSuccess" in f:
                        continue
                    else:break
            rcvFrame = "".join(rcvFrame)
            #print self.ip,binascii.hexlify(rcvFrame)
            superUiLog(self.ip+":<-"+binascii.hexlify(rcvFrame))
            #superUiLog(u"receive from ip:%s,%s"%(self.ip,rcvFrame))
            #rcvFrame = rcvFrame.replace("PowerOnSuccess","").replace("\r","").replace("\n","").replace("\x00","")
            #rcvFrame = rcvFrame.decode("iso-8859-1")
            if rcvFrame  != "":return rcvFrame.strip()
            raise Exception(u"OBU串口无响应")
        except Exception,e:
            if self.con is not None:
                self.con.close()
            self.con = None
            raise TestItemFailException(failWeight=10,message=unicode(e))

    def assertSynComm(self,request,response):
        realResponse = self.sendAndRecv(request)
        if realResponse is not None and response not in realResponse:
            raise TestItemFailException(failWeight=10,message=u"%s命令串口响应错误"%request)

    def sendAndGet(self,request):
        return self.sendAndRecv(request)

    def assertAndGetParam(self,request, response):
        r = self.sendAndRecv(request)
        if not r.startswith(response):
            raise TestItemFailException(failWeight=10, message=u'%s命令串口响应错误' % request)
        else:
            return r[len(response):]

    def assertAndGetNumberParam(self,request,response):
        return float(self.assertAndGetParam(request, response))


OBU_CONTAINER = {}  #OBU对象池，key:OBU槽位号,value:Fe2Rs232Obu对象


class Fe2Rs232ObuTestor:
    def __init__(self,obuSlot):
        global OBU_CONTAINER

        if obuSlot not in OBU_CONTAINER:
            OBU_CONTAINER[obuSlot] = Fe2Rs232Obu(PARAM["obuIp-slot%s"%obuSlot],5000)
            OBU_CONTAINER[obuSlot].initSocket()
        self.obu = OBU_CONTAINER[obuSlot]
        self.obuSlot = obuSlot


    def OBUCloseSendSingle(self):
        pass

    def ResetObu(self):
        pass

    def ReadTestFrameNum(self):
        pass

    def TestBattPower(self):
        return self.obu.assertAndGetNumberParam(request="TestBattPower",response="TestBattPower")

    def TestSolarPower(self):
        return self.obu.assertAndGetNumberParam(request="TestSolarPower",response="TestSolarPower")

    def TestCapPower(self):
        return self.obu.assertAndGetNumberParam(request="TestCapPower",response="TestCapPower")

    def TestESAM(self):
        response = self.obu.sendAndGet(request="TestESAM")
        if response.startswith("TestESAMOK"):
            return response[11:]
        elif response == "ResetFail":
            raise TestItemFailException(failWeight = 10,message = u'ESAM复位失败，可能是焊接不良')
        elif response == "SelectMFFail":
            raise TestItemFailException(failWeight = 10,message = u'ESAM选择MF文件失败，可能是焊接不良')
        elif response.startswith("SelectMFErrCode"):
            code = response[-2:]
            raise TestItemFailException(failWeight = 10,message = u'ESAM选择MF文件错误，错误码:'+code)
        elif response == "ReadSysInfoFail":
            raise TestItemFailException(failWeight = 10,message = u'ESAM读系统信息失败')
        elif response.startswith("ReadSysInfoErrCode"):
            code = response[-2:]
            raise TestItemFailException(failWeight = 10,message = u'ESAM读系统信息返回错误，错误码:'+code)
        elif response == "SelectDFFail":
            raise TestItemFailException(failWeight = 10,message = u'ESAM选择DF文件失败')
        elif response.startswith("SelectDFErrCode"):
            code = response[-2:]
            raise TestItemFailException(failWeight = 10,message = u'ESAM选择DF文件返回错误，错误码:'+code)

    def TestHFChip(self):
        self.obu.assertSynComm(request="TestHFChip",response="TestHFChipOK")

    def TestHF(self,times):
        self.obu.assertSynComm(request="TestHF 5",response = "TestHFOK")
        return 0

    def TestUART(self):
        self.obu.assertSynComm(request="TestUART",response="TestUartOK")

    def TestReset(self):
        pass

    def TestBandWidth(self):
        pass

    def TestLedLight(self):
        pass

    def CloseLedLight(self):
        pass

    def TestOLED(self):
        pass

    def TestDirection(self):
        pass

    def IfObuWakeUp(self):
        pass

    def OBUEnterWakeUp(self):
        pass

    def OBUEnterSleep(self):
        self.obu.assertSynComm(request="OBUEnterSleep",response="OBUEnterSleepOK")

    def OBUSendSingle(self):
        pass

    def SetWakenSensi(self,gain,grade):
        pass

    def TestRedLedPara(self,testTime):
        pass

    def TestGreenLedPara(self,testTime):
        pass

    def TestBeepPara(self,testTime):
        pass

    def WriteWakeSensiPara(self,gain,grade):
        pass

    def Test5_8G(self):
        self.obu.assertSynComm(request="Test5_8G",response="Test5_8GOK")

    def TestSendVst(self):
        self.obu.assertSynComm(request="TestSendVst 0x0%s"%self.obuSlot,response="SendVst%sOK"%self.obuSlot)
