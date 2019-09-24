#encoding:utf-8
"""
模块:

@author:zws
"""

from hhplt.parameters import GLOBAL, PARAM
import autoPowerDivider
from hhplt.testengine.testcase import uiLog


class AutoPowerDividerSetupFun:
    def __init__(self,spParamFile):
        self.spParamFile = spParamFile

    def __call__(self,product):
        self.__changeSpParam(self.spParamFile)

    def __changeSpParam(self,paramFile):
        PARAM["SP_PARAM"] = "config/hr/%s"%paramFile
        GLOBAL["mainWnd"].initDefaultLocalSpParams()
        uiLog(u"加载功分器良品判决参数文件:%s"%paramFile)


class AutoPowerDivider:
    def __init__(self,testSuiteObj):
        self.__dict__.update(testSuiteObj)


autoPowerDivider_4 = {
    "__doc__":u"4口功分器自动测试",
    "suiteName" : u"4口功分器测试",
    "version" : "1.0",
    "failWeightSum":10,

    "setup": AutoPowerDividerSetupFun("spParam-4.json"),
    "finalFun":autoPowerDivider.finalFun,
    "T_01_scanBare_M":autoPowerDivider.T_01_scanBare_M,
    "T_02_port4Test_A":autoPowerDivider.T_02_port4Test_A,
    "T_04_port2Test_A":autoPowerDivider.T_04_port2Test_A,
    "T_05_port1Test_A":autoPowerDivider.T_05_port1Test_A,
    "T_06_port6Test_A":autoPowerDivider.T_06_port6Test_A
}



autoPowerDivider_5 = {
    "__doc__":u"5口功分器自动测试",
    "suiteName" : u"5口功分器测试",
    "version" : "1.0",
    "failWeightSum":10,

    "setup": AutoPowerDividerSetupFun("spParam-5.json"),
    "finalFun":autoPowerDivider.finalFun,
    "T_01_scanBare_M":autoPowerDivider.T_01_scanBare_M,
    "T_02_port4Test_A":autoPowerDivider.T_02_port4Test_A,
    "T_03_port3Test_A":autoPowerDivider.T_03_port3Test_A,
    "T_04_port2Test_A":autoPowerDivider.T_04_port2Test_A,
    "T_05_port1Test_A":autoPowerDivider.T_05_port1Test_A,
    "T_06_port6Test_A":autoPowerDivider.T_06_port6Test_A,
}

autoPowerDivider_6 = {
    "__doc__":u"6口功分器自动测试",
    "suiteName" : u"6口功分器测试",
    "version" : "1.0",
    "failWeightSum":10,

    "setup": AutoPowerDividerSetupFun("spParam-6.json"),
    "finalFun":autoPowerDivider.finalFun,
    "T_01_scanBare_M":autoPowerDivider.T_01_scanBare_M,
    "T_02_port4Test_A":autoPowerDivider.T_02_port4Test_A,
    "T_03_port3Test_A":autoPowerDivider.T_03_port3Test_A,
    "T_04_port2Test_A":autoPowerDivider.T_04_port2Test_A,
    "T_05_port1Test_A":autoPowerDivider.T_05_port1Test_A,
    "T_06_port6Test_A":autoPowerDivider.T_06_port6Test_A,
    "T_07_port5Test_A":autoPowerDivider.T_07_port5Test_A,
}
