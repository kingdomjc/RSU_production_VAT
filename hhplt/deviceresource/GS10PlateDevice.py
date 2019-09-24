#encoding:utf-8
'''
Created on 2014-9-15
GS10工装板
'''
from hhplt.deviceresource import TestResource,TestResourceInitException
from hhplt.deviceresource import AbortTestException,TestItemFailException
import time
from hhplt.testengine.testcase import uiLog,superUiLog
from hhplt.deviceresource.Gs10Bsl import PlateDevice as BslDevice,MODE_SEND_SMALL_POWER
from hhplt.parameters import PARAM

class GS10PlateDevice(TestResource):
    '''工装板入参：串口号'''
    def __init__(self,initParam):
        self.serialPortName = initParam["serialPortName"]

        #BSL及工装板，包含普通串口方式和BSL方式
        self.bslDevice = BslDevice(self.serialPortName)
        self.bslDevice.setCableComsuption(initParam["cableComsuption"])
    
    def initResource(self):
        try:
            self.bslDevice.initResource()
            self.linearSerialComm = LinearSerialComm(self.bslDevice.serial)
        except:
            raise TestResourceInitException(u"初始化GS10工装板失败，请检查设置并重启软件")
    
    def retrive(self):
#        self.linearSerialComm.retrive()
        self.bslDevice.retrive()
        
    def clearSerialBuffer(self):    
        self.bslDevice.serial.flushInput()
    
    def sendAndGet(self,request):
        '''发送并接收，判定逻辑完全由外部进行'''
        return self.linearSerialComm.synComm(request)
    
    def assertSynComm(self,request,response = None,noResponseFailWeight=10,assertFailWeight=10):
        '''直接给出请求响应，自动判定串口通信值是否正确；如果response==None，则不判定响应'''
        superUiLog(u"串口发送:"+request)
        realResponse = self.linearSerialComm.synComm(request)
        superUiLog(u"收到串口响应:"+realResponse)
        if response != None and realResponse != response:
            raise TestItemFailException(failWeight = assertFailWeight,message = u'%s命令串口响应错误'%(request))
        return True
    
    def assertAndGetParam(self,request,response,noResponseFailWeight=10,assertFailWeight=10):
        '''判定响应命令正确与否，并返回输出参数'''
        superUiLog(u"串口发送:"+request)
        r = self.linearSerialComm.synComm(request)
        superUiLog(u"收到串口响应:"+r)
        if not r.startswith(response):
            raise TestItemFailException(failWeight = assertFailWeight,message = u'%s命令串口响应错误'%(request))
        else:
            return r[len(response):]
    
    def assertAndGetNumberParam(self,request,response,noResponseFailWeight=10,assertFailWeight=10):
        '''判定响应，并获得数字返回参数，在上面那个基础上'''
        return float(self.assertAndGetParam(request, response, noResponseFailWeight, assertFailWeight))
    
    def asynSend(self,request):
        '''异步下达指令'''
        self.linearSerialComm.send(request)
    
    def asynReceive(self):
        '''异步接收'''
        return self.linearSerialComm.receive()
    
    def asynReceiveAndAssert(self,assert_response,noResponseFailWeight=10,assertFailWeight=10):
        '''异步接收并验证'''
        response = self.linearSerialComm.receive()
        if response == '':
            raise TestItemFailException(failWeight = noResponseFailWeight,message = u'串口无响应')
