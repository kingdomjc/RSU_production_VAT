#encoding:utf-8
'''
GS11补丁维修工位
'''
import hhplt.testengine.product_manage as product_manage
import offlineUnbind,mendtrading,board_mending
product_manage.registerProduct(u'GS11补丁维修',(
                                           offlineUnbind,mendtrading,board_mending
                                            ))