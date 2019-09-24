#encoding:utf-8
"""
模块: 用于检查CPCID重复的数据库助手
在镭雕工位，用此工具检查CPCID的重复

@author:zws
"""
import BaseHTTPServer
import httplib
import json
import sqlite3
import time
from SocketServer import ThreadingMixIn
from threading import RLock, Thread

from hhplt.parameters import PARAM

DB_SCRIPT = '''
 create table if not exists CarveData(
    cpcId varchar(32) primary key,
    sn varchar(32),
    mac varchar(16),
    carveTime int
 )

'''

dbHelper = None

class DuplicateCheckDbHelper:
    def __init__(self):
        self.cx = None
        self.dbFile = "localdata/cpcLaserCarving.db"
        self.dbLock = RLock()

    def connToDb(self):
        # 连接数据库
        self.cx = sqlite3.connect(self.dbFile,check_same_thread=False)
        for sql in DB_SCRIPT.split(";"):
            self.cx.execute(sql)

    def closeDb(self):
        # 关闭数据库连接
        if self.cx is not None:
            self.cx.close()
            self.cx = None

    def getCpcId(self,cpcId):
        # 读取cpcid，如果没有，说明没重复，返回None
        # 如果有，返回镭雕的时间和其他信息
        self.dbLock.acquire()
        try:
            cu = self.cx.execute("select * from CarveData where cpcId = '%s'"%cpcId)
            a = cu.fetchone()
            if a is None:return None
            return {"sn":a[1],"carveTime":a[3]}
        finally:
            self.dbLock.release()

    def recordCpc(self,cpcId,sn,mac):
        # 记录CPC卡
        self.dbLock.acquire()
        try:
            self.cx.execute("delete from CarveData where cpcId='%s'"%cpcId)
            self.cx.execute("insert into CarveData (cpcId,sn,mac,carveTime) values('%s','%s','%s',%d)"%(cpcId,sn,mac,(time.time()*1000)))
            self.cx.commit()
        finally:
            self.dbLock.release()


class DuplicateCheckNetHelper:
    def __init__(self,baseUrl):
        self.baseUrl = baseUrl

    def __post(self,content,requestParam):
        self.conn = httplib.HTTPConnection(self.baseUrl)
        self.conn.timeout = 6
        self.conn.connect()
        reqPayload = json.dumps(requestParam)
        header = {'Content-Type': "text/json", "Connection": "keep-alive", "Content-length": str(len(reqPayload))}
        self.conn.request("POST", content, reqPayload , header)
        response = self.conn.getresponse()
        res = response.read()
        if response.status != 200:
            raise Exception('recv wrong rest response:%s' % res)
        return json.loads(res)

    def getCpcId(self,cpcId):
        return self.__post("getCpcId",{"cpcId":cpcId})

    def recordCpc(self,cpcId,sn,mac):
        self.__post("recordCpc",{"cpcId":cpcId,"sn":sn,"mac":mac})


class DuplicateCheckHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def __processUrl(self, path):
        # 处理URL，截取context和查询字符串参数Map
        context = self.path.split("/")[-1]
        param = {}
        if "?" in context:
            v = context.split("?")
            context = v[0]
            for kv in v[1].split("&"):
                kvs = kv.split("=")
                param[kvs[0]] = kvs[1]
        return context, param

    def do_POST(self):
        datas = self.rfile.read(int(self.headers['content-length']))
        context,param = self.__processUrl(self.path)
        self.__invokeMethod(context,datas)

    def __invokeMethod(self,context,datas):
        self.protocol_version = 'HTTP/1.1'
        try:
            httpPayload = json.dumps(self.__processLocalInvoke(context, json.loads(datas)))
            self.send_response(200)
        except Exception, e:
            self.send_response(500)
            import traceback
            print traceback.format_exc()
            httpPayload = ""
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Connection", "keep-alive")
        self.send_header("Content-length", len(httpPayload))
        self.end_headers()
        self.wfile.write(httpPayload)

    def __processLocalInvoke(self,context,datas):
        if context == "getCpcId":
            res = dbHelper.getCpcId(datas["cpcId"])
            return res if res is not None else {}
        elif context == "recordCpc":
            dbHelper.recordCpc(cpcId = datas["cpcId"],sn = datas["sn"],mac = datas["sn"])
            return {}


duplicateCheckServer = None

class DuplicateCheckServer(Thread):
    class DuplicateCheckHttpServer(ThreadingMixIn,BaseHTTPServer.HTTPServer):
        pass

    def __init__(self,port):
        Thread.__init__(self)
        self.port = port

    def run(self):
        Protocol = "HTTP/1.1"
        port = self.port
        server_address = ('', port)
        DuplicateCheckHandler.protocol_version = Protocol
        httpd = DuplicateCheckServer.DuplicateCheckHttpServer(server_address, DuplicateCheckHandler)

        sa = httpd.socket.getsockname()
        print "Serving HTTP on %s,port %s ..." % (sa[0], sa[1])
        while True:
            try:
                httpd.serve_forever()
            except Exception, e:
                import traceback
                print traceback.format_exc()

    def startServer(self):
        self.start()


def generateDBH():
    if ":" in PARAM["duplicateCheckService"]:
        # 客户端模式
        return DuplicateCheckNetHelper(PARAM["duplicateCheckService"])
    else:
        # 服务端模式
        port = int(PARAM["duplicateCheckService"])
        global dbHelper
        dbHelper = DuplicateCheckDbHelper()
        dbHelper.connToDb()
        DuplicateCheckServer(port).start()
        return dbHelper