#        if not response.startswith(assert_response):
        if assert_response not in response:
            raise TestItemFailException(failWeight = assertFailWeight,message = u'串口响应错误')
        
    def getObuSendPower(self,assertFailWeight = 10):
        '''计算并获得OBU的发送功率'''
        device = self.bslDevice
        device.close_send_single()
        if "powerSendMode" in PARAM and PARAM["powerSendMode"] == "BIG":
            device.set_test_mode(3)
        else:
            device.set_test_mode(MODE_SEND_SMALL_POWER)
            
        read_string = device.read_eeprom(12,12)
        print read_string
        superUiLog(u"read_eeprom:"+read_string)
        if read_string[0:8] != '55AA55AA':
            raise
        slope_k = float(int(read_string[8:16], 16))/1000000.0
        slope_b = float(int(read_string[16:24], 16))/1000.0
        print slope_k
        print slope_b
        superUiLog(u"slop_k:"+str(slope_k)+"slope_b:"+str(slope_b))
        time.sleep(0.5)
        device.obu_send_single()
        time.sleep(1.8)
        adc_value = device.read_adc_cable()
        print adc_value    
        superUiLog(u"adc_value:"+str(adc_value))
        test_power = (adc_value - slope_b)/slope_k + device.cable_comsuption
        if "powerSendMode" in PARAM and PARAM["powerSendMode"] == "BIG":
            test_power -= 12
        device.obu_close_send_single()
        print test_power
        return test_power

    def testWakenSensiWithFixedPowerAndSensi(self,target_power,grade,level):
        '''试验target_power功率下，(grade,level)是否能唤醒，如果唤醒返回true，否则返回false'''
        self.clearSerialBuffer()
        device = self.bslDevice
        device.calibra_target_power(target_power)
        device.set_obu_waken_sensi(grade, level)
        time.sleep(0.2)
        device.send_14k(10)
        time.sleep(0.2)
        return device.test_if_obu_wakeup()

    def adjustWakenSensi(self, target_power,assertFailWeight = 10):
        self.clearSerialBuffer()
        print "target power is %.2f " % target_power
        superUiLog("target power is %.2f " % target_power)
        device = self.bslDevice
        device.calibra_target_power(target_power)
        grade = 0x03
        level = 0x0e
        grade_list = [0x03, 0x02, 0x01, 0x00]
        level_list = [0x0e, 0x0d, 0x0c, 0x0b, 0x0a, 0x09, 0x08, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01]
        yes_waken = False
        not_waken = False
        device.test_if_obu_wakeup()
        try:
            for grade in grade_list:
                for level in level_list:
                    device.set_obu_waken_sensi(grade, level)
                    time.sleep(0.2)
                    device.send_14k(10)
                    time.sleep(0.2)
                    result = device.test_if_obu_wakeup()
                    if result:
                        yes_waken = True
                        break
                    else:
                        not_waken = True
                if yes_waken and not_waken:
                    print "find it , grade is {0:02X} {1:02X}".format(grade, level)
                    uiLog(u'发现%.2f功率的灵敏度灵敏度:grade=0x%.2X,level=0x%.2X'%(target_power,grade,level))
                    break
                if not_waken:
                    print "Can not find grade and level!"
                    uiLog(u'无法发现%.2f功率灵敏度'%target_power)
                    break
        except Exception as e:
            print str(e)
            uiLog(str(e))
#        finally:
#            device.close()
        if yes_waken and not_waken: 
            return (grade, level)
        else:   
            raise TestItemFailException(failWeight = assertFailWeight)


    def testObuRecvSensi(self,power_db,frame_num,assertFailWeight = 10):
        '''接收灵敏度，power_db是个定值，frame_num是发送帧数。实际使用时，这两个值是定死的。
                        接收灵敏度没有高低，只有一个，需求文档中错了'''
        #返回值是唤醒的帧数，判断该帧数是否在正确的范围内
        device = self.bslDevice
        try:
            device.calibra_target_power(power_db)
            device.make_obu_enter_wakeup()
            device.send_test_frame(frame_num)
            recv_num = device.read_frame_num()
        finally:
            device.reset_obu()
        print "recv_num=",recv_num
        return recv_num
    
    def convertAdcToCurrent(self,adc):
        '''静态电流、深度静态电流从ADC值换算成电流（单位uA）'''
        return 0.019*adc - 1.5237
    
    def getPlateWorkingCurrent(self):
        '''读取工装板工作电流'''
        device = self.bslDevice
        device.set_small_current_switch(0)
        current_val = device.read_adc_current()
        return current_val
    
    def testStaticCurrent(self):
        ''' 测试静态电流  测试完静态电流后必须手动复位OBU，此项正在调试中'''
        #但在实际测试中，此为单板测试的最后一项（后面正式版本下载不影响），可以不复位
        #返回值为静态电流值
        try:
            device = self.bslDevice
            device.make_obu_enter_sleep()
            time.sleep(1) #延时时间待定
            device.set_small_current_switch(0)
            current_val = device.read_adc_current()
            if current_val > 10:
                print "current_val=",current_val
                superUiLog("small_current_switch = 0,current_val="+str(current_val))
                raise
            device.set_small_current_switch(1)
            current_val = device.read_adc_current()
            return self.convertAdcToCurrent(current_val)
        finally:
            device.set_small_current_switch(0)

    def testDeepStaticCurrent(self):
        '''深度静态电流测试'''
        try:
            device = self.bslDevice
            device.set_small_current_switch(0)
            current_val = device.read_adc_current()
            print "current_val=",current_val
            superUiLog("small_current_switch = 0,current_val="+str(current_val))
            if current_val > 20:    #原值为10，20151106为测试而修改
                raise
            device.set_small_current_switch(1)
            current_val = device.read_adc_current()
            print "current_val=",current_val
            superUiLog("small_current_switch = 1,current_val="+str(current_val))
            return self.convertAdcToCurrent(current_val)
        finally:
            device.set_small_current_switch(0)

    def testBattPower(self):
        '''测试电池开路电压'''
        #返回值为电池ADC值
        device = self.bslDevice
        device.set_batt_cap_switch(0)
        batt_power = device.read_adc_batt()
        return batt_power
    
    def testCapPower(self):
        '''测试电容开路电压'''
        #返回值为电池ADC值
        device = self.bslDevice
        device.set_batt_cap_switch(1)
        cap_power = device.read_adc_batt()
        return cap_power
    
    def downloadVersion(self,version_file,password_file=None):
        '''下载版本，入参是密码文件、版本文件的路径'''
        device = self.bslDevice
        try:
            #如果不带密码，就擦一下；带密码，就用密码
            if password_file is None:
                device.download_ver(None, version_file, True)
                pass
            else:
                device.download_ver(password_file, version_file, False)
        except:
            raise TestItemFailException(failWeight = 10,message = u'下载版本失败')

    def read_obu_id(self,password_file):
        '''读取OBUID(MAC地址)'''
        device = self.bslDevice
        return device.read_obuid(password_file)

    def startBslWriting(self,passwdFile):
        '''开始BSL写入'''
        device = self.bslDevice
        device.startBslWriting(passwdFile)
    
    def finishBslWritten(self):
        '''结束BSL写入'''
        device = self.bslDevice
        device.finishBslWritten()
        time.sleep(1)
        self.clearSerialBuffer()
        
    def save_obu_id(self,mac):
        '''写OBUID（MAC地址），入参：密码，MAC地址（byte数组）'''
        device = self.bslDevice
        device.bslWriteData([[0x1884,mac]])
    
    def save_CONFIG_BUILD_INFO(self,CONFIG_BUILD_INFO):
        '''写入CONFIG_BUILD_INFO_ADDR'''
        device = self.bslDevice
        device.bslWriteData([[0x1880,CONFIG_BUILD_INFO]])
        
    def read_INFO(self,passwordFile,startAddress):
        '''读取信息区，输入密码文件、开始地址、长度'''
        device = self.bslDevice
        info = device.read_info(passwordFile,startAddress)
        return info
        
    def save_CONFIG_RF_PARA(self,CONFIG_RF_PARA):
        '''写入CONFIG_RF_PARA_ADDR'''
        device = self.bslDevice
        device.bslWriteData([[0x1900,CONFIG_RF_PARA]])
        
    def save_waken_sensi(self, grade_low, level_low,grade_high,level_high):
        '''写唤醒灵敏度参数，passwd:密码,grade_low:低粗调灵敏度,level_low:低细调灵敏度,low,grade_high:高粗调,level_high:高细调'''
        device = self.bslDevice
        device.save_waken_sensi(grade_low,level_low,grade_high,level_high)


