#encoding:utf-8
'''
设备及测试资源
'''

'''
Created on 2014-8-13
测试资源

测试用例集根据自身需要，到这里来请求资源，资源由框架统一进行管理，测试用例只负责使用。
在登出的时候，调用retrieveAllResource回收全部资源；
在用例执行时，第一次用到某个资源的时候，初始化该资源，此后就不自动回收，直到登出为止。
在实际用例执行时，可能根据需要手动释放资源

@author: 张文硕
'''
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.parameters import GLOBAL
from PyQt4.QtCore import SIGNAL
from threading import RLock

resources = {}
resourceLock = RLock()

def retrieveAllResource():
    '''回收全部资源'''
    for res in resources.keys():
        resources[res].retrive()
    resources.clear()

def askForResource(resName,resType=None,**param):
    '''要资源,resType是资源的类'''
    try:
        resourceLock.acquire()
        rs = None
        if resName in resources:
            rs = resources.get(resName)
        else:
            if resType is None:
                GLOBAL["mainWnd"].emit(SIGNAL("CRITICAL_MESSAGE(QString)"),u"设备初始化失败")
                return None
            rs = resType(param)
            resources[resName] = rs
            try:
                rs.initResource()
            except TestResourceInitException,e:
                GLOBAL["mainWnd"].emit(SIGNAL("CRITICAL_MESSAGE(QString)"),e.message)
                del resources[resName]
                return None
        return rs
    finally:
        resourceLock.release()

class TestResource:
    '''测试资源从此处派生，此为接口定义'''
    def initResource(self):
        '''初始化资源'''
    
    def retrive(self):
        '''回收资源'''

class TestResourceInitException(Exception):
    '''测试资源初始化失败时，抛出此异常'''
    def __init__(self,message):
        self.message = message



