#coding:utf-8
'''GS15 UHF卡生产测试'''
import hhplt.testengine.product_manage as product_manage
import jiangsu_card_overall,card_board,caofeidian_card_overall,jiangsu_card_replenish_carving,caofeidian_card_replenish_carving

#注册产品测试项
product_manage.registerProduct(u'华虹GS15 超高频标签',(
                                             card_board,   #通用超高频卡单板测试
                                           jiangsu_card_overall,    #江苏环保卡整机测试
                                           caofeidian_card_overall, #唐山曹妃甸卡整机测试
                                           jiangsu_card_replenish_carving,  #江苏环保卡补充镭雕
                                           caofeidian_card_replenish_carving,   #曹妃甸补充镭雕
                                           ))

