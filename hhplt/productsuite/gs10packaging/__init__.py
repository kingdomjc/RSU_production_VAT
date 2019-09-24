#encoding:utf-8
'''GS10 OBU包装工位'''

import hhplt.testengine.product_manage as product_manage
import gs10_10_per_small_box

product_manage.registerProduct(u'GS10包装',(gs10_10_per_small_box,))

#当前只有每小盒10个的包装