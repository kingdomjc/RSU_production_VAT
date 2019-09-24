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
        s = "%s\t%s\t%s\tʧ��\n"%self.item
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
    if u"��ʼ���Բ�Ʒ[GS10 OBU]��[MAC��֤�����½��ײ�����]" in line:
        r.start()
    elif u"[ɨ���ص�����]���Գɹ�" in line:
        barCode = line[-16:]
        r.setBarCode(barCode)
    elif u"���Բ�Ʒ��ʶ" in line:
        mac = line[-8:]
        r.setMac(mac)
    elif u"�󶨺�ͬ���к�" in line:
        serial = line[:16]
        r.setContractSerial(serial)
    elif u"[MAC��֤�����½��ײ�����]���Գɹ�" in line:
        r.succ()
    elif u"���β���������ֹ�����β��Խ������" in line:
        r.fail()
r.finish()






