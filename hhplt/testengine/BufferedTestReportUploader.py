#encoding:utf-8
"""
模块: 带有本地缓存的测试报告上传

@author:zws
"""
import uuid,sqlite3,time
from threading import Thread, RLock,  Event

from hhplt.testengine.server import ServerBusiness
from hhplt.testengine.testcase import uiLog

BUFFER_DB_SCRIPT = '''
create table if not exists server_cache(id integer primary key AUTOINCREMENT,
	requestUUID varchar(128),
	funName varchar(64),
	payload text,
	addTime int
);
'''

class BufferedTestReportUploader(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.__initDb()
        self.bufferEvent = Event()
        self.start()

    def __initDb(self):
        self.cx = sqlite3.connect("testReportUploadCache.db",check_same_thread=False)
        self.dbLock = RLock()
        self.dbLock.acquire()
        try:
            self.cx.execute(BUFFER_DB_SCRIPT)
            self.cx.commit()
        finally:
            self.dbLock.release()

    def __generateUuid(self):
        return str(uuid.uuid1()).replace("-","")

    def submitReportUpload(self,idCode,testReport):
        try:
            self.dbLock.acquire()
            self.cx.execute(u"insert into server_cache (requestUUID,funName,payload,addTime) values('%s','%s','%s',%d)"%(
                self.__generateUuid()+"-"+idCode,"uploadTestingReport.do",testReport,int(time.time()*1000)))
            self.cx.commit()
        finally:
            self.dbLock.release()
            self.bufferEvent.set()


    def __fetchAReportToUpload(self):
        # 拿一个待上传的报告，如果没有报告，返回None
        try:
            self.dbLock.acquire()
            cu = self.cx.execute(u"select requestUUID,funName,payload from server_cache limit 1")
            a = cu.fetchone()
            if a is None:return
            return {"requestUUID":a[0],"funName":a[1],"payload":a[2]}
        finally:
            self.dbLock.release()

    def __uploadTestReport(self,toUploadReport):
        # 执行上报
        with ServerBusiness() as sb:
            sb.actionAndCheckSuccess("%s?%s"%(toUploadReport["funName"],toUploadReport["requestUUID"]),str(toUploadReport["payload"]),encodeToUrl=False)
            uiLog(u'测试报告%s上传成功'%(toUploadReport["requestUUID"].split("-")[1]))

    def __removeUploadedReport(self,toUploadReport):
        # 移除已经上报的报告
        try:
            self.dbLock.acquire()
            self.cx.execute(u"delete from server_cache where requestUUID='%s'"%toUploadReport["requestUUID"])
        finally:
            self.dbLock.release()


    def run(self):
        while True:
            try:
                tb = self.__fetchAReportToUpload()
                if tb is not None:
                    self.__uploadTestReport(tb)
                    self.__removeUploadedReport(tb)
            except Exception,e:
                import traceback
                print traceback.format_exc()
                # uiLog(u'测试报告上传失败:%s'%unicode(e))
            finally:
                self.bufferEvent.wait(10)
                self.bufferEvent.clear()

bufferedTestReportUploader = BufferedTestReportUploader()



