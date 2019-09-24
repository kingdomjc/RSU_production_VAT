#encoding:utf-8
u'''GS15 唐山曹妃甸补充镭雕，测试装配后的卡片功能及性能是否正常
将被测标签放在射频覆盖范围内，测试通过后进行补充镭雕。'''

suiteName = u'''曹妃甸卡补充镭雕成品测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import caofeidian_card_overall

from hhplt.productsuite.generaluhf.uhf_card_overall_replenish_carving import T_04_laserCarve_M as laserCarve

autoTrigger = caofeidian_card_overall.autoTrigger
setup = caofeidian_card_overall.setup
finalFun = caofeidian_card_overall.finalFun
rollback = caofeidian_card_overall.rollback

T_01_inventoryTagAndTid_A = caofeidian_card_overall.T_01_inventoryTagAndTid_A
T_02_testWriteEpc_A = caofeidian_card_overall.T_02_testWriteEpc_A
T_03_testWriteUser_A = caofeidian_card_overall.T_03_testWriteUser_A

global carvingCode
carvingCode = ""

def T_04_laserCarve_M(product):
    u'''补充镭雕卡面编号-输入卡面编号并进行镭雕'''
    return laserCarve(product)


