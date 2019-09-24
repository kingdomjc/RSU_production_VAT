#encoding:utf-8
"""
模块:

@author:zws
"""
from hhplt.testengine import product_manage

import versionDownload,IntegratedCpcTradeTest,LaserCarving,InitEsamBeforeCarving,CardMacUpdate,justCloseCard,CpcRouteInspectExitTest,CpcEntryTest,RD52ToCpcTradeTest

product_manage.registerProduct(u"CPC卡片",(versionDownload,IntegratedCpcTradeTest,LaserCarving,InitEsamBeforeCarving,CardMacUpdate,justCloseCard,CpcRouteInspectExitTest,CpcEntryTest,RD52ToCpcTradeTest))