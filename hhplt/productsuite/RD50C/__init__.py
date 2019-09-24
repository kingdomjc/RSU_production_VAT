#coding:utf-8
'''桩产品生产测试'''

import hhplt.testengine.product_manage as product_manage
import manual_test,auto_test1,lightBoard_test,downloadEPLD,RD50CAging

#注册产品
from hhplt.productsuite.RD50C import try_test1, try_test2, try_test3, try_test4
product_manage.registerProduct('RD50C_RSU',(manual_test, downloadEPLD,auto_test1,lightBoard_test,RD50CAging))