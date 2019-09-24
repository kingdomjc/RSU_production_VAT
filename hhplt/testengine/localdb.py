#encoding:utf-8
'''
Created on 2015-5-4
本地数据库支撑工具
@author: zws
'''

#数据库构造脚本
createDbSql = '''
    create table if not exists localData(
        productName varchar(30),
        idCode varchar(100),
        codeName varchar(50),
        code varchar(100),
        bindingTime bigint,
        primary key(productName,idCode,codeName)
    );
    create table if not exists testResult(
        productName varchar(30),
        idCode varchar(100),
        testTime varchar(32),
        testResult varchar(30),
        primary key(productName,idCode)
    )
'''

import sqlite3,os,time
from hhplt.parameters import PARAM 
from threading import Thread
from threading import Event
from threading import RLock

class LocalDb:
    '''本地数据库工具'''
    def __init__(self,dbFile = None):
        self.cx = None
        self.dbFile = "localdata/"+(PARAM["localDbFile"] if dbFile is None else dbFile)
        
    def connToDb(self):
        '''连接数据库'''
        self.cx = sqlite3.connect(self.dbFile)
        for sql in createDbSql.split(";"):
            self.cx.execute(sql)
#        self.cx = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+"/"+SESSION["localDbFile"])
    
    def closeDb(self):
        '''关闭数据库连接'''
        if self.cx is not None:
            self.cx.close()
            self.cx = None
    
    def writeToDb(self,product):
        '''产品测试结果写入数据库'''
        productName = product.productName
        idCode = product.getTestingProductIdCode()
        self.cx.execute("delete from localData where productName = '%s' and idCode = '%s'"%(productName,idCode))
        bindingTime = int(time.time()*1000)
        bcs = product.verifyReport["testReport"]["bindingCode"]
        if type(bcs) != list:bcs = [bcs]

        try:
            self.cx.execute("delete from testResult where productName = '%s' and idCode = '%s'"%(productName,idCode))
            self.cx.execute("insert into testResult (productName,idCode,testTime,testResult) values ('%s','%s','%s','%s')"%\
                            (productName,idCode,
                             time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(bindingTime/1000.0)),
                             "OK" if product.testResult else "NG"))
            for bc in bcs:
                codeName = bc.attr("codeName")
                code = bc.value
                self.cx.execute("insert into localData values('%s','%s','%s','%s',%d);"%(
                           productName,idCode,codeName,code,bindingTime))
            self.cx.commit()
        except Exception,e:
            print e


    def query(self,productName,queryCodeName,queryCondScope,outputCodeList,itemCallback=None):
        '''查询，入参：查询码名，查询码范围，输出内容'''#与服务端的bindingCode表查询完全相同
        sqlHead = u"select localData.code as queryCode,localData.idCode as idCode,testTime,testResult, "
        outputFieldStr = u",".join([u"T_%d.code as code_%d"%(i,i) for i in range(len(outputCodeList))])
        fromStr = u"from localData left join testResult on testResult.idCode = localData.idCode and testResult.productName= localData.productName "
        outputCondStr = u" ".join([u'''
        left join 
        (select code ,idCode from localData where productName = '%s' and codeName = '%s') T_%d
        on localData.idCode = T_%d.idCode
        '''%(productName,outputCodeList[i],i,i) for i in range(len(outputCodeList))])
        
        queryCondStr = u'''
        inner join
        (
        select max(bindingTime) as bindingTime,code from localData
        where codeName= '%s' and productName = '%s'
        group by code
        )B 
        on localData.bindingTime = B.bindingTime and localData.code = B.code
        where localData.productName = '%s' and localData.codeName = '%s' 
            and localData.code between '%s' and '%s'
        order by localData.code;
        '''%(queryCodeName,productName,productName,queryCodeName,queryCondScope[0],queryCondScope[1])

        sql = u" ".join([sqlHead,outputFieldStr,fromStr,outputCondStr,queryCondStr])
        # print sql
        cu = self.cx.execute(sql)
        if itemCallback is not None:
            while True:
                a = cu.fetchone()
                if a == None:
                    break;
                itemCallback(a)
        else:
            rs = []
            while True:
                a = cu.fetchone()
                if a == None:
                    break;
                rs.append(a)
            return rs


    def queryByTime(self,productName,startTime,endTime,outputCodeList,itemCallback = None):
        sqlHead = u"select distinct localData.idCode as idCode,testTime,testResult, "
        outputFieldStr = u",".join([u"T_%d.code as code_%d"%(i,i) for i in range(len(outputCodeList))])
        fromStr = u"from localData left join testResult on testResult.idCode = localData.idCode and testResult.productName= localData.productName "
        outputCondStr = u" ".join([u'''
        left join
        (select code ,idCode from localData where productName = '%s' and codeName = '%s') T_%d
        on localData.idCode = T_%d.idCode
        '''%(productName,outputCodeList[i],i,i) for i in range(len(outputCodeList))])

        queryCondStr = u'''
        inner join
        (
        select max(bindingTime) as bindingTime,code from localData
        where productName = '%s'
        group by code
        )B
        on localData.bindingTime = B.bindingTime and localData.code = B.code
        where localData.productName = '%s'and testResult.testTime between '%s' and '%s'
        order by localData.code;
        '''%(productName,productName,startTime,endTime)

        sql = u" ".join([sqlHead,outputFieldStr,fromStr,outputCondStr,queryCondStr])
        # print sql
        cu = self.cx.execute(sql)
        if itemCallback is not None:
            while True:
                a = cu.fetchone()
                if a == None:
                    break;
                itemCallback(a)
        else:
            rs = []
            while True:
                a = cu.fetchone()
                if a == None:
                    break;
                rs.append(a)
            return rs



