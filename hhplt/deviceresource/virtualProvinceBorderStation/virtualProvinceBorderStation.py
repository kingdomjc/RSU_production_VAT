#encoding:utf-8
from rsuController import RsuController
from hhplt.parameters import PARAM
from hhplt.deviceresource import TestResource
from utils import Utils,DataParser
from hhplt.testengine.testcase import uiLog
from dataTypes import VirtualStationConfig,TransactionError,CommunicationError
import time
import struct
from cpcTrade import CpcTrade
from obuTrade import ObuTrade
import threading
import sys
class Tag(object):
    def __init__(self, mac, tick=0):
        self.mac = mac
        self.tick = tick
class TagCache(object):
    def __init__(self, cacheTime):
        self.tagSet = set()
        self.mutex = threading.Lock()
        self.cacheTime = cacheTime
    def add(self, mac):
        self.mutex.acquire()
        self.tagSet.add(Tag(mac))
        self.mutex.release()
    def isTagInCache(self,mac):
        for t in self.tagSet:
            if(t.mac == mac):
                return True
        return False
    def checkTags(self):
        uiLog(u"check tag cache")
        removeList = []
        for t in self.tagSet:
            t.tick = t.tick+1
            if(t.tick >= self.cacheTime):
                removeList.append(t)
        self.mutex.acquire()
        for t in removeList:
            self.tagSet.remove(t)
        self.mutex.release()
class VirtualProvinceBorderStation(TestResource):
    def __init__(self, param=None):
        config = param["config"]
        self.rsu = param["rsuController"]
        self.spare = 0
        self.bstMandApplication = "418729301a00290004"
        self.config = config
        self.bstMandAppMap = {"link1":"418729301a00290006", "link2":"428731e81a0004000e00040000", \
                            "broadcast1":"418729701a"+config.localRoute+"00290006", "broadcast2":"428731f81a0004002b0004"+config.localRoute+"0000"}
        self.tagCache = TagCache(3)
        self.checkTagCacheTask = threading.Thread(target=self.checkTagCache)
        self.shouldStop = False
        self.shouldStopMutex = threading.Lock()
    def changeBstRoute(self):
        self.bstMandAppMap["broadcast1"] = "418729701a"+self.config.localRoute+"00290006"
        self.bstMandAppMap["broadcast2"] = "428731f81a0004002b0004"+self.config.localRoute+"0000"
    def updateShouldStop(self, val):
        self.shouldStopMutex.acquire()
        self.shouldStop = val
        self.shouldStopMutex.release()
    def checkTagCache(self):
        while(self.shouldStop==False):
            self.tagCache.checkTags()
            time.sleep(1)
    def stop(self):
        self.updateShouldStop(True)
    def getIccPurchaseKeyIdAndObuDescrypKeyId(self):
        apdu = "0500b0871902"
        res = self.rsu.psamChannel(self.config.obuCappPsamSlot, 1, apdu)
        uiLog(u"&&&&&&&&&&&&&&&&&&&&&&&&&&&&",res.data)
    def run(self):
        self.rsu.open()
        #self.getIccPurchaseKeyIdAndObuDescrypKeyId()
        #self.checkTagCacheTask.start()
        self.cpcTrade = CpcTrade(self.rsu, None, self.config)
        while(self.shouldStop==False):
            try:
                beaconId = Utils.getBeaconId(self.config.manufacturerId)
                currentTime = Utils.currentTime()
                try:
                    res = self.rsu.initialization(beaconId, currentTime, 0, 1, self.bstMandAppMap[self.config.linkMode+hex(self.config.aid)[2:]], 0)
                except (TransactionError, CommunicationError), e:
                    if(self.config.singleRun):
                        self.updateShouldStop(True)
                        break
                    else:
                        continue
                #print "receive vst time ", int(round(time.time()*1000))
                #print res.__dict__
                mac = self.rsu.getCurrentMac()
                '''
                print mac
                if(self.tagCache.isTagInCache(mac)):
                    print "ignore mac"
                    self.rsu.eventReport()
                    if(self.config.singleRun):
                        self.updateShouldStop(True)
                        break
                    else:
                        continue
                '''
                if(int(mac[:2], 16) >= 0xa0):
                    self.cpcTrade.vstApp = res.application
                    self.cpcTrade.run()
                else:
                    if(self.config.aid==2):
                        self.rsu.eventReport()
                        if(self.config.singleRun):
                            self.updateShouldStop(True)
                            break
                        else:
                            continue
                    obuTrade = ObuTrade(self.rsu, res.application, res.obuConfiguration, self.config, self.spare)
                    obuTrade.run()
                self.tagCache.add(mac)
                self.config.changeBothRoute()
                self.changeBstRoute()
            except (TransactionError,CommunicationError),e:
                uiLog(e)
                self.config.changeBothRoute()
                self.changeBstRoute()
                self.rsu.eventReport()
            except KeyboardInterrupt:
                uiLog(u"ctrl+c pressed")
                self.updateShouldStop(True)
            except BaseException,e:
                uiLog(e)
                break
            if(self.config.singleRun):
                self.updateShouldStop(True)
                break
        self.rsu.close()

    # def start(self):
    #     controller = RsuController(PARAM["rd52_ipaddr"], PARAM["rd52_post"])
    #     config = VirtualStationConfig("a4","0600","0a00","broadcast",1,0)
    #     #config = VirtualStationConfig("a4","0600","0a00","link",1,1,singleRun=True)
    #     station = VirtualProvinceBorderStation(controller, config)
    #     station.run()
# if __name__  == '__main__':
#     controller = RsuController("192.168.200.200", 3009)
#     config = VirtualStationConfig("a4","0600","0a00","broadcast",1,0)
#     #config = VirtualStationConfig("a4","0600","0a00","link",1,1,singleRun=True)
#     station = VirtualProvinceBorderStation(controller, config)
#     station.run()
