#encoding:utf-8
'''
GS11 OBU生产测试
'''

import hhplt.testengine.product_manage as product_manage
import board,overall,trading

product_manage.registerProduct("GS11 OBU", (board,overall,trading,))
