#encoding:utf-8
'''
高速公路433二义性卡
'''


import hhplt.testengine.product_manage as product_manage
import check_card

product_manage.registerProduct(u"复合通行卡自动检卡", (check_card,))
