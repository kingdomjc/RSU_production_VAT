#encoding:utf-8
'''
Created on 2015-8-17

Alien9900读写器、大华镭雕机桩

@author: user
'''

from Tkinter import *
import tkMessageBox
import socket
import random
from threading import Thread

class Tag():
    '''抽象标签，初始化时随机出标签来'''
    def __init__(self):
        self.reserved = ["00" for i in range(8)]
        self.epc = ["00" for i in range(16)]    #12字节的EPC，前面两个字（PC）不可动
        self.tid = [self.__getRandChar() for x in range(12)]
        self.user = ["00" for i in range(128)]

    def __getRandChar(self):
        return "%X%X"%(random.randint(0,15),random.randint(0,15))
    
    def __getitem__(self,bank):
        return [self.reserved,self.epc,self.tid,self.user][bank]

class Alien9900Mock(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.currentTag = None  #当前放置的标签
    
    def placeTag(self,tag):
        self.currentTag = tag
    
    def __processInventory(self):
        return "Tag:"+"".join(self.currentTag.epc[4:])+",ant1"
    
    def __processRead(self,cmd):
        cs = cmd.split(" ")
        bank = int(cs[2])
        offset = int(cs[3])
        length = int(cs[4])
        return "G2Read = "+"".join(self.currentTag[bank][offset*2:(offset+length)*2])
    
    def __processWrite(self,cmd):
        cs = cmd.split(" ")
        bank = int(cs[2])
        offset = int(cs[3])
        towriteData = ("".join(cs[4:])).strip()
        for i in range(0,len(towriteData),2):
            self.currentTag[bank][offset*2+i/2] = towriteData[i]+towriteData[i+1]
        return "G2Write = Success!"
    
    def run(self):
        HOST = ''                 
        PORT = 23     
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(200)
        while True:
            conn, addr = s.accept()
            #连接成功，推送欢迎界面
            conn.send("Alien>\x00")
            while True:
                try:
                    data = conn.recv(1024)
                    toSend = None
                    if not data: continue
                    elif self.currentTag is None:
                        toSend = "notag\r\b"
                    elif data.startswith("t\r\n"):#清点6C标签
                        toSend = self.__processInventory()
                    elif data.startswith("g2read"): #读
                        toSend = self.__processRead(data)
                    elif data.startswith("g2write"):#写
                        toSend = self.__processWrite(data)
                    toSend += "\r\n"
                    conn.send(toSend)
                    if not data.startswith("t\r\n"):
                        print '-'*10+"\n",'recv:',data,'send:',toSend,'-'*10
                except Exception,e:
                    print str(e)
                    conn.close()
                    break

carveText = None    #镭雕内容显示框

GLOBAL_TAG_POOL = [Tag() for i in range(3)]
ALIEN9900 = Alien9900Mock()
ALIEN9900.start()

def removeTag():
    ALIEN9900.placeTag(None)

def placeTagOne():
    ALIEN9900.placeTag(GLOBAL_TAG_POOL[0])

def placeTagTwo():
    ALIEN9900.placeTag(GLOBAL_TAG_POOL[1])

def placeTagThree():
    ALIEN9900.placeTag(GLOBAL_TAG_POOL[2])


def askForCarve():
    data = None
    try:
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        client.settimeout(2)
        client.connect(("127.0.0.1",3335))
        client.send("TCP:Give me string")
        data = client.recv(30)
        client.close()
    except Exception,e:
        print e
    if data is not None:
        global sysInfoText
        carveText.delete(0,carveText.get().__len__())
        carveText.insert(0,data)
    
def startMainWnd():
    top = Tk()
    top.wm_title(u"Alien9900+读写器/大华镭雕机桩")
    
    Button(top,text=u'拿走标签',command = removeTag).pack()
    Button(top,text=u'放置标签1',command = placeTagOne).pack()
    Button(top,text=u'放置标签2',command = placeTagTwo).pack()
    Button(top,text=u'放置标签3',command = placeTagThree).pack()
    Button(top,text=u'镭雕机踏板',command = askForCarve).pack()
    
    global carveText
    Label(top,text='镭雕内容').pack()
    carveText = Entry(top,width = 50)
    carveText.pack()
    
    mainloop()
    
if __name__ == '__main__':
    startMainWnd()