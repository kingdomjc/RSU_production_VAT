#!/usr/bin/env python  
# -*- coding: utf_8 -*-  

import serial
import time
from time import sleep
import struct
#import crc16cctt
import sys
import os
import crcmod.predefined
import binascii

from hhplt.deviceresource import askForResource
from hhplt.deviceresource.LonggangIOBoard import LonggangIOBoardDevice
from hhplt.parameters import PARAM

crc16_xmode = crcmod.mkCrcFun(0x11021,rev=True,initCrc=0xffff,xorOut=0x0000)

macid     = 'ac000001'
start     = '5043' #帧头
read_cmd  = '65'   #读出flash
write_cmd = '6A'   #写入flash
down_cmd  = 'EE'   #开始下载，正式版本

down_cmd_for_test = "EF"    #开始下载测试版本

# # response code
# RSP_NULL    = '6E55'
# RSP_FINISH  = '6649'
# RSP_CMD_OK  = '6F4B'
# RSP_CMD_ERR = '6552'
# RSP_CRC_ERR = '6345'
# RSP_FAILED  = '6144'
# RSP_NO_APP  = '6E41'

RSP_NULL = chr(0x6E)+chr(0x55)
RSP_FINISH = chr(0x66)+chr(0x49)
RSP_CMD_OK = chr(0x6F)+chr(0x4B)
RSP_CMD_ERR = chr(0x65)+chr(0x52)
RSP_CRC_ERR = chr(0x63)+chr(0x45)
RSP_FAILED = chr(0x61)+chr(0x44)
RSP_NO_APP = chr(0x6E)+chr(0x41)

start_first_flag = 1

#ser=serial.Serial("COM12", baudrate=115200, bytesize=8, parity='N', stopbits=1, xonxoff=0,timeout=1)

ser = None  #串口对象
currentBaud = 115200

class IOInputProcessor:
    def processInput(self):
        pass

def switchMode(mode="VER"):
    # 切换串口模式：VER为版本下载，CPC为读取CPCID和SN
    io = askForResource("longgangIO", LonggangIOBoardDevice,impl =  IOInputProcessor(),ioBoardCom = PARAM["ioBoardCom"])
    global currentBaud,ser
    ser.close()
    if mode == "VER":   #版本下载，采用115200波特率
        # if currentBaud != 115200:
        #     currentBaud = 115200
        #     ser.close()
        #     ser = serial.Serial(PARAM["downloadBoardCom"], baudrate = currentBaud , bytesize=8, parity='N', stopbits=1, xonxoff=0,timeout=2)
        # ser.setDTR(True)
        for i in range(5): io[i] = False
        time.sleep(1)
    elif mode == "CPC":
        # if currentBaud != 9600:
        #     currentBaud = 9600
        #     ser.close()
        #     ser = serial.Serial(PARAM["downloadBoardCom"], baudrate = currentBaud , bytesize=8, parity='N', stopbits=1, xonxoff=0,timeout=2)
        #  ser.setDTR(False)
        ser.setRTS(False)
        for i in range(5): io[i] = True
        time.sleep(1.8)
    ser.open()
    

def resetChip():
    # 复位CPC卡
    ser.setRTS(True)
    time.sleep(0.5)
    ser.setRTS(False)

def readCpcIdAndSn():
    # 串口方式读取CPCID和SN
    ser.flushInput()
    ser.write("55AA56000201010256".decode("hex"))
    cpcIdBytes = ser.read(8)
    cpcId = cpcIdBytes.encode("hex").upper()
    print '<',cpcId
    if len(cpcId) != 16:return None,None

    # time.sleep(1)
    ser.write("55AA56000202020256".decode("hex"))
    snBytes = ser.read(4)
    sn = snBytes.encode("hex").upper()
    return cpcId,sn

def openSerial():
    global ser
    ser=serial.Serial(PARAM["downloadBoardCom"], baudrate=115200, bytesize=8, parity='N', stopbits=1, xonxoff=0,timeout=4)
    print "serial.isOpen() =",ser.isOpen()

# function: string convert to hex
def str_to_hex(str_to_switch):	
	init_datahex = binascii.unhexlify(str_to_switch)
	get_hex = []
	for d in init_datahex:
		get_hex.append(int(ord(d)))
	return get_hex

# function: hex convert to string
def hexlist_to_str(hexlist_to_switch):
	ret_res = "%02x" % (hexlist_to_switch[0])
	for d in hexlist_to_switch[1:]:
		temp = "%02x" % d
		ret_res = ret_res + temp
	return ret_res

# calculate CRC
def get_crc(temp_val):
	tem_val = binascii.unhexlify(temp_val)
	crc = crc16_xmode(tem_val)
	crc_list = []
	crc_list.append(crc / 256)
	crc_list.append(crc & 0xFF)
	crc_str = hexlist_to_str(crc_list)
	return crc_str

# get MAC_ID
def get_mac_id(init_macid):
	global start_first_flag
	
	macid_str = init_macid
	
	if start_first_flag != 1:
	    macid_hex = str_to_hex(macid_str)
	    macid_hex[3] += 1
	    if (macid_hex[3] & 0xFF) == 0:
		    macid_hex[3] = 0
		    macid_hex[2] += 1
		    if (macid_hex[2] & 0xFF) == 0:
			    macid_hex[2] = 0
			    macid_hex[1] += 1
			    if (macid_hex[1] & 0xFF) == 0:
				    return None	
	    ret_macid = hexlist_to_str(macid_hex)
	else:
		start_first_flag  = 2 ## flag for other board
		ret_macid = macid_str
		
	return ret_macid


