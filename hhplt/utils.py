#encoding:utf-8
'''
Created on 2014-8-14
工具
@author: 张文硕
'''
import json
import os
import base64
import hashlib

class ParamHolder:
    def __init__(self,dumpFile = None):
        self.dumpFile = dumpFile
        self.param = {}
        if dumpFile is not None:
            self.__loadParameterFromLocalFile()
        
    def __loadParameterFromLocalFile(self):
        '''从本地配置文件中获取配置'''
        if not os.path.exists(self.dumpFile):
            return
        try:
            f = file(self.dumpFile)
            self.param = json.load(f)
        except IOError,e:
            print e
        finally:
            f.close()
    
    def dumpParameterToLocalFile(self):
        '''配置保存到本地文件'''
        with open(self.dumpFile, 'w') as f:
            f.write(json.dumps(self.param,indent=1))
            
    def clearAll(self):
        self.param.clear()
    
    def __getitem__(self,key):
        if key not in self.param:
            raise Exception("需要的属性[%s]不在这里面"%key)
        return self.param[key]
    
    def __setitem__(self,key,value):
        self.param[key] = value

    def __contains__(self,key):
        return key in self.param
    
    def __delitem__(self,key):
        if key in self.param:
            del self.param[key]
    
    def __len__(self):
        return len(self.param)

    def isEmpty(self):
        return len(self.param) == 0

def isEmptyString(strObj):
    '''字符串是否为空'''
    return str(strObj).strip() == ''

def encryPassword(plainPassword):
    '''密码加密（MD5-16位）'''
    m = hashlib.md5()
    m.update(plainPassword)
    return m.hexdigest()[8:24]
    
def toHex(ba):
    return "".join(["%.2X"%(ord(x) if isinstance(x,str) else x) for x in ba])

