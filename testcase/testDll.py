#encoding:utf-8
'''
Created on 2014-10-20
DLL包装葫芦
@author: user
'''
from ctypes import *

PCI_7230 = 6

#加载API库
api = windll.LoadLibrary('PCI-Dask.dll');
cardNumber = 0
card = api.Register_Card(PCI_7230,cardNumber)
print "card=",card

inputBuffer = c_char_p()

api.DI_ReadPort(card,0,inputBuffer);
print inputBuffer
