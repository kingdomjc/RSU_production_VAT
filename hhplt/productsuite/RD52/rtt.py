#encoding:utf-8
import visa
import time
# start of M1_RSU_Freq

# 配置功率频点5830 5840
MARKer_num_=1
freq=5830000000
rel_ampl=2
real0=30

rm = visa.ResourceManager()
N9020A = rm.open_resource('TCPIP0::222.255.255.210::inst0::INSTR')
N9020A.write(':SYSTem:PRESet')
N9020A.write(':TRACe1:TYPE %s' % ('WRITe'))
N9020A.write(':CONFigure:SANalyzer')
N9020A.write(':INITiate:IMMediate')
N9020A.write(':INITiate:CONTinuous %d' % (1))
N9020A.write(':UNIT:POWer %s' % ('DBMW'))
N9020A.write(':SENSe:FREQuency:CENTer %G' % (freq))
N9020A.write(':DISPlay:WINDow:TRACe:Y:SCALe:RLEVel:OFFSet %G' % (rel_ampl))
N9020A.write(':DISPlay:WINDow:TRACe:Y:SCALe:RLEVel %G' % (real0))
N9020A.write(':SENSe:FREQuency:SPAN %G' % (5000000.0))
N9020A.write(':SENSe:BWIDth:RESolution %G' % (100000.0))
N9020A.write(':CALCulate:MARKer1:CPSearch:STATe %d' % (1))
time.sleep(2)
temp_values = N9020A.query_ascii_values(':CALCulate:MARKer<%d>:Y?' % (MARKer_num_))
TSSI0 = temp_values[0]

N9020A.close()
rm.close()
