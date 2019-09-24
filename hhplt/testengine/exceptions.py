#encoding:utf-8
'''
Created on 2014-8-13
异常定义
@author: 张文硕
'''


class TestItemFailException(Exception):
    '''单个测试项不通过，抛出此异常'''
    def __init__(self,failWeight,message=None,output=None):
        self.failWeight = failWeight
        self.message = message
        self.output = output

class AbortTestException(Exception):
    '''需要终止测试，抛出此异常'''
    def __init__(self,message=None):
        self.message = message
