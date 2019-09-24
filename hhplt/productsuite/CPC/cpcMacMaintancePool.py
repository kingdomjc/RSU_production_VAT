#encoding:utf-8
"""
模块: 本地MAC地址维护池
负责自动累加MAC地址，并控制在一定范围内

@author:zws
"""
from threading import RLock

from hhplt.parameters import PARAM


class NoRestMacToFetch(Exception):pass


class CpcMacMaintancePool:
    def __init__(self,macRange,currentMac):
        self.startMac = int(macRange[0],16)
        self.endMac = int(macRange[1],16)
        self.currentMac = int(currentMac,16) - 1
        #mac范围、当前mac，都以int维护
        self.poolLock = RLock()

    def fetchAndSwitchToNextMac(self):
        # 拿取一个MAC，并切换至下一个
        self.poolLock.acquire()
        try:
            self.currentMac += 1
            if self.currentMac > self.endMac:raise NoRestMacToFetch()
            return "%.8x"%self.currentMac
        finally:
            self.poolLock.release()

    def currentMac(self):
        return "%.8x"%self.currentMac

    def withdrawCurrentMac(self):
        # 回收MAC
        self.poolLock.acquire()
        try:
            self.currentMac -= 1
        finally:
            self.poolLock.release()

    def dumpToParam(self):
        PARAM["currentMac"] = "%.8x"%self.currentMac
        PARAM.dumpParameterToLocalFile()



