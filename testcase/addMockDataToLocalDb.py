#encoding:utf-8
'''
Created on 2015-5-4

@author: user
'''
import sqlite3
import os
import time

cx = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+"/../localData/lanzhouData.db")

idCodeSerial = 10000

for i in range(100000):
    idCodeSerial += 1
    cx.execute("insert into localData values('MOCK PRODUCT','%s','PID','%s',%d);"%(
        "%.6d"%idCodeSerial,"%.8d"%(idCodeSerial+10000),time.time()*1000))
    cx.execute("insert into localData values('MOCK PRODUCT','%s','EPC','%s',%d);"%(
        "%.6d"%idCodeSerial,"%.8d"%(idCodeSerial+13000),time.time()*1000))
    cx.execute(u"insert into localData values('MOCK PRODUCT','%s','中文属性','%s',%d);"%(
        "%.6d"%idCodeSerial,"%.8d"%(idCodeSerial+16000),time.time()*1000))
    cx.commit()
    if i %100 == 0:
        print 'add mock data:%d'%i
cx.close()