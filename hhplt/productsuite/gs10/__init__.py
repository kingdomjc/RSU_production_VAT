#coding:utf-8
'''GS10 OBU生产测试'''




import hhplt.testengine.product_manage as product_manage
import battery,cq_overall_unit,trading,board_mending,cq_auto_board,manual_board,trading_mending,retradeAndValidateMac


#注册产品测试项
product_manage.registerProduct('GS10 OBU',(
                                           cq_auto_board, #单板自动测试工位
                                           manual_board, #单板手动测试工位
                                           board_mending, #单板维修工位
                                           trading_mending, #单板维修交易复测工位
                                           cq_overall_unit,    #整机
                                           trading,  #交易
#                                           retradeAndValidateMac    #检查MAC
                                           ))

'''
测试中使用的参数：

名称                                                              测试项                                含义                        默认值
--------------------------------------------------------------------
gs10.initParam.displayDirect    初始数据            显示方向
gs10.initParam.softwareVersion                软件版本号
gs10.initParam.hardwareVersion                硬件版本号
gs10.initParam.wakeupMode                    唤醒模式
gs10.initParam.amIndex                        AmIndex
gs10.initParam.transPower                    发射功率
gs10.initParam.txFilter                        TxFilter



gs10.initWanken.low.grade    初始唤醒灵敏度    初始低唤醒灵敏度粗调    
gs10.initWanken.low.level                    初始低唤醒灵敏度细调    
gs10.initWanken.high.grade                   初始高唤醒灵敏度粗调    
gs10.initWanken.high.level                    初始低唤醒灵敏度细调    

gs10.capPower.low            电容电路电压        电容电路电压判定低阈值
gs10.capPower.high                            电容电路电压判定高阈值
gs10.solarBatteryPower.board.low    太阳能电路电压(单板)            太阳能电路电压判定低阈值
gs10.solarBatteryPower.board.high                    太阳能电路打压判定高阈值
gs10.solarBatteryPower.overall.low    太阳能电路电压(整机)            太阳能电路电压判定低阈值
gs10.solarBatteryPower.overall.high                    太阳能电路打压判定高阈值
gs10.batteryPower.low        电池电路电压                    电池电路电压判定低阈值
gs10.batteryPower.high                            电池电路电压判定高阈值

       

gs10.wakeup.power.low    唤醒灵敏度                    低唤醒功率                    
gs10.wakeup.power.high                    高唤醒功率                    

gs10.receiveSensitivity.power     接收灵敏度测试        接收功率值                   
gs10.receiveSensitivity.frameNum                     发送总帧数                
gs10.receiveSensitivity.frameBorder                接收帧数判定低阈值        

gs10.esamDistrictCode.[单板前缀]    ESAM测试                            ESAM地区分散码                
gs10.boardBarPrefix                           单板前缀         



gs10.sendPower.low    发射功率测试        发射功率低判定阈值                
gs10.sendPower.high                    发射功率高判定阈值        

gs10.staticCurrent.low    静态电流测试            静态电流低判定阈值
gs10.staticCurrent.high                    静态电流高判定阈值
gs10.deepStaticCurrent.low    深度静态电流测试    深度静态电流低判定阈值
gs10.deepStaticCurrent.high                    深度静态电流判定高阈值


gs10.batteryOpenPower.low    电池开路电压        电池开路电压低判定阈值
gs10.batteryOpenPower.high                    电池开路电压高判定阈值
gs10.capOpenPower.low        电容开路电压            电容开路电压低判定阈值
gs10.capOpenPower.high                        电容开路电压高判定阈值

gs10.formalVersion.filename        下载正式版本                版本文件名称（不含路径）


'''









