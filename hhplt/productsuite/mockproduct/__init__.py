#coding:utf-8
'''桩产品生产测试'''

import hhplt.testengine.product_manage as product_manage
import mock_suite,mock_suite_2,mock_test_inst_bind,mock_suite_3,simle_mock_suite_1

#注册产品
product_manage.registerProduct('MOCK PRODUCT',(mock_suite,mock_suite_2,mock_test_inst_bind,mock_suite_3,simle_mock_suite_1))