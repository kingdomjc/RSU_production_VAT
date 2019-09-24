#encoding:utf-8
'''
Created on 2016-11-12
GS25发卡器
@author: zws
'''


from hhplt.deviceresource import TestResource,TestResourceInitException,askForResource

from GS25.GS25 import GS25
from GS25.GS25 import GS25Exception


class GS25Device(TestResource):
    def __init__(self,param):
        self.issueCom = param["issueCom"]
        self.gs25 = GS25()
    
    def initResource(self):
        try:
            if self.issueCom == "":
                self.gs25.open()
            else:
                self.gs25.open(1,dev=str(self.issueCom))
        except GS25Exception,e:
            raise TestResourceInitException(u"初始化GS25读卡器失败:"+str(e))
            
            
            