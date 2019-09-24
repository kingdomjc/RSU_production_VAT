#encoding:utf-8
'''
Created on 2015-9-2
测试nulink
@author: user
'''

import os
from hhplt import utils
import time




def readData():
    '''测试读取信息区'''
    if os.path.isfile("data2.bin"):
        os.remove("data2.bin")
    r = os.popen("NuLink.exe -r DATAROM data2.bin")
    dr = r.read()
    if "Write DATAROM to FILE: data2.bin Finish." in dr:
        f = open("data2.bin","rb")
        data = f.read(128)
        f.close()
        print utils.toHex(data)
    else:
        print dr.strip()

def downloadVersion():
    '''下载版本并校验'''
    vf = "versions/V2.00.00.00-VAT.hex"
    #擦除版本文件
    r = os.popen("NuLink.exe -e APROM")
    dr = r.read()
    if "Erase APROM finish" in dr:
        print 'earse aprom finished'
    else:
        print 'earse aprom failed!'
        return
    #下载版本文件
    dr = os.popen("NuLink.exe -w APROM %s"%vf).read()
    if "Write APROM finish" in dr:
        print 'write aprom finished'
    else:
        print 'write aprom failed!'
        return
    #校验版本下载
    dr = os.popen("NuLink.exe -v APROM %s"%vf).read()
    if "Verify APROM DATA success" in dr:
        print 'verify version file success'
    else:
        print 'verify version file failed'
        return
    
def writeInfoData():
    '''写信息区'''
    CONFIG_BUILD_INFO = "555555552401f01a0101200100010000"
    CONFIG_RF_PARA = "55555555030f020a0400020600"
    toWriteFileInHex = CONFIG_BUILD_INFO+"ff"*48+CONFIG_RF_PARA
    toWriteFileInByte = bytearray([int(toWriteFileInHex[h:h+2],16) for h in range(0,len(toWriteFileInHex),2)])
    hxfile = open("infoData.bin","wb")
    hxfile.write(toWriteFileInByte)
    hxfile.close()
    print 'write to target file:infoData.bin'
    
    #擦除Info区
    r = os.popen("NuLink.exe -e DATAROM")
    dr = r.read()
    if "Erase DATAROM finish" in dr:
        print 'earse data rom finished'
    else:
        print 'earse data rom failed!'
        return
    
    #写Info区
    dr = os.popen("NuLink.exe -w DATAROM infoData.bin").read()
    if "Write DATAROM finish" in dr:
        print 'write data rom finished'
    else:
        print 'write data rom failed'
        return


if __name__ == '__main__':
#    print time.time() 
#    downloadVersion()
#    print time.time()
#    writeInfoData()
    readData()



