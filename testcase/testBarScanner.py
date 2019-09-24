#encoding:utf-8
'''
Created on 2014-11-14
条码枪调试
@author: user
'''


import serial
import time

scannerSerial = serial.Serial(port="com5",baudrate = 9600,timeout = 5)

startScanCommand = bytearray([0x03,0x53,0x80,0xff,0x2a,0x00])
while True:
    time.sleep(5)
    scannerSerial.flushInput()
    scannerSerial.write(startScanCommand)
    result = scannerSerial.readline()
    ack = result[0:5]
    data = result[5:]
    if data == "":
        print "empty"
        continue
    print data
