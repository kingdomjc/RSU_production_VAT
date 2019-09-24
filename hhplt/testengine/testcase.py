#encoding:utf-8
'''
Created on 2014-8-13
@author: 张文硕
'''

from hhplt.testengine.product_manage import productTestSuits,getTestSuiteVersion
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.parameters import SESSION, PARAM
from hhplt.simplexml import xmldoc
import time

from PyQt4.QtCore import SIGNAL
from threading import Thread

testingFlow = None

def uiLog(message):
    '''测试过程中的日志'''
    if testingFlow is not None:
        testingFlow.ui.emit(SIGNAL("LOG(QString)"),message)

def superUiLog(message):
    '''高级日志，只有super权限的用户登录才打印'''
    if SESSION["testorRole"] == 'SUPER_TESTOR' or SESSION["testorRole"] == 'MANAGER':
        uiLog(message)

def startTest(ui):
    SESSION["testingProduct"] = TestingProduct()
    global testingFlow
    testingFlow = TestFlowModel(SESSION["testingProduct"],ui)
    testingFlow.startExecuteTestSuite()

class TestingProduct():
    '''正在测试中的产品对象:对应到产品-测试大项'''
    def __init__(self,productSlot = None):
        self.productSlot = productSlot  #产品槽号，用于并行测试时，引用基础设施时引用
        self.productName = SESSION["product"]
        self.suite = SESSION["testsuite"]
        self.verifyReport = self.__initReport()
        self.finishSmoothly = None  #是否顺利完成，如果没顺利完成，结果就不要了
        self.testResult = None  #测试结果是否正确
        self.failReasonMessage = []
        self.param = {} #测试中使用的参数，相当于一个便签纸
    
    def __initReport(self):
        verifyReport = xmldoc("xml/TestReportPrototype.xml")
        now = time.strftime('%Y-%m-%dT%H:%M:%S',time.localtime(time.time()))
        verifyReport["testReport"].attr("reportTime",now)
        verifyReport["testReport"]["testingProduct"].attr("productName",self.productName)
        verifyReport["testReport"]["testingProduct"].attr("idCode","")
        verifyReport["testReport"]["testSuite"].attr("status","UNTESTED")
        verifyReport["testReport"]["testSuite"].attr("name",self.suite)
        verifyReport["testReport"]["testSuite"].attr("testor",SESSION["testor"])
        verifyReport["testReport"]["testSuite"].attr("workbay",SESSION["workbay"])
        verifyReport["testReport"]["testSuite"].attr("testTime",now)
        verifyReport["testReport"]["testSuite"].attr("version",getTestSuiteVersion(self.productName,self.suite))
        return verifyReport
    
    def toXml(self):
        '''生成XML文档'''
        return self.verifyReport.toxml()
        
    def markItem(self,itemName,itemStatus,output=None,message=None):
        item = xmldoc()
        item.load_string('''
            <testItem name="%s" status="%s">
            </testItem>
            '''%(itemName,itemStatus))
        
        if output is not None:
            for k in output.keys():
                outputItem = xmldoc()
                outputItem.load_string('''
                    <output name="%s">%s</output>
                    '''%(k,output[k]))
                item["testItem"].appendchild(outputItem.root())
        
        if message is not None:
            messagexml = xmldoc()
            messagexml.load_string("<message>%s</message>"%message)
            item["testItem"].appendchild(messagexml.root())
        self.verifyReport["testReport"]["testSuite"].appendchild(item.root())
        
        if itemStatus == 'FAIL':
            self.failReasonMessage.append(message)

    def finishSuite(self,successOrFail):
        self.testResult = successOrFail
        self.finishSmoothly = True
        self.verifyReport["testReport"]["testSuite"].attr("status","PASS" if successOrFail else "FAIL")
    
    def abortSuite(self,message):
        self.finishSmoothly = False
        self.failReasonMessage.append(message)
        
    def setTestingProductIdCode(self,idCode):
        '''设置测试产品标识'''
        self.verifyReport["testReport"]["testingProduct"].attr("idCode",idCode)
    
    def setTestingSuiteBarCode(self,barCode):
        ''''设置测试项中的条码'''
        self.verifyReport["testReport"]["testSuite"].attr("barCode",barCode)

    def getTestingSuiteBarCode(self):
        '''获得测试项中的条码'''
        return self.verifyReport["testReport"]["testSuite"].attr("barCode")

    def addBindingCode(self,codeName,code):
        '''设置绑定编码'''
        bindingCode = xmldoc()
        bindingCode.load_string('''<bindingCode codeName="%s">%s</bindingCode>'''%(codeName,code))
        self.verifyReport["testReport"].appendchild(bindingCode.root())
        
    
    def getTestingProductIdCode(self):
        '''获得测试产品标识'''
        idCode = self.verifyReport["testReport"]["testingProduct"].attr("idCode")
        return idCode if idCode != '' else None
    
    
