#encoding:utf-8
'''
Created on 2014-8-13
服务端业务
@author: 张文硕
'''

import httplib,urllib,json

from hhplt.parameters import SESSION,GLOBAL
from PyQt4.QtCore import SIGNAL
from hhplt.testengine.exceptions import AbortTestException,TestItemFailException
            
class ServerBusiness:
    class NormalException(Exception):
        '''正常流程中的异常由此封装'''
        def __init__(self,message):
            self.message = message
            
    def __init__(self,ip=None,testflow=False):
        '''可指定IP地址，如果没有，则从Session中取；如果指定为testflow，表示用于测试流程中，对于异常结束的情况，则要终止整个测试了'''
        self.testflow = testflow
        if ip is None:
            ip = SESSION["serverIp"]
        self.baseUri = ip+":8080"
        self.rootContent = "/HHPLTServer"
        pass
    
    def __enter__(self):
        self.conn = httplib.HTTPConnection(self.baseUri)
        return self
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        self.conn.close()
        if exc_value is not None:
            print exc_value
            if exc_type == ServerBusiness.NormalException:
                GLOBAL["mainWnd"].emit(SIGNAL("ALERT_MESSAGE(QString)"),exc_value.message)
            if exc_type == AbortTestException or exc_type == TestItemFailException:
                raise exc_value
            else:#这里可能需要细化一下
                GLOBAL["mainWnd"].emit(SIGNAL("CRITICAL_MESSAGE(QString)"),u"服务异常，请检查软硬件设置")
                
            if self.testflow:
                raise AbortTestException(exc_value.message)
        return True
    
    
    def __post(self,content,header,requestParam):
        self.conn.request("POST", self.rootContent+"/"+content,requestParam,header)
        response = self.conn.getresponse()
        rtnData = response.read()
        return rtnData
    
    
    def __get(self,content,param):
        requestParam = urllib.urlencode(param)
        self.conn.request("GET", self.rootContent+"/"+content+"?"+requestParam)
        response = self.conn.getresponse()
        return response.read()
    
        
    def __decodeResponse(self,rtnValue):
        return json.JSONDecoder().decode(rtnValue)
    
    def __actionAndCheckSuccess(self,do,param,encodeToUrl = True):
        requestParam = urllib.urlencode(param) if encodeToUrl else param
        header = {}
        header['Content-Type'] = "application/x-www-form-urlencoded" if encodeToUrl else "text/xml"
        rtn = self.__decodeResponse(self.__post(do,header,requestParam))
        if rtn["rtnCode"] != 0:
            raise ServerBusiness.NormalException(rtn["message"])
        return rtn["payload"]

    def actionAndCheckSuccess(self,do,param,encodeToUrl = True):
        return self.__actionAndCheckSuccess(do,param,encodeToUrl)

    ###############################以下是服务端的接口暴露####################################
    
    def login(self,**param):
        '''登录，返回用户对象'''
        return self.__actionAndCheckSuccess("login.do",param)
    
    def modifyPassword(self,**param):
        '''修改密码'''
        self.__actionAndCheckSuccess("modifyPassword.do",param)
    
    def getProductTestStatus(self,**param):
        '''获取某产品的状态'''
        return self.__actionAndCheckSuccess("getProductTestStatus.do",param)
        
    def uploadTestReport(self,report):
        '''上传报告'''
        self.__actionAndCheckSuccess("uploadTestingReport.do",report,encodeToUrl=False)

    def getParamFromServer(self,key):
        '''从服务端获取参数'''
        return self.__get("getParam.do", {"key":key})

    def generateSerialCodeFromServer(self,key):
        '''从服务端获得序列化编码'''
        return self.__actionAndCheckSuccess("generateSerialCode.do",{"key":key})

    def retrieveSerialCodeToServer(self,key,code):
        '''回收序列编码给服务'''
        return self.__actionAndCheckSuccess("retrieveSerialCode.do",{"key":key,"code":code})
    
    def markTestingProductFinishSuccessfully(self,**param):
        '''标记产品测试完成'''
        self.__actionAndCheckSuccess("markTestingProductFinishSuccessfully.do",param)

    def getProductIdByBarCode(self,**param):
        '''通过条码获得产品标识码'''
        if 'suiteName' not in param:
            param['suiteName'] = ''
        return self.__actionAndCheckSuccess("getProductIdCodeByTestSuiteBarCode.do",param)['rtn']
    
    def getProductIdByBindingCode(self,**param):
        return self.__actionAndCheckSuccess("getProductIdCodeByBindingCode.do", param)['rtn']

    def checkAndPersistUniqueBindingCode(self,**param):
        '''检查并持久化唯一绑定码，如果持久成功，返回True，否则返回False'''
        try:
            self.__actionAndCheckSuccess("checkAndPersistUniqueBindingCode.do", param)
            return True
        except ServerBusiness.NormalException,e:
            return False
    
    def unbindCode(self,**param):
        '''解绑定码'''
        self.__actionAndCheckSuccess("unbindCode.do",param)
    
    def getBindingCode(self,**param):
        '''获得绑定码，如果没有绑定码，返回空字符串'''
        return self.__actionAndCheckSuccess("getBindingCode.do", param)['rtn']
        
        
SERVER_PARAM_CACHE = {}
def serverParam(key,defaultValue = None,paramType=float):
    '''从服务端获取参数，本地有个缓存'''
    if key in SERVER_PARAM_CACHE:
        return paramType(SERVER_PARAM_CACHE[key])
    SERVER_PARAM_CACHE[key] = defaultValue
    if SESSION["testor"] != u"单机":
        with ServerBusiness() as sb:
            value = sb.getParamFromServer(key)
            if value !='':
                SERVER_PARAM_CACHE[key] = paramType(value)
    return paramType(SERVER_PARAM_CACHE[key])

def serialCode(key):
    '''获得序列化编码，一定是在测试过程中使用的'''
    with ServerBusiness(testflow=True) as sb:
        value = sb.generateSerialCodeFromServer(key)
        return value['rtn']

def retrieveSerialCode(key,code):
    '''回收编码'''
    with ServerBusiness(testflow=False) as sb:
        sb.retrieveSerialCodeToServer(key,code)
        
        

