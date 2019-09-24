#encoding:utf-8
'''GS10 OBU包装工位'''

import hhplt.testengine.product_manage as product_manage
import gs11_11_per_small_box

product_manage.registerProduct(u'GS11包装',(gs11_11_per_small_box,))

#当前只有每小盒10个的包装