#-----------------------------这儿不画一条分割线我看着别扭-----------------------------------

class LinearSerialComm(TestResource):
    '''行式串口通信，入参是serial对象'''
    def __init__(self,param):
        self.serialPort = param
        self.ENDSIGNAL = '\r\n'
    
    def initResource(self):
        try:
            if self.serialPort.getPort() is None:
                self.serialPort.setPort(self.serialPortName)
            if not self.serialPort.isOpen():
                self.serialPort.open()
                time.sleep(1)
        except Exception,e:
            print e
            self.retrive()
            raise AbortTestException(message = u'计算机串口初始化失败，不能继续测试，请检查软硬件设置')
        
    def retrive(self):
        if self.serialPort.isOpen():
            self.serialPort.close()
            time.sleep(1)

    def synComm(self,request,noResponseFailWeight=10):
        '''同步通信，直接返回结果。发送和接收都是以换行(\r\n)为标志的，自动填入并筛除'''
        print "->",request
        self.serialPort.flushInput()
        self.send(request)
        response = self.receive()
        tmpResponse = None
#        if response.rstrip() == 'PowerOnSuccess':   #如果是上电成功信息，再读一行试试
#            tmpResponse = 'PowerOnSuccess'
#            response = self.receive()
        print "<-",response
        #如果串口回乱码，要处理一下
        try:
            response = response.decode('utf-8')
        except UnicodeDecodeError,e:
            response =u'[乱码]'
            
        if response == '':
            if tmpResponse is None:
                raise TestItemFailException(failWeight = noResponseFailWeight,message = u'串口无响应')
            else:
                return tmpResponse
        return response.rstrip()
    
    def send(self,request):
        '''发送'''
        if not request.endswith(self.ENDSIGNAL):
            request+=self.ENDSIGNAL
        try:
            self.serialPort.write(request)
            print "->",request
        except Exception,e:
            print e
            raise AbortTestException(message = u'计算机串口异常，请检查硬件连接并重启软件')
        
    def receive(self):
        '''接收'''
        response = self.serialPort.readline(128)
        print "<-",response
        return response

    
    
    
    