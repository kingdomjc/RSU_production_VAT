#encoding:utf-8
'''GS15 UHF卡包装工位'''



import hhplt.testengine.product_manage as product_manage
import gs15_20_per_small_box

product_manage.registerProduct(u'GS15卡片包装',(gs15_20_per_small_box,))