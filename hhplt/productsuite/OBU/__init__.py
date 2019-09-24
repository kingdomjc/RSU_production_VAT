#coding:utf-8
'''桩产品生产测试'''

import hhplt.testengine.product_manage as product_manage


#注册产品
import obuLaserCarving,try_test1,writeMac


product_manage.registerProduct('SP_OBU',(obuLaserCarving,try_test1,writeMac))