#encoding:utf-8
"""
模块:

@author:zws
"""
from threading import RLock
import time
import sqlite3

from hhplt.parameters import PARAM


COMPLEMENT_TABLE_SCRIPT = '''
create table if not exists ComplementData(
    cpcId varchar(32) primary key,
    mac varchar(32) ,
    sn varchar(32) ,
    addTime int
)

'''

class CpcMissingDbHelper:
    def __init__(self,targetScope):
        self.cx = None
        self.dbFile = "localdata/cpcLaserCarving.db"
        self.dbLock = RLock()
        self.targetScope = targetScope   #目标范围

        self.cpcIdRadix = PARAM["cpcIdRadix"]
        # 头是一样的，所以只截取后半部分
        self.perfix = targetScope[0][:8]
        self.targetCpcIdRange = xrange(int(targetScope[0][8:],self.cpcIdRadix),int(targetScope[1][8:],self.cpcIdRadix)+1)
        self.missingCpcIter = self.fetchAMissingCpcIdIter()

        self.currentCpcId = None

    def connToDb(self):
        # 连接数据库
        self.cx = sqlite3.connect(self.dbFile,check_same_thread=False)
        for sql in COMPLEMENT_TABLE_SCRIPT.split(";"):
            self.cx.execute(sql)

    def closeDb(self):
        # 关闭数据库连接
        if self.cx is not None:
            self.cx.close()
            self.cx = None

    def fetchAMissingCpcId(self):
        return self.currentCpcId if self.currentCpcId is not None else self.missingCpcIter.next()

    def fetchAMissingCpcIdIter(self):
        for cpcIdInt in self.targetCpcIdRange:
            if self.cpcIdRadix == 10:
                cpcId = "%s%.8d"%(self.perfix,cpcIdInt)
            elif self.cpcIdRadix == 16:
                cpcId = "%s%.8X"%(self.perfix,cpcIdInt)
            if self.__checkMissing(cpcId):
                yield cpcId

    def __checkMissing(self,cpcId):
        a = self.cx.execute("select count(*) from CarveData where cpcId = '%s'"%cpcId).fetchone()[0]
        b = self.cx.execute("select count(*) from ComplementData where cpcId = '%s'"%cpcId).fetchone()[0]
        return a == b == 0

    def rollbackCpcId(self,cpcId):
        self.currentCpcId = cpcId

    def saveComplementRecord(self,cpcId,mac):
        self.cx.execute("delete from ComplementData where cpcId='%s'"%cpcId)
        self.cx.execute("insert into ComplementData (cpcId,mac,addTime) values('%s','%s',%d)"%(cpcId,mac,(time.time()*1000)))
        self.cx.commit()
        self.currentCpcId = None

