#coding:utf-8
'''桩产品生产测试'''

import hhplt.testengine.product_manage as product_manage
from hhplt.productsuite.RD52 import RSDB5ManualTest, RSDB5AutoTest, RSRB4SendRecvTest, RS52AllTest, bindBarcode, \
    downloadEPLD, RD52Aging, RFTest

product_manage.registerProduct('RD52_RSU',(RSDB5ManualTest,downloadEPLD,RSDB5AutoTest,RSRB4SendRecvTest,bindBarcode,RS52AllTest,RD52Aging))