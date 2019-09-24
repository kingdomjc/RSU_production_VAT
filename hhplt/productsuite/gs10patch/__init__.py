#encoding:utf-8
'''
GS10补丁工位
对GS10正式测试完成的产品打补丁，统一使用此工位进行
'''

import hhplt.testengine.product_manage as product_manage
import updateVersion,parallelUpdateVersion,rewriteNewMac,updateForJiangxiTest,offlineUnbind,updateVersionAndInfo
product_manage.registerProduct(u'GS10补丁',(
                                           updateVersion,
                                           parallelUpdateVersion,
                                           updateForJiangxiTest,
                                           offlineUnbind,
                                           updateVersionAndInfo
                                            ))