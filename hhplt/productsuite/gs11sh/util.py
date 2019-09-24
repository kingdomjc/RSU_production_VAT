#encoding:utf-8
"""

@author:zws
"""



def hexStrToSerialCmdFormat(hexStr):
    #从16进制字符串转换成串口命令格式，即0x11 0x33 ....
    return str(" ".join(["0x"+hexStr[2*i:2*i+2] for i in range(len(hexStr)/2)]))


def cmdFormatToHexStr(cmdStr):
    # 从命令字串转换成普通Hex字符串，即去掉Ox头
    return str("".join(map(lambda x: x.replace("0x", ""), cmdStr.split(" "))))