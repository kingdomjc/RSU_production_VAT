#encoding:utf-8
'''
GS11 OBU 上海产线-生产测试
'''
import hhplt.testengine.product_manage as product_manage
# import version_download,board_digital,board_radiofreq,overall,trading

# product_manage.registerProduct("GS11 OBU", (version_download,board_digital,board_radiofreq,overall,trading,))


import tj_board_digital,tj_board_downloadversion

# product_manage.registerProduct("TEST_OBU",(tj_board_digital,tj_board_downloadversion))

import version_downloader_update,board_download_and_digital_test,board_download_only

product_manage.registerProduct("TJ_OBU",(version_downloader_update,board_download_and_digital_test,board_download_only))
