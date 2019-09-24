#encoding:utf-8
'''
KC-RD40 家校通读写器测试
'''
import hhplt.testengine.product_manage as product_manage
import master_board,slave_board

product_manage.registerProduct("KC-RD40-M", (master_board,))
product_manage.registerProduct("KC-RD40-S", (slave_board,))
