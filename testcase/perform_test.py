#encoding:utf-8
'''
Created on 2014-9-10
服务端性能测试
@author: 张文硕
'''
from hhplt.testengine.server import ServerBusiness,serialCode
from hhplt.simplexml import xmldoc
import time
import thread
from hhplt.parameters import SESSION,GLOBAL

class _WndMock:
        def emit(self,*p):
            print p
SESSION["serverIp"] = "192.168.1.179"
GLOBAL["mainWnd"]=_WndMock()

totalProductCount = 0

prototypes = {}


def initPrototypes():
    prototypes[1] = xmldoc("SampleTestReport-1.xml").toxml()
    prototypes[2] = xmldoc("SampleTestReport-2.xml").toxml()
    prototypes[3] = xmldoc("SampleTestReport-3.xml").toxml()
    

def generateMockReport(idCode,sampleIndex):
    global prototypes
    mockReport = xmldoc()
    mockReport.load_string(prototypes[sampleIndex])
    
    now = time.strftime('%Y-%m-%dT%H:%M:%S',time.localtime(time.time()))
    mockReport["testReport"].attr("reportTime",now)
    mockReport["testReport"]["testingProduct"].attr("idCode",idCode)
    if type(mockReport["testReport"]["testSuite"]) == list:
        for ts in mockReport["testReport"]["testSuite"]:
            ts.attr("testTime",now)
    else:
        mockReport["testReport"]["testSuite"].attr("testTime",now)
    return mockReport.toxml()


def performTestThread():
    global totalProductCount
    with ServerBusiness() as sb:
        while True:
            startTime = time.time()
            idCode = serialCode("mac")
            sb.uploadTestReport(generateMockReport(idCode,1))
            time.sleep(3.5)
            sb.uploadTestReport(generateMockReport(idCode,2))
            time.sleep(3.5)
            sb.uploadTestReport(generateMockReport(idCode,3))
            totalProductCount = totalProductCount+1
            time.sleep(3.5)
            endTime = time.time()
            print u'完成一个，平均交互耗时:%f秒'%((endTime-startTime-10.5)/3)


if __name__ == '__main__':
    global totalProductCount
    initPrototypes()
#    for i in range(0,30):
    for i in range(0,5):
        time.sleep(1)
        thread.start_new_thread(performTestThread,())
    while True:
        startNum = totalProductCount
        time.sleep(10)
        endNum = totalProductCount
        print "\t\t正在轰击，已产生产品结果【%d】个/10秒，累计【%d】"%(endNum-startNum,totalProductCount)
    
    
    
    