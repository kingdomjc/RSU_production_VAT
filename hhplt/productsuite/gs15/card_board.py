#encoding:utf-8
u'''GS15 UHF卡片单板测试，测试卡片的读写功能是否正常。
将一张被测标签放在天线下面，测试将自动开始。结束后请移走标签，放置下一张'''

suiteName = u'''GS15超高频标签单板测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.productsuite.generaluhf import uhf_card_board

#目前江苏卡单板测试完全使用通用单板测试即可
autoTrigger = uhf_card_board.autoTrigger
setup = uhf_card_board.setup
finalFun = uhf_card_board.finalFun
rollback = uhf_card_board.rollback
T_01_inventoryTagAndTid_A = uhf_card_board.T_01_inventoryTagAndTid_A
T_02_testWriteEpc_A = uhf_card_board.T_02_testWriteEpc_A
T_03_testWriteUser_A = uhf_card_board.T_03_testWriteUser_A

