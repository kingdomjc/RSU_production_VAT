#encoding:utf-8
'''
Created on 2014-8-14
本地记录的参数
@author: 张文硕
'''
from hhplt.utils import ParamHolder

PARAM = ParamHolder()

SESSION = ParamHolder()
'''
#Session对象键值如下，其他业务自行使用：

product:正在测试的产品名称（string)
testsuite:正在测试的用例名称
isMend:是否属于维修测试，维修测试结果不上传服务
seletedTestItemNameList:选中的测试项目名称列表[string,]

testor:测试人员用户名
testorRole:测试人员角色
serverIp:服务器IP
workbay:工位

autoStart:测试项是否自动启动（boolean）

'''


GLOBAL = ParamHolder()
'''
#Global对象键值如下：

mainWnd:主窗口
logUi:日志栏

'''




