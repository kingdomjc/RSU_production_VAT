#encoding:utf-8
u'''请将GS10单板与工装板相连接，检查接口是否松动，指示灯正常亮起。
检查无误后，合上夹具，测试将自动开始。（如果合上夹具后测试未启动，请检查软硬件连接，或手动点击开始测试）
'''
import time

from hhplt.deviceresource.RD52SingleTone import proxy, fpga_pll, tx_pll, proxyFrock
from hhplt.productsuite.RD52 import RSDB5AutoTest
from hhplt.testengine.server import ServerBusiness, serialCode

from hhplt.deviceresource.RD52SingleTone import rx_pll

suiteName = u'''人工手动测试项目1'''
version = "1.0"
failWeightSum = 5  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.parameters import PARAM
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.manul import manulCheck


#串口夹具开合触发器

#测试函数体例：T_<序号>_方法名
#_A为自动完成测试，_M为人工测试；函数正常完成，返回值为输出数据（可空）；异常完成，抛出TestItemFailException异常，含输出（可选）
#函数的doc中，<测试名称>-<描述>
#可选的两个函数:setup(product)和rollback(product)，前者用于在每次测试开始前（不管选择了多少个用例）都执行；后者当测试失败（总权值超出）后执行



def __checkAutoFinished(idCode):
    '''检查RSDB5单板功能测试工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="RD52_RSU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"RSDB5尚未进行单板功能测试，整机测试终止")
        else:
            sn = RSDB5AutoTest.suiteName
            if sn not in status["suiteStatus"] or status["suiteStatus"][sn] != 'PASS':
                raise AbortTestException(message=u"RSDB5单板功能测试项未进行或未通过，整机测试终止")

def _T_01_scanCode_A(product):
    u'扫码RSDB5条码-扫描条码'
    barCode = askForSomething(u'扫描条码', u'请扫描RSDB5条码', autoCommit=False)
    __checkAutoFinished(barCode)
    product.setTestingSuiteBarCode(barCode)
    product.setTestingProductIdCode(barCode)

def T_02_simulationPowerTest_A(product):
    u"单板DAC电路测试-接入RSRB4单板发射模拟控制功率测试（MAX , MIN  2个值）"
    try:
        error = []
        # 待测单板发射单音
        # 模拟高，数字高
        manulCheck(u'提示', u'请接入频谱仪开始测试')
        proxy.open(PARAM["defaultNetOneIp"])
        proxy._init_fpga()
        fpga_pll.config()
        proxy._write_fpga_reg(0x5a, 0x01)
        proxy._write_fpga_reg(0x3e, 0x00)
        tx_pll.config(5830)
        proxy._write_fpga_reg(0x50, 0x02)
        proxy._write_fpga_reg(0x51, 0x01)
        proxy._write_fpga_reg(0x58, 0x01)
        proxy._write_fpga_reg(0x59, 0x01)
        proxy._write_fpga_reg(0x24, 0x47e)
        proxy._write_fpga_reg(0x56, 0x3c)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        MaxMax = manulCheck(u'提示', u'最大功率是否达标')
        if not MaxMax:
            error.append("1.最大功率")

        # 模拟高，数字低
        proxy._write_fpga_reg(0x56, 0x24)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        MaxMin = manulCheck(u'提示', u'衰减数字信号后的功率是否达标')
        if not MaxMin:
            error.append("2.衰减数字信号后的功率")

        # 模拟低，数字高
        proxy._write_fpga_reg(0x24, 0xa28)
        proxy._write_fpga_reg(0x56, 0x3c)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        MinMax = manulCheck(u'提示', u'衰减模拟信号后的功率是否达标')
        if not MinMax:
            error.append("3.衰减模拟信号后的功率")

        # 关闭待测单板单音
        proxy._write_fpga_reg(0x5a, 0x1)
        proxy._write_fpga_reg(0x58, 0x0)
        proxy._write_fpga_reg(0x59, 0x0)
        proxy._write_fpga_reg(0x46, 0x1)
        proxy._write_fpga_reg(0x3e, 0x0)
        proxy._write_fpga_reg(0x5a, 0x0)

    except Exception as e:
        raise AbortTestException(message=e)
    finally:
        proxy.close()
    errorStr = ",".join(error)
    if error != []:
        PARAM["failNum"] = "1"
        raise TestItemFailException(failWeight=1, message=u"%s不达标" % errorStr)
    return


def T_03_RecvRSSITest_A(product):
    u"单板ADC电路测试-计算RSRB4单板接收射频信号的RSSI值测试"
    manulCheck(u'提示', u'请接入信号源', check="ok")
    try:
        proxy.open(PARAM["defaultNetOneIp"])
        fpga_pll.config()
        proxy._write_fpga_reg(0x5a, 0x01)
        rx_pll.config(5722)
        proxy._write_fpga_reg(0x59, 0x00)
        proxy._write_fpga_reg(0x50, 0x01)
        proxy._write_fpga_reg(0x51, 0x02)
        proxy._write_fpga_reg(0x58, 0x01)
        proxy._write_fpga_reg(0x56, 0x00)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x52, 0x00)
        proxy._write_fpga_reg(0x95, 0x03)
        proxy._write_fpga_reg(0x96, 0x01)
        proxy._write_fpga_reg(0x9b, 0x01)
        proxy._write_fpga_reg(0x90, 0x01)
        time.sleep(0.5)

        fpga_addr = "3f"
        fpga_addr = int(str(fpga_addr), 16)
        fpga_value = proxy._read_fpga_reg(fpga_addr)
        print hex(fpga_value)[2:]

        proxy._write_fpga_reg(0x5a, 0x1)
        proxy._write_fpga_reg(0x46, 0x1)
        proxy._write_fpga_reg(0x58, 0x0)
        proxy._write_fpga_reg(0x5a, 0x0)
        print "关闭接收"

    except Exception as e:
        raise AbortTestException(message=e)
    finally:
        proxy.close()

    if fpga_value > int(PARAM["recvRSSILow"]) and fpga_value < int(PARAM["recvRSSIHigh"]):
        return {u"接收RSSI值为：":fpga_value}
    else:
        PARAM["failNum"] = "1"
        raise TestItemFailException(failWeight=1, message=u"接收RSSI测试不通过,值:%d:"%fpga_value)


def T_04_RecvRSSITest222_A(product):
    u"无连接测试-计算RSRB4单板接收射频信号的RSSI值测试"
    manulCheck(u'提示', u'请断开信号源', check="ok")
    try:
        proxy.open(PARAM["defaultNetOneIp"])
        fpga_pll.config()
        proxy._write_fpga_reg(0x5a, 0x01)
        rx_pll.config(5722)
        proxy._write_fpga_reg(0x59, 0x00)
        proxy._write_fpga_reg(0x50, 0x01)
        proxy._write_fpga_reg(0x51, 0x02)
        proxy._write_fpga_reg(0x58, 0x01)
        proxy._write_fpga_reg(0x56, 0x00)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x52, 0x00)
        proxy._write_fpga_reg(0x95, 0x03)
        proxy._write_fpga_reg(0x96, 0x01)
        proxy._write_fpga_reg(0x9b, 0x01)
        proxy._write_fpga_reg(0x90, 0x01)
        time.sleep(0.5)
        # 工装发射单音

        proxy._write_fpga_reg(0x52, 0x7f)
        fpga_addr = "3f"
        fpga_addr = int(str(fpga_addr), 16)
        fpga_value = proxy._read_fpga_reg(fpga_addr)
        print hex(fpga_value)[2:]

        proxy._write_fpga_reg(0x5a, 0x1)
        proxy._write_fpga_reg(0x46, 0x1)
        proxy._write_fpga_reg(0x58, 0x0)
        proxy._write_fpga_reg(0x5a, 0x0)
        print "关闭接收"

    except Exception as e:
        raise AbortTestException(message=e)
    finally:
        proxy.close()

    if fpga_value > int(PARAM["recvNothingLow"]) and fpga_value < int(PARAM["recvNothingHigh"]):
        return {u"无输入接收RSSI值为：": fpga_value}
    else:
        PARAM["failNum"] = "1"
        raise TestItemFailException(failWeight=1, message=u"无输入接收RSSI测试失败,值:%d:" % fpga_value)
