#encoding:utf-8
'''
Created on 2016-7-5
并行产品测试引擎
@author: 张文硕
'''
from PyQt4.QtCore import SIGNAL
from threading import Thread
from testcase import TestingProduct
from hhplt.testengine.product_manage import productTestSuits,getTestSuiteVersion
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.parameters import SESSION,PARAM
import time
import testcase

def startParallelTest(ui):
    #使用并行测试时,PARAM中必须具备productSlots参数，是逗号隔开的产品槽编号列表
    slots = PARAM["productSlots"].split(",")
    SESSION["testingProduct"] = {}
    for s in slots:
        SESSION["testingProduct"][s] = TestingProduct(productSlot = s)
        testcase.testingFlow = ParallelTestFlowModel(SESSION["testingProduct"][s],ui)
        testcase.testingFlow.startExecuteTestSuite()
        #只给testingFlow一个引用即可，目前这东西只用于日志。虽然有些不合适。

class ParallelTestFlowModel(Thread):
    '''测试流程对象'''
    def __init__(self,testingProduct,ui):
        super(ParallelTestFlowModel,self).__init__()
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
        except Exception,e:
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
                        self.testSuite.rollbackFun(self.testingProduct)
                        self.__finishTestSuiteFlowWithFail()
                        break
                except AbortTestException,e:
                    #各种原因终止了测试，进行回滚
                    self.testSuite.rollbackFun(self.testingProduct)
                    self.__abortTest(e.message)
                    import traceback
                    print traceback.format_exc()
                    break
                except Exception,e:
                    self.__abortTest(u"严重异常，测试终止，请检查软硬件设置："+e.message)
                    self.testSuite.rollbackFun(self.testingProduct)
                    import traceback
                    print traceback.format_exc()
                    break
                finally:
                    time.sleep(0.1)
            else:
                self.__finishTestSuiteFlowSuccessfully()
        finally:
            self.testSuite.finalFun(self.testingProduct)
    
    def __outputStr(self,output):
        if output is None:
            return u'<无>'
        return ",".join(["%s=%s"%(k,output[k]) for k in output.keys()])
                    
    def __addAndGetFailWeight(self,failWeight):
        self.acculatedFailWeight = self.acculatedFailWeight + failWeight
        return self.acculatedFailWeight
    
    def __startTestItem(self,fun):
        self.ui.emit(SIGNAL("START_ITEM(QString,QString)"),self.testingProduct.productSlot,fun)
    
    def __finishTestSuiteFlowWithFail(self):
        '''流程失败而结束'''
        self.testingProduct.finishSuite(False)
        self.ui.emit(SIGNAL("LOG(QString)"),u"产品[%s][%s]，槽号[%s]测试完成，结果不通过！" % 
                     (self.testingProduct.productName,self.testingProduct.suite,self.testingProduct.productSlot))
        self.ui.emit(SIGNAL("FINISH_TEST(QString)"),self.testingProduct.productSlot)
    
    def __finishTestSuiteFlowSuccessfully(self):
        '''流程成功结束'''
        self.testingProduct.finishSuite(True)
        self.ui.emit(SIGNAL("LOG(QString)"),u"产品[%s][%s]，槽号[%s]测试完成，测试通过！" %
                     (self.testingProduct.productName,self.testingProduct.suite,self.testingProduct.productSlot))
        self.ui.emit(SIGNAL("FINISH_TEST(QString)"),self.testingProduct.productSlot)

    def __abortTest(self,message):
        '''流程终止，本次测试结果不要了'''
        self.testingProduct.abortSuite(message)
        self.ui.emit(SIGNAL("LOG(QString)"),u"由于[%s]，本次槽[%s]测试流程终止，本次测试结果抛弃！" % \
                     (message,self.testingProduct.productSlot))
        self.ui.emit(SIGNAL("FINISH_TEST(QString)"),self.testingProduct.productSlot)
        
    def __finishItemSuccessfully(self,itemName,output):
        '''单条测试成功'''
        self.testingProduct.markItem(itemName,"PASS",output)
        self.ui.emit(SIGNAL("ITEM_FINISH(QString,QString,bool)"),self.testingProduct.productSlot,itemName,True)
        self.ui.emit(SIGNAL("LOG(QString)"),u"槽[%s],[%s]测试成功，输出:%s"%\
                     (self.testingProduct.productSlot,itemName,self.__outputStr(output)))
        
    def __finishItemWithFail(self,itemName,itemIndex,e):
        '''单条失败'''
        self.testingProduct.markItem(itemName,"FAIL",e.output,e.message+"(编号:%s)"%itemIndex)
        self.ui.emit(SIGNAL("ITEM_FINISH(QString,QString,bool)"),self.testingProduct.productSlot,itemName,False)
        self.ui.emit(SIGNAL("LOG(QString)"),u"槽[%s]，%s(编号:%s)测试失败：%s，输出:%s"%\
                     (self.testingProduct.productSlot,itemName,itemIndex,e.message,self.__outputStr(e.output)))

    def __finishItemUntested(self,itemName):
        '''单条没测'''
        self.testingProduct.markItem(itemName,"UNTESTED")
