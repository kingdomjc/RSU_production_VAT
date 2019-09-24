#coding:utf-8
'''通用超高频卡生产测试'''
#为安智博定制开发的通用UHF卡片测试用例集

import hhplt.testengine.product_manage as product_manage
import uhf_card_board,uhf_card_overall,uhf_card_overall_with_serial_carving,uhf_card_overall_replenish_carving

#注册产品测试项
product_manage.registerProduct(u'通用UHF标签测试',(
                                             uhf_card_board,   #通用超高频卡单板测试
                                           uhf_card_overall,    #通用整机测试
                                           uhf_card_overall_with_serial_carving, #带有镭雕的整机测试
                                           uhf_card_overall_replenish_carving, #带有镭雕的整机测试
                                           ))

