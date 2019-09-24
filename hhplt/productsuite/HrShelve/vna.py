#encoding:utf-8
"""

@author:zws
"""

import visa
import time
# start of M05_ANT

file='D:\\state02.sta'

rm = visa.ResourceManager()
E5071C = rm.open_resource('TCPIP0::222.255.255.201::5025::SOCKET')
E5071C.write(':MMEMory:LOAD:STATe "%s"' % (file))
E5071C.write(':SENSe1:FREQuency:CENTer %G' % (13560000.0))
E5071C.write(':SENSe1:FREQuency:SPAN %G' % (10000000.0))
E5071C.write(':CALCulate1:PARameter1:SELect') #选择trace1
E5071C.write(':DISPlay:WINDow:SPLit %s' % ('D1X1')) #屏幕分割为1X1
E5071C.write(':CALCulate1:PARameter1:COUNt %d' % (1)) #trace数目设定为1
E5071C.write(':CALCulate1:SELected:MARKer1:ACTivate') #激活marker
E5071C.write(':CALCulate1:SELected:MARKer1:X %G' % (12800000.0)) #设置marker频点
temp_values = E5071C.query_ascii_values(':CALCulate1:SELected:MARKer1:DATA?') #获取marker相关参数
data0 = temp_values[0] #获取marker S参数值
data1 = temp_values[1] #获取值为0，可忽略
data2 = temp_values[2] #获取marker 频点位置

E5071C.write(':CALCulate1:SELected:MARKer2:ACTivate') #激活marker2
E5071C.write(':CALCulate1:SELected:MARKer2:X %G' % (13320000.0)) # 设置marker2频点
temp_values = E5071C.query_ascii_values(':CALCulate1:SELected:MARKer2:DATA?') # 获取marker参数
data01 = temp_values[0] #获取marker S参数值
data11 = temp_values[1]
data21 = temp_values[2] #获取marker 频点位置

E5071C.write(':CALCulate1:SELected:MARKer3:ACTivate')
E5071C.write(':CALCulate1:SELected:MARKer3:X %G' % (13560000.0))
temp_values = E5071C.query_ascii_values(':CALCulate1:SELected:MARKer3:DATA?')
data02 = temp_values[0]
data12 = temp_values[1]
data22 = temp_values[2]

E5071C.write(':CALCulate1:SELected:MARKer4:ACTivate')
E5071C.write(':CALCulate1:SELected:MARKer4:X %G' % (13800000.0))
temp_values = E5071C.query_ascii_values(':CALCulate1:SELected:MARKer4:DATA?')
data03 = temp_values[0]
data13 = temp_values[1]
data23 = temp_values[2]

E5071C.write(':CALCulate1:SELected:MARKer5:ACTivate')
E5071C.write(':CALCulate1:SELected:MARKer5:X %G' % (14320000.0))
temp_values = E5071C.query_ascii_values(':CALCulate1:SELected:MARKer5:DATA?')
data04 = temp_values[0]
data14 = temp_values[1]
data24 = temp_values[2]

E5071C.write(':CALCulate1:SELected:MARKer6:ACTivate') #激活marker
E5071C.write(':CALCulate1:SELected:MARKer6:FUNCtion:TYPE %s' % ('MINimum')) #设置marker类型为获取最小值；
E5071C.write(':CALCulate1:SELected:MARKer6:FUNCtion:EXECute') #执行获取最小第1次
E5071C.write(':CALCulate1:SELected:MARKer6:FUNCtion:EXECute') #执行获取最小第2次
E5071C.write(':CALCulate1:SELected:MARKer6:FUNCtion:EXECute') #执行获取最小第3次
temp_values = E5071C.query_ascii_values(':CALCulate1:SELected:MARKer6:DATA?') #获取marker相关参数；
data05 = temp_values[0] #获取marker S参数值
data15 = temp_values[1]
data25 = temp_values[2] #获取marker 频点位置

E5071C.close()
rm.close()

# end of M05_ANT

