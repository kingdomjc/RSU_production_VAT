#encoding:utf-8
'''
Created on 2016-7-27
测试摄像头抓拍
@author: user
'''
from VideoCapture import Device as CamDevice

cam0 = CamDevice(0, False)
cam0.saveSnapshot("F:\\sn0.jpg")

cam1 = CamDevice(1, False)
cam1.saveSnapshot("F:\\sn1.jpg")

cam2 = CamDevice(2, False)
cam2.saveSnapshot("F:\\sn2.jpg")


