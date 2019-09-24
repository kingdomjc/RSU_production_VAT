#encoding:utf-8
u""" CPC交易测试
在 RD52 天线上完成标识路径测试
"""
import threading
from hhplt.parameters import PARAM
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.testutil import multipleTest, multipleTestCase
from hhplt.deviceresource import askForResource, retrieveAllResource
from hhplt.deviceresource.virtualProvinceBorderStation.rsuController import RsuController
from hhplt.deviceresource.virtualProvinceBorderStation.dataTypes import VirtualStationConfig
from hhplt.deviceresource.virtualProvinceBorderStation.virtualProvinceBorderStation import VirtualProvinceBorderStation
suiteName = u"RD52天线CPC路径标识测试"
version = "1.0"
failWeightSum = 10
station = None
def setup(product):
    global station
    controller = __getRsuController()
    config = __getVirtualStationConfig()
    station = __getVirtualProvinceBorderStation(controller, config)

def finalFun(product):
    pass

def rollback(product):
    pass

def __getRsuController():
    return askForResource("RsuController", RsuController, ipaddr=PARAM["rd52_ctrl_ipaddr"],post=PARAM["rd52_ctrl_post"])
def __getVirtualStationConfig():
    return askForResource("VirtualStationConfig", VirtualStationConfig, manufacturerId="a4",localRoute="0600",\
            nextRoute="0a00",linkMode="broadcast",aid=1,cpcChannelId=0)
def __getVirtualProvinceBorderStation(controller, config):
    return askForResource("VirtualProvinceBorderStation", VirtualProvinceBorderStation, rsuController=controller,config=config)
def stop():
    uiLog(u"停止RD52控制器，模拟链路路径标识")
    station.stop()

# @multipleTestCase(times=5)
def T_01_routeSign_A(product):
    u"路径标识-模拟链路路径标识信息"
    timer = threading.Timer(20, stop)
    timer.start()
    station.run()


# def T_06_inspectRoute_A(product):
#     u"检查路径标识-检查路径标识是否成功"
#     ENTRY.__getRsu().cpcHfActive()
#     ret = EXIT.T_02_inspectRoute_A(product)
#     if product.param["testRouteInfo"] not in ret[u"路径信息"]:
#         raise TestItemFailException(failWeight = 10,message = u'路径标识检查错误')