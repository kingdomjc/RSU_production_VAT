#encoding:utf-8
"""
模块: CPC卡片测试用例集

@author:zws
"""
from hhplt.testengine import product_manage

import cpcVersionDownload,CpcRouteInspectExitTest,CpcEntryTest,LaserCarving,IntegratedCpcTradeTest,justCloseCard
import CpcMacCorrectThroughAirIntf,CpcMissingComplement
import cpcInit

product_manage.registerProduct(u"CPC卡片",(cpcVersionDownload ,CpcRouteInspectExitTest,CpcEntryTest,LaserCarving,IntegratedCpcTradeTest,
                                         justCloseCard,CpcMacCorrectThroughAirIntf,CpcMissingComplement,
										 cpcInit))






