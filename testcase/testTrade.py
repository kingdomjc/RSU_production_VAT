#encoding:utf-8
'''
Created on 2014-11-7

@author: user
'''

from hhplt.deviceresource import askForResource,CpuCardTrader
import os,time

os.chdir("../")
def __askForTrader():
    '''获得交易资源(ZXRIS 8801)'''
    sc = askForResource('CpuCardTrader', CpuCardTrader.CpuCardTrader)
    return sc

sc = __askForTrader()
try:
    print sc.readObuId()
except Exception,e:
    print e
    print '获得MAC地址失败'
    
#succ = 0
#fail = 0
#for i in range(5):
#    time.sleep(3)
#    try:
#        sc.testTrade()
#        succ = succ + 1
#    except Exception,e:
#        print e
#        fail = fail + 1
#print "succ=",succ,"fail=",fail

    
