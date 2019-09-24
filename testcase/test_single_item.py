#encoding:utf-8
'''
Created on 2014-10-8
其他一些测试用例
@author: user
'''
from hhplt.parameters import SESSION,GLOBAL,PARAM
from hhplt.testengine.server import ServerBusiness,serialCode,retrieveSerialCode
from hhplt.testengine.exceptions import TestItemFailException
import time

class _WndMock:
    def emit(self,*p):
        for msg in p:
            print "--------",msg,"--------"
        
GLOBAL["mainWnd"]=_WndMock()
SESSION["serverIp"] = "127.0.0.1"
PARAM["gs10PlateDeviceCom"]="com3"
#for i in range(15):
#    print serialCode("surface.obuid")



def processException(e):
    print e.message
    if e.output is not None:
        for k in e.output.keys():
            print k,"=",e.output[k]


def ET(FN,stopIfFail = True):
    '''这东西用于测试'''
    try:
        result = FN(None)
        print '=========',FN.__name__,'测试成功========='
        if result is not None:
            for k in result.keys():
                print k,"=",result[k]
        print '==================================================='
    except Exception,e:
        if not stopIfFail:
            processException(e)
        else:
            raise e

from hhplt.productsuite.gs10 import board_rf_conduct,board_digital,battery,overall_unit
try:
#    pass
#    ET(board_digital.T_02_testVersionDownload_A)
#    print '等待10秒，请复位OBU'
#    time.sleep(10)
#    ET(board_digital.T_03_rs232Test_A)
#    ET(board_digital.T_05_capacityVoltage_A)
#    ET(board_digital.T_08_esam_A)
#    ET(board_rf_conduct.T_01_readRfCard_A)
#    ET(board_rf_conduct.T_02_wakeupSensitivity_A)
#    ET(board_rf_conduct.T_03_receiveSensitivity_A)
#    ET(board_rf_conduct.T_04_transmittingPower_A)
#    ET(board_rf_conduct.T_05_staticCurrent_A)
#    ET(board_rf_conduct.T_06_deepStaticCurrent_A)
    
#    ET(board_rf_conduct.T_07_formalVersionDownload_A)
#    ET(battery.T_01_batteryOpen_A)
#    ET(battery.T_02_capacityOpen_A)
    ET(overall_unit.T_11_trade_A)
except TestItemFailException,e:
    processException(e)
except Exception,e:
    print e


