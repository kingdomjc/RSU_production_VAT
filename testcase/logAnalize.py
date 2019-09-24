'''
Created on 2014-12-9

@author: user
'''
f = open("log.txt")

class ItemResult:
    def __init__(self):
        self.item = ["","",""]
        self.towrite = open("output.txt","a")
    
    def start(self):
        self.item = ["","",""]
    
    def succ(self):
        s = "%s\t%s\t%s\n"%self.item
        print s
        self.towrite.write(s)
    
    def fail(self):
        s = "%s\t%s\t%s\t失败\n"%self.item
        print s
        self.towrite.write(s)
    
    def setBarCode(self,barCode):
        self.item[0] = barCode
    
    def setMac(self,mac):
        self.item[1] = mac
    
    def setContractSerial(self,serial):
        self.item[2] = serial

    def finish(self):
        self.towrite.close()

r = ItemResult()

for line in f.readlines():
    if u"开始测试产品[GS10 OBU]的[MAC验证与重新交易测试项]" in line:
        r.start()
    elif u"[扫描镭雕条码]测试成功" in line:
        barCode = line[-16:]
        r.setBarCode(barCode)
    elif u"测试产品标识" in line:
        mac = line[-8:]
        r.setMac(mac)
    elif u"绑定合同序列号" in line:
        serial = line[:16]
        r.setContractSerial(serial)
    elif u"[MAC验证与重新交易测试项]测试成功" in line:
        r.succ()
    elif u"本次测试流程终止，本次测试结果抛弃" in line:
        r.fail()
r.finish()






