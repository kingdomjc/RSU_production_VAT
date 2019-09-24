#encoding:utf-8
import struct
from hhplt.deviceresource.OBU_tc56 import Tc56Message

msg = Tc56Message()
'''
data = [0x55,0xaa ,0x1 ,0x0 ,0x2 ,0x1 ,0x2 ,0x2,0xfd,0x03,0x04]
body = struct.pack(str(len(data)) + "B", *data)
bytes = msg.appendBytes(body)
print repr(bytes)
print repr(msg.getBytes())
print msg.getCmd()
print msg.getData(0)

msg2=Tc56Message()
msg2.set(0,1,[1,2])
print repr(msg2.getBytes())
'''
data = [0x2,0x3,0x55,0xaa ,0x1 ,0x0 ,0x2 ,0x1 ,0x2 ,0x2,0xfd,0x03,0x04]
body = struct.pack(str(len(data)) + "B", *data)
print body
# bytes = msg.appendBytes(body)
# print repr(bytes)
# print repr(msg.getBytes())

# data = [0xfd,0x03,0x04]
# body = struct.pack(str(len(data)) + "B", *data)
# bytes = msg.appendBytes(body)
# print repr(bytes)
# print repr(msg.getBytes())
# s = 0
# for i in [0x2,0x3,0x55,0xaa ,0x1 ,0x0 ,0x2 ,0x1 ,0x2 ,0x2]:
#     s ^= i
# print s
# print int(str(0xfd),16)

