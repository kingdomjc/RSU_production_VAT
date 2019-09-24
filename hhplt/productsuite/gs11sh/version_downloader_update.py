#encoding:utf-8
u"""
版本下载板固件更新用例，用于更新板子中的版本
实际测试中将直接使用板中的版本下载到OBU

author:zws
"""
from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM
from hhplt.productsuite.gs11sh.ObuVersionDownloadBoard import ObuVersionDownloadBoard
from hhplt.testengine.exceptions import AbortTestException
from hhplt.testengine.parallelTestSynAnnotation import serialSuite
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.versionContainer import getVersionFile
from hhplt.testengine.server import serverParam as SP

import time


suiteName = u"版本下载板固件更新"
version = "1.0"
failWeightSum = 10

def __getVersionDownloadBoard():
    # 获取版本下载板卡
    return askForResource("VersionDownloadIOController",
                          ObuVersionDownloadBoard,downloadBoardSerialPort = PARAM["downloadBoardSerialPort"])


@serialSuite
def setup(product):
    pass

@serialSuite
def finalFun(product):
    __getVersionDownloadBoard().unselectChannelForUpdateVersion()

from version_download import __getNuLink


def T_01_selectModule_A(product):
    u"选择下载通道-选择槽位下载通道"
    try:
        __getVersionDownloadBoard().selectChannelForUpdateVersion(int(product.productSlot))
    except Exception,e:
        raise AbortTestException(message = str(e))

def T_02_downloadVersionToBoard_A(product):
    u"下载版本到板卡-通过Nulink下载版本到板卡"
    versionFileName = SP("gs11.vatVersion.filename",PARAM["defaultVatVersionFile"],str)
    vf = getVersionFile(versionFileName)
    uiLog(u"开始下载槽位[%s],版本文件:%s"%(product.productSlot,vf))
    __getNuLink(1).downloadVersion(vf,verify=False)
    uiLog(u"槽位[%s]版本下载成功，正在复位芯片"%product.productSlot)


def T_03_resetVersionModule_A(product):
    u"复位板卡-复位板卡使得版本生效"
    __getVersionDownloadBoard().reset(int(product.productSlot))
