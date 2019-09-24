#encoding:utf-8
'''江苏安智博通用UHF标签工装测试'''


import hhplt.testengine.product_manage as product_manage
import uhf_tag_board,uhf_tag_fixepc_without_carve,uhf_tag_variableepc_without_carve,    \
    uhf_tag_fixepc_with_carve,uhf_tag_variableepc_with_carve,uhf_tag_from_file,\
    uhf_tag_fixepc_with_carve_tid


product_manage.registerProduct(u"安智博通用UHF标签", (
                                               uhf_tag_board,
                                               uhf_tag_fixepc_without_carve,
                                               uhf_tag_variableepc_without_carve,
                                               uhf_tag_fixepc_with_carve,
                                               uhf_tag_variableepc_with_carve,
                                               uhf_tag_from_file,
                                               uhf_tag_fixepc_with_carve_tid
                                               ))

