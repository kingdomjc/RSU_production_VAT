#encoding:utf-8
'''
Created on 2014-8-13
测试产品管理
@author: 张文硕
'''

from hhplt.testengine.autoTrigger import EmptyTrigger

class ProductTestSuite():
    @staticmethod
    def emptyFun(product):
        '''空方法，用于没有定义set和rollback方法的测试用例集模块'''
        pass
    
    '''产品测试项'''
    def __init__(self,testSuiteModule):
        #测试项名称
        self.suiteName = testSuiteModule.__dict__["suiteName"]
        #版本
        self.version = testSuiteModule.version
        #测试描述
        self.suiteDesc = testSuiteModule.__doc__
        #测试内容（函数）列表
        self.testFunList = [testSuiteModule.__dict__[testFcName] 
                            for testFcName in filter(lambda s:s.startswith("T_") ,dir(testSuiteModule))]
        #失败权值和
        self.failWeightSum = testSuiteModule.failWeightSum
        #准备函数，可以没有
        self.setupFun = testSuiteModule.setup if "setup" in testSuiteModule.__dict__ else ProductTestSuite.emptyFun
        #回滚处理函数，可以没有
        self.rollbackFun = testSuiteModule.rollback if "rollback" in testSuiteModule.__dict__ else ProductTestSuite.emptyFun
        #结束finally函数，可以没有
        self.finalFun = testSuiteModule.finalFun if "finalFun" in testSuiteModule.__dict__ else ProductTestSuite.emptyFun
        #自动开始结束触发，可以没有，入参是类，不是实例；启动时实例化
        self.autoTrigger = testSuiteModule.autoTrigger if "autoTrigger" in testSuiteModule.__dict__ else EmptyTrigger
    
    def __getFunName(self,fdoc):
        inx = fdoc.find("-")
        return fdoc[:inx] if inx>0 else fdoc;
    
    def __getFunDesc(self,fdoc):
        inx = fdoc.find("-")
        return fdoc[inx+1:] if inx>0 else "";
    
    def __getIndex(self,fname):
        return fname[2:4]
    
    def getItems(self):
        return [{"name":self.__getFunName(f.__doc__),
                 "method":{"A":u"自动判定","M":u"手动判定"}[f.__name__[-1]],
                 "fun":f,
                 "desc":self.__getFunDesc(f.__doc__),
                 "index":self.__getIndex(f.__name__)
                 } for f in self.testFunList]

productTestSuits={}


def registerProduct(productName,testSuiteModules):
    '''注册产品及测试项'''
    productTestSuits[productName] = {}
    for testSuiteModule in testSuiteModules:
        suite = ProductTestSuite(testSuiteModule)
        productTestSuits[productName][suite.suiteName] = suite


def getProductNameList():
    '''获得产品名称列表'''
    return productTestSuits.keys()

def getProductTestSuiteNameList(productName):
    '''获得某产品的测试大项列表'''
    ks = productTestSuits[productName].keys()
    ks.sort()
    return ks
    
def getTestItemList(productName,suiteName):
    '''获得测试单项列表'''
    testSuite = productTestSuits[productName][suiteName]
    return testSuite.getItems()
    
def getTestSuiteDesc(productName,suiteName):
    '''获得测试内容描述'''
    testSuite = productTestSuits[productName][suiteName]
    return testSuite.suiteDesc

def getTestSuiteVersion(productName,suiteName):
    '''获得测试项版本'''
    testSuite = productTestSuits[productName][suiteName]
    return testSuite.version

def getAutoTrigger(productName,suiteName):
    '''获得自动触发器'''
    testSuite = productTestSuits[productName][suiteName]
    return testSuite.autoTrigger
    
def getTestSuiteParallelSlotCount(productName,suiteName):
    "获得测试用例集的并行数量"
    testSuite = productTestSuits[productName][suiteName]
    return testSuite.parallelSlot
    
    
    
