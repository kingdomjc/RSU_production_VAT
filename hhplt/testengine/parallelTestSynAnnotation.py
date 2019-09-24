#encoding:utf-8
'''
Created on 2016-7-6
并行测试中的同步注释
在并行测试中，如果某个测试方法在各个槽之间需要同步执行，
则在测试方法上面增加@syntest注释即可

如果整个测试用例集都需要串行执行，则在setup和finFun上增加@serialSuite注释

注意：上述两个注释不能（也不应该，没必要）同时使用。
@author: user
'''

from threading import RLock

__paraSynLock = RLock()

def syntest(testFun):
    '''在并行测试中，同步测试方法可使用此注释'''
    def synTestFun(product):
        try:
            __paraSynLock.acquire()
            return testFun(product)
        finally:
            __paraSynLock.release()
    synTestFun.__doc__ = testFun.__doc__
    synTestFun.__name__ = testFun.__name__
    return synTestFun


def serialSuite(setupFinFun):
    '''并行测试中，整体串行的用例集可在setup/finalFun上使用此注释'''
    if setupFinFun.__name__ == "setup":
        def setup(product):
            __paraSynLock.acquire()
            setupFinFun(product)
        return setup
    elif setupFinFun.__name__ == "finalFun":
        def finalFun(product):
            try:
                setupFinFun(product)
            finally:
                __paraSynLock.release()
        return finalFun
    else:
        raise Exception(u"the @serialSuite cannot be added on any functions but setup or finalFun!")
            

        
        
        
        
        
        
    
