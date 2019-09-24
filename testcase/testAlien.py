#encoding:utf-8
'''
Created on 2014-12-11

@author: user
'''
from hhplt.deviceresource import TestResource
from hhplt.deviceresource.Alien9900Reader import *

    
if __name__ == '__main__':
    reader =Alien9900Reader({"readerIp":u"192.168.1.100","readerPort":23,"accessPassword":"00000000"})
    reader.initResource()
    
    rl = reader.inventry6CTag()
    print 'inventory output:'
    for i in rl:
        print i
        toOpEpc = i
#    
    readResult = reader.read(toOpEpc,0,4,0);
    print 'reserved:',readResult
    readResult = reader.read(toOpEpc,1,6,2);
    print 'epc:',readResult
    readResult = reader.read(toOpEpc,2,4,0);
    print 'tid:',readResult
    readResult = reader.read(toOpEpc,3,16,0);
    print 'user:',readResult

    writeResult = reader.write(toOpEpc, 1, 2, "000000000000000000000000")
    print 'write epc result',writeResult
    writeResult = reader.write(toOpEpc, 3, 0, "0"*128)
    print 'write USER result',writeResult
    readResult = reader.read(toOpEpc,3,1,4);
    print 'USER:',readResult
    
    reader.retrive()
    

