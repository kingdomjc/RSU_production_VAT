#encoding:utf-8
u'''GS15 UHF江苏环保卡整机测试，测试装配后的卡片功能及性能是否正常
将被测标签放在射频覆盖范围内，扫描条码后测试自动进行。结束后请移走标签，放置下一张。'''

suiteName = u'''江苏环保卡成品测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.productsuite.generaluhf import uhf_card_overall_with_serial_carving

autoTrigger = uhf_card_overall_with_serial_carving.autoTrigger 
setup = uhf_card_overall_with_serial_carving.setup
finalFun = uhf_card_overall_with_serial_carving.finalFun
rollback = uhf_card_overall_with_serial_carving.rollback

def T_01_inventoryTagAndTid_A(product):
    u'''清点标签并读取TID-测试标签可被清点到，并确保只有一个标签在测'''
    return uhf_card_overall_with_serial_carving.T_01_inventoryTagAndTid_A(product)

def T_02_testWriteEpc_A(product):
    u'''EPC区读写测试-测试EPC写入出厂值'''
    return uhf_card_overall_with_serial_carving.T_02_testWriteEpc_A(product)

def T_03_testWriteUser_A(product):
    u'''USER区读写测试-清零USER区'''
    return uhf_card_overall_with_serial_carving.T_03_testWriteUser_A(product)

def T_04_laserCarve_M(product):
    u'''镭雕卡面编号-自动镭雕卡面顺序编号'''
    return uhf_card_overall_with_serial_carving.T_04_laserCarve_M(product)        