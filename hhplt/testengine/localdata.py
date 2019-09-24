#encoding:utf-8
'''
Created on 2015-1-23
本地测试数据工具
如果需要记录本地数据，使用此工具引擎进行
@author: user
'''

from hhplt.parameters import SESSION 
import time

global filename

def __generateItem(product):
    item = [u"测试时间:%s"%(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))),
            u"结果:%s"%(u'通过' if product.testResult else '不过'),
            u"产品标识码:%s"%product.getTestingProductIdCode()]
    bcl = product.verifyReport["testReport"]["bindingCode"]
    if bcl is None:
        pass
    elif type(bcl) == list: 
        for bc in product.verifyReport["testReport"]["bindingCode"]:
            bsStr = "%s:%s"%(bc.attr("codeName"),bc.value)
            item.append(bsStr)
    else:
        bc = product.verifyReport["testReport"]["bindingCode"]
        bsStr = "%s:%s"%(bc.attr("codeName"),bc.value)
        item.append(bsStr)
    return "\t".join(item)
        

def writeToLocalData(product,fileDir='localdata'):
    item = __generateItem(product)
    if 'localDataFileName' not in SESSION:
        SESSION['localDataFileName'] = u'%s-%s-%s.data'%(time.strftime('%Y-%m-%d',time.localtime(time.time())),
                                                        SESSION["product"],
                                                        SESSION["testsuite"]
                                                        )
    f = open(fileDir+"\\"+SESSION['localDataFileName'],'a')
    f.write("%s\n"%item)





        