class WriteToLocalDbThread(Thread):
    def __init__(self,dbFile = None):
        Thread.__init__(self)
        self.localDb = LocalDb(dbFile)
        self.running = False
        self.productBuffer = []
        self.rlock = RLock()    #重入锁
        self.event = Event()    #事件通知机制
    
    def run(self):
        self.localDb.connToDb()
        while self.running:
            try:
                self.rlock.acquire()
                toSaveProduct = [i for i in self.productBuffer]
                self.productBuffer = []
                self.rlock.release()
                if len(toSaveProduct) == 0:
                    self.event.wait()
                    self.event.clear()
                    continue
                else:
                    self.__saveProductsToDb(toSaveProduct)
            except Exception,e:
                print e
        
    def __saveProductsToDb(self,productList):
        for product in productList:
            self.localDb.writeToDb(product)
    
    def writeToDb(self,product):
        if not self.running:    #虽然相关对象默认创建，但只有真正使用时，才开启线程并连接数据库
            self.running = True
            self.start()
        self.rlock.acquire()
        self.productBuffer.append(product)
        self.event.set()
        self.rlock.release()

# localDbThread = WriteToLocalDbThread()

LOCAL_DB_MAP = {}   #本地数据库文件Map，有可能使用多个数据库文件的情况。key是数据库文件名，value是WriteToLocalDbThread对象

def writeProductToLocalDb(product,dbFile = None):
    '''产品数据写入本地数据库'''
    if dbFile not in LOCAL_DB_MAP:
        LOCAL_DB_MAP[dbFile] = WriteToLocalDbThread(dbFile)
    localDbThread = LOCAL_DB_MAP[dbFile]
    localDbThread.writeToDb(product)
        
def queryFromLocalDb(productName,queryCodeName,queryCondScope,outputCodeList,itemCallback=None,dbFile=None):
    '''查询数据库，每次查询后会关闭数据库连接'''
    ldb = LocalDb(dbFile)
    try:
        ldb.connToDb()
        rs = ldb.query(productName, queryCodeName, queryCondScope, outputCodeList, itemCallback)
    finally:
        ldb.closeDb()
    return rs

def queryFromLocalDbByTime(productName,startTime,endTime,outputCodeList,itemCallback = None,dbFile=None):
    # 查询数据库，通过时间查询
    ldb = LocalDb(dbFile)
    try:
        ldb.connToDb()
        rs = ldb.queryByTime(productName, startTime,endTime, outputCodeList, itemCallback)
    finally:
        ldb.closeDb()
    return rs