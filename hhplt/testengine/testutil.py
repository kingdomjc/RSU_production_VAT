#encoding:utf-8
'''
Created on 2014-11-24
测试辅助工具
@author: user
'''

from hhplt.testengine.testcase import uiLog
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
import time


def multipleTestCase(times=2):
    #并行测试的测试用例，在测试用例函数添加此装饰器
    def multipleTestFun(testFun):
        def mtestFun(product):
            return multipleTest(testFun,product,times)
        mtestFun.__doc__ = testFun.__doc__
        mtestFun.__name__ = testFun.__name__
        return mtestFun
    return multipleTestFun

def multipleTest(testFun,product,times = 2):
    '''多次测试，入参是测试函数、产品、次数'''
    #多次测试中，有一次通过则认为整体通过，超过次数均不通过，认为测试失败
    fdoc = testFun.__doc__
    inx = fdoc.find("-")
    testItemName = fdoc[:inx] if inx>0 else fdoc;
    exp = None
    for i in range(1,times+1):
        try:
            return testFun(product)
        except TestItemFailException,e:
            exp = e
            uiLog(u'第%d次测试[%s]待重试'%(i,testItemName))
            time.sleep(1)
    raise exp        
            
def checkBySenser(itemName,timeInSecond,cmdFun,resFun,checkFun):
    '''传感器检测'''
    if checkFun():
        raise AbortTestException(message = u'%s检测传感器异常，请检查'%itemName)
    cmdFun()
    result = False
    time.sleep(1)
    for i in range(timeInSecond*2):
        if checkFun():
            result = True
            break
        time.sleep(0.5)
    resFun()
    time.sleep(0.5)
    if not result:
        raise TestItemFailException(failWeight = 10,message = u'%s检测不通过！'%itemName) 
        

class WrappedPyUnitTestCase:
    "如果原始用例用Unittest封装，通过此类来替换unittest.TestCase从而直接匹配到VAT框架中"
    def __init__(self):
        self.defaultFailMessage = u"参数验证失败"
    
    def assertEqual(self,v1,v2,failMessage = None):
        if failMessage is None:failMessage = self.defaultFailMessage
        if v1 != v2:raise TestItemFailException(failWeight = 10,message = failMessage) 
    
    def assertNotEqual(self,v1,v2,failMessage = ""):
        if v1 == v2:raise TestItemFailException(failWeight = 10,message = failMessage) 
    
    def assertGreaterEqual(self,v1,v2,failMessage = ""):
        if v1 < v2:raise TestItemFailException(failWeight = 10,message = failMessage) 
    
    def assertLessEqual(self,v1,v2,failMessage = ""):
        if v1 > v2:raise TestItemFailException(failWeight = 10,message = failMessage) 
    

def pyutest(testcaseClass,testname,defaultFailMessage = ""):
    #对于unittest.TestCase封装的测试用例，在VAT用例中，直接使用此注释装饰
    #格式：@pyutest(测试用例集类,"用例函数")添加到VAT用例上，VAT用例可空
    def wrappedTestcase(testFun):
        try:
            class wrappedClassfulTestcase(testcaseClass,WrappedPyUnitTestCase):
                def __init__(self):
                    self.defaultFailMessage = defaultFailMessage
                    
                def __call__(self,product):
                    testFun(product)
                    testcaseClass.__dict__[testname](self)
            f = wrappedClassfulTestcase()
            f.__doc__ = testFun.__doc__
            f.__name__ = testFun.__name__
            return f
        finally:
            pass
    return wrappedTestcase


##########################################################################
#import unittest
#class TestTT(unittest.TestCase):
#    def test_xx(self):
#        print 'runtest'
#        self.assertEqual(1, 2, "zzzzzz")
##suite = unittest.TestSuite()
##suite.addTest(TestTT('test_xx'))
##unittest.TextTestRunner().run(suite)
#@pyutest(TestTT,"test_xx")
#def runtest(product):
#    pass
#
#runtest(None)
        
    
    
    
    
        
        