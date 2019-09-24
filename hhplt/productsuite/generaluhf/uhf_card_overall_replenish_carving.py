#encoding:utf-8
u'''GS15 UHF卡整机通用测试，测试装配后的卡片功能及性能是否正常
将被测标签放在射频覆盖范围内，测试通过后进行补充镭雕。'''

suiteName = u'''补充镭雕的超高频卡成品测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import uhf_card_overall_with_serial_carving
from hhplt.testengine.manul import askForSomething


autoTrigger = uhf_card_overall_with_serial_carving.autoTrigger
setup = uhf_card_overall_with_serial_carving.setup
finalFun = uhf_card_overall_with_serial_carving.finalFun
rollback = uhf_card_overall_with_serial_carving.rollback

T_01_inventoryTagAndTid_A = uhf_card_overall_with_serial_carving.T_01_inventoryTagAndTid_A
T_02_testWriteEpc_A = uhf_card_overall_with_serial_carving.T_02_testWriteEpc_A
T_03_testWriteUser_A = uhf_card_overall_with_serial_carving.T_03_testWriteUser_A

global carvingCode
carvingCode = ""

def T_04_laserCarve_M(product):
    u'''补充镭雕卡面编号-输入卡面编号并进行镭雕'''
    global carvingCode
    carvingCode = askForSomething(u"镭雕卡面号", u"输入需要镭雕的内容",defaultValue = carvingCode ,autoCommit=False)
    return uhf_card_overall_with_serial_carving.__carveTest(carvingCode, product)



