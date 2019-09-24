#encoding:utf-8
'''
Created on 2015-4-30
实验Sqlite
@author: user
'''

import sqlite3
import os

cx = None   #数据库连接对象

def connToDb():
    global cx
    cx = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+"/lanzhouData.db")

def closeDb():
    cx.close()

def writeToDb(tid,pid,epc):
    global cx
    cx.execute("insert into lanzhouData values('1234','12345','123456');")
    cx.execute("insert into lanzhouData values('aaaa','123sdf45','12srg3456');")
    cx.execute("insert into lanzhouData values('1323234','123gfd45','12xcg3456');")
    cx.commit()

def readFromDb():
    global cx
    cu=cx.cursor()
    cu.execute("select * from lanzhouData;")
    while True:
        a = cu.fetchone()
        if a == None:
            break;
        print `a`
        print a[2]
    
    
    
if __name__ == '__main__':
    connToDb()
#    writeToDb(0,0,0)
    readFromDb()
    closeDb()
    
    
    
    