class TestFlowModel(Thread):
    '''测试流程对象'''
    def __init__(self,testingProduct,ui):
        super(TestFlowModel,self).__init__()
        self.testingProduct = testingProduct
        self.ui = ui
        self.testSuite = productTestSuits[testingProduct.productName][testingProduct.suite] #测试项目方法列表
        self.acculatedFailWeight = 0
        
    def startExecuteTestSuite(self):
        self.start()

    def run(self):
        '''开始执行测试'''
        #准备函数。如果准备失败，不论什么原因，则直接终止测试
        try:
            self.testSuite.setupFun(self.testingProduct)
        except (BaseException,Exception),e:
            self.__abortTest(e.message)
            self.testSuite.finalFun(self.testingProduct)
            return

        #顺次用例函数
        try:
            for testItem in self.testSuite.getItems():
                if testItem["name"] not in SESSION["seletedTestItemNameList"]:
                    #不测的项，记录为不测
                    self.__finishItemUntested(testItem["name"])
                    continue
                try:
                    testFun = testItem["fun"]
                    self.__startTestItem(testItem["name"])
                    output = testFun(self.testingProduct)
                    self.__finishItemSuccessfully(testItem["name"],output)
                except TestItemFailException,e:
                    self.__finishItemWithFail(testItem["name"],testItem["index"],e)
                    if self.__addAndGetFailWeight(e.failWeight) >= self.testSuite.failWeightSum:
                        #总权值超了，测试失败，进行回滚并通知界面
                        PARAM["failNum"] = "0"
                        self.testSuite.rollbackFun(self.testingProduct)
                        self.__finishTestSuiteFlowWithFail()
                        break
                except AbortTestException,e:
                    #各种原因终止了测试，进行回滚
                    PARAM["failNum"] = "0"
                    self.testSuite.rollbackFun(self.testingProduct)
                    self.__abortTest(e.message)
                    break
                except (BaseException,Exception),e:
                    PARAM["failNum"] = "0"
                    self.__abortTest(u"严重异常，测试终止，请检查软硬件设置："+e.message)
                    self.testSuite.rollbackFun(self.testingProduct)
                    import traceback
                    print traceback.format_exc()
                    break
                finally:
                    time.sleep(0.1)
            else:
                if PARAM["failNum"] == "0":
                    self.__finishTestSuiteFlowSuccessfully()
                else:
                    PARAM["failNum"] = "0"
                    self.testSuite.rollbackFun(self.testingProduct)
                    self.__finishTestSuiteFlowWithFail()

        finally:
            self.testSuite.finalFun(self.testingProduct)
    
    def __outputStr(self,output):
        if output is None:
            return u'<无>'
        kl = output.keys()
        kl.sort()
        return ",".join(["%s=%s"%(k,output[k]) for k in kl])
                    
    
    def __addAndGetFailWeight(self,failWeight):
        self.acculatedFailWeight = self.acculatedFailWeight + failWeight
        return self.acculatedFailWeight
    
    def __startTestItem(self,fun):
        self.ui.emit(SIGNAL("START_ITEM(QString)"),fun)
    
    def __finishTestSuiteFlowWithFail(self):
        '''流程失败而结束'''
        self.testingProduct.finishSuite(False)
        self.ui.emit(SIGNAL("LOG(QString)"),u"产品[%s][%s]测试完成，结果不通过！" % 
                     (self.testingProduct.productName,self.testingProduct.suite))
        self.ui.emit(SIGNAL("FINISH_TEST()"))
    
    def __finishTestSuiteFlowSuccessfully(self):
        '''流程成功结束'''
        self.testingProduct.finishSuite(True)
        self.ui.emit(SIGNAL("LOG(QString)"),u"产品[%s][%s]测试完成，测试通过！" %
                     (self.testingProduct.productName,self.testingProduct.suite))
        self.ui.emit(SIGNAL("FINISH_TEST()"))

    def __abortTest(self,message):
        '''流程终止，本次测试结果不要了'''
        self.testingProduct.abortSuite(message)
        self.ui.emit(SIGNAL("LOG(QString)"),u"由于[%s]，本次测试流程终止，本次测试结果抛弃！" % message)
        self.ui.emit(SIGNAL("FINISH_TEST()"))
        
    def __finishItemSuccessfully(self,itemName,output):
        '''单条测试成功'''
        self.testingProduct.markItem(itemName,"PASS",output)
        self.ui.emit(SIGNAL("ITEM_FINISH(QString,bool)"),itemName,True)
        self.ui.emit(SIGNAL("LOG(QString)"),u"[%s]测试成功，输出:%s"%(itemName,self.__outputStr(output)))
        
    def __finishItemWithFail(self,itemName,itemIndex,e):
        '''单条失败'''
        self.testingProduct.markItem(itemName,"FAIL",e.output,e.message+"(编号:%s)"%itemIndex)
        self.ui.emit(SIGNAL("ITEM_FINISH(QString,bool)"),itemName,False)
        self.ui.emit(SIGNAL("LOG(QString)"),u"%s(编号:%s)测试失败：%s，输出:%s"%(itemName,itemIndex,e.message,self.__outputStr(e.output)))

    def __finishItemUntested(self,itemName):
        '''单条没测'''
        self.testingProduct.markItem(itemName,"UNTESTED")
    
