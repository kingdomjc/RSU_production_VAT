#encoding:utf-8
"""
模块:

@author:zws
"""
from hhplt.parameters import PARAM


def transCpcIdToMac(cpcId):
    # 将CPCID转换成MAC
    #FE080001对应5201ACFF000000C9
    refCpcId = int(PARAM["refCpcId"],16)
    refMac = int(PARAM["refMac"],16)
    return "%.8X"%(int(cpcId,16) - refCpcId + refMac)

