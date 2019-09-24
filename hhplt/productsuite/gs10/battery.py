#encoding:utf-8
u'''电池工位测试项'''

suiteName = u'''电池工位测试项(元件测试)'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.server import serverParam as SP
from hhplt.deviceresource import askForResource,GS10PlateDevice

from hhplt.productsuite.gs10.board_digital import __askForPlateDeviceCom
from hhplt.parameters import SESSION

def setup(product):
    #电池工位由于不绑定标识，为元件测试，属于维修测试
    SESSION["isMend"] = True

def T_01_batteryOpen_A(product):
    u'''电池开路电压-返回电压数据，后台根据配置判断'''
    try:
        sc = __askForPlateDeviceCom()
        v = sc.testBattPower()
        resultMap = {"电池开路电压ADC":v}
        if v < SP('gs10.batteryOpenPower.low',-1) or v > SP('gs10.batteryOpenPower.high',4.0):
            raise TestItemFailException(failWeight = 10,message = u'电池开路电压异常',output=resultMap)
        return resultMap
    except TestItemFailException,e:
        raise e
    except:
        raise TestItemFailException(failWeight = 10,message = u'电池开路电压测试失败')

def T_02_capacityOpen_A(product):
    u'''电容开路电压-返回电压数据，后台根据配置判断'''
    try:
        sc = __askForPlateDeviceCom()
        v = sc.testCapPower()
        resultMap = {"电容开路电压ADC":v}
        if v < SP('gs10.capOpenPower.low',-1) or v > SP('gs10.capOpenPower.high',4.0):
            raise TestItemFailException(failWeight = 10,message = u'电容开路电压异常',output=resultMap)
        return resultMap
    except TestItemFailException,e:
        raise e
    except:
        raise TestItemFailException(failWeight = 10,message = u'电容开路电压测试失败')