#16进制数值显示
def hexShow(argv):  
    result = ''  
    hLen = len(argv)  
    for i in xrange(hLen):  
        hvol = ord(argv[i])  
        hhex = '%02x'%hvol  
        result += hhex+''  
    return result
    #print 'hexShow:',result  


def revdata(timeval=50):
    data_val=''
    k = 0
    while True:
        time.sleep(0.05)
        while ser.inWaiting()>0 :
            k=0
            data_val +=ser.read(1)
        k=k+1
        if k>=timeval:
            k=0
            break
    return data_val


def Senddataadd0(cmd, data): #地址0x40000
    datalen = '0010'
    dataadd = '040000'
    tmep1 = '55555555'
    ovel = '0100060018070000'
    temp = start + cmd + datalen + dataadd + tmep1 + data + ovel # 55555555 AC000001 01000600 18070000
    crc = get_crc(temp)
    Senddata_str = temp + crc
    Senddata = binascii.unhexlify(Senddata_str)
    ser.write(Senddata)
    #print hexShow(Senddata)

def Senddataadd1(cmd, data):#地址0x40080
    datalen = '0002'
    dataadd = '040080'
    dataval = '0102'
    temp = start + cmd + datalen + dataadd + dataval
    crc = get_crc(temp)
    Senddata_str = temp + crc
    Senddata = binascii.unhexlify(Senddata_str)
    ser.write(Senddata)
    #print hexShow(Senddata)
	
def Senddataadd2(cmd, data): #地址0x40040
    datalen = '0014'
    dataadd = '040040'
    dataval = '55555555011A090F0200020B0E05013C000302FF'
    temp = start + cmd + datalen + dataadd + dataval # 55555555 011A090F 0200020B 0E05013C 000302
    crc = get_crc(temp)
    Senddata_str = temp + crc
    Senddata = binascii.unhexlify(Senddata_str)
    ser.write(Senddata)
    #print hexShow(Senddata)


def download(verCmd = "ee"):
    temp = start + verCmd
    crc = get_crc(temp)
    Senddata_str = temp + crc
    print '>',Senddata_str
    Senddata = binascii.unhexlify(Senddata_str)
    ser.write(Senddata)
    print u"开始下载版本"
    #print u"发送数据↓："+hexShow(Senddata)    


def run():
    global macid
	
    #开始下载版本
    PORT=raw_input(unicode('\n\n按回车键开始-->','utf-8').encode('gbk'))
    flag =1
    while flag:
        flag = 0
        readdata = ''
        download()
        readdata = revdata(10)#读取回复
        if RSP_CMD_OK in readdata:#收到命令格式正确的回复
            readdata = ''
            readdata = revdata(50)#读取回复
            if RSP_FINISH in readdata:#执行完成回复码
                print u"版本下载成功" + hexShow(readdata)
                macid = get_mac_id(macid)
                Senddataadd0(write_cmd, macid)
                print u"--------------->>>MACID：" + macid
                readdata = ''
                readdata = revdata(10) #读取回复                
                if RSP_FINISH in readdata: #执行完成回复码
                    print u"地址0x40000配置成功" + hexShow(readdata)
                    print u"------------------------------>>地址0x40000配置成功"
                else:
                    print u"地址0x40000配置失败" + hexShow(readdata)
                    print u"------------------------------------------->>地址0x40000配置失败XXXXX"


                Senddataadd1(write_cmd, chr(0x00))
                print u"地址0x40080写入数据："                  
                readdata = ''
                readdata = revdata(10)#读取回复                
                if RSP_FINISH in readdata:#执行完成回复码
                    print u"地址0x40080配置成功" + hexShow(readdata)
                    print u"------------------------------>>地址0x40080配置成功"
                else:
                    print u"地址0x40080配置失败" + hexShow(readdata)
                    print u"------------------------------------------->>地址0x40080配置失败XXXXX"
				
                
                Senddataadd2(write_cmd, chr(0x00))
                print u"地址0x40040写入数据："                  
                readdata = ''
                readdata = revdata(10)#读取回复                
                if RSP_FINISH in readdata:#执行完成回复码
                    print u"地址0x40040配置成功" + hexShow(readdata)
                    print u"------------------------------>>地址0x40040配置成功"
                else:
                    print u"地址0x40040配置失败" + hexShow(readdata)
                    print u"------------------------------------------->>地址0x40040配置失败XXXXX"


            else:
                print u"版本下载失败" + hexShow(readdata)
        else:
            print u"命令格式错误或者下载板死机无回复"+hexShow(readdata)
            break




def main():
    global macid
    global start_first_flag
	
    print u"***** 开始下载版本 请输入 1 启动程序下载 *****"
    PORT = input(unicode('请输入1: ','utf-8').encode('gbk'))
    
    macid = raw_input(unicode('请输入起始 MAC_ID(XXXXXXXX): ', 'utf-8').encode('gbk'))
    
    if PORT == 1:
        while True:
            run()


if __name__ == "__main__":
    main()




