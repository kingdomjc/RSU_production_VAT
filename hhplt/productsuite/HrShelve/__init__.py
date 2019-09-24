#encoding:utf-8
"""
模块: 海尔自取货架来料检测测试用例集
共分为3个组件：
1、阅读器，有安的提供，测试功率、清点情况
2、天线，使用矢量网络分析仪，测试若干参数
3、功分器，读取6个口的值

@author:zws
"""
from hhplt.productsuite.HrShelve import localmock
from hhplt.testengine import product_manage
import hfReaderBoard, antenna,powerDivider,autoPowerDivider,powerDivider_suite

product_manage.registerProduct(u"海尔-高频阅读器板",(hfReaderBoard,))
product_manage.registerProduct(u"海尔-托盘天线",(antenna,))
product_manage.registerProduct(u"海尔-功分器",( powerDivider_suite.AutoPowerDivider(powerDivider_suite.autoPowerDivider_4),
                                           powerDivider_suite.AutoPowerDivider(powerDivider_suite.autoPowerDivider_5),
                                            powerDivider_suite.AutoPowerDivider(powerDivider_suite.autoPowerDivider_6)  ))

product_manage.registerProduct(u"海尔-举例子玩",(localmock,))


from HrDataQueryDlg import HrDataQueryDlg
from hhplt.localutil import registerUiToMenu
registerUiToMenu(HrDataQueryDlg)

