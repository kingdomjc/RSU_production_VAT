#encoding:utf-8
'''GS25 发卡器生产测试'''

import hhplt.testengine.product_manage as product_manage

import gs25board,gs25overall

product_manage.registerProduct('GS25',(gs25board,gs25overall))
