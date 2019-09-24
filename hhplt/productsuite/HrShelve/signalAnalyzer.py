#encoding:utf-8
"""
频谱仪，用于读取阅读器的功率
@author:zws
"""
import visa
import time
# start of M06_RSU

MARKer_num_=1
rel_ampl=29

rm = visa.ResourceManager()
N9020A = rm.open_resource('TCPIP0::222.255.255.210::5025::SOCKET', open_timeout =1.2) #打开仪表IP地址
N9020A.timeout = 2000
N9020A.clear()
N9020A.write(':SYSTem:PRESet') #仪表复位
N9020A.write(':SENSe:FREQuency:CENTer %G' % (13560000.0)) #设定频点
N9020A.write(':SENSe:FREQuency:SPAN %G' % (0.0)) #设定0中频
N9020A.write(':SENSe:BWIDth:RESolution %G' % (8000000.0)) #RBW=8MHz
N9020A.write(':DISPlay:WINDow:TRACe:Y:SCALe:RLEVel:OFFSet %G' % (rel_ampl)) #补偿线损
N9020A.write(':SENSe:SWEep:TIME %G' % (1e-05)) #扫面谁建设定为10us
N9020A.write(':DISPlay:WINDow:TRACe:Y:SCALe:RLEVel %G' % (45.0)) #设定屏幕显示最大值45dBm
N9020A.write(':TRIGger:SEQuence:RFBurst:LEVel:ABSolute %G' % (30.0)) #设定RFbrust触发电平为30dBm
N9020A.write(':TRIGger:SEQuence:RFBurst:DELay %G' % (1e-05)) #设定RFbrust触发延时10us
N9020A.write(':TRIGger:SEQuence:RFBurst:DELay:STATe %d' % (1)) #设定RFbrust触发使能
N9020A.write(':TRIGger:SEQuence:RF:SOURce %s' % ('RFBurst')) #设定RFbrust触发
N9020A.write(':CALCulate:MARKer1:MODE %s' % ('POSition')) #增加marker1
N9020A.write(':CALCulate:MARKer1:X %G' % (5e-06)) #设定marker1位置5us
time.sleep(1) #延时1000ms
#temp_values = N9020A.query_ascii_values(':CALCulate:MARKer<%d>:Y?' % (MARKer_num_)) #获取marker1的幅度Y大小

temp_values = N9020A.query_ascii_values(':CALCulate:MARKer1:Y?') #获取marker1的幅度Y大小
Max = temp_values[0] #marker1 Y值大小
print Max




N9020A.close()
