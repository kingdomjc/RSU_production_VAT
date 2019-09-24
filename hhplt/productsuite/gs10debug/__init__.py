#encoding:utf-8
'''
GS10调试使用的测试工具
'''

import hhplt.testengine.product_manage as product_manage
import critical_rf_param,power_scan_test

product_manage.registerProduct(u'GS10 调试',(critical_rf_param,
                                          power_scan_test 
                                           ))
