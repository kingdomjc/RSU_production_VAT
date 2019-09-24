#encoding:utf-8
'''
Created on 2015-11-5
基于Windows摄像头的图像抓拍和识别
基于Zbar命令行工具，VideoCapture，及pytesser

@author: user
'''

from hhplt.deviceresource import TestResource,TestResourceInitException
from hhplt.deviceresource import AbortTestException,TestItemFailException
from hhplt.parameters import PARAM
# from VideoCapture import Device as CamDevice
#from pytesser import pytesser
import os


CAMS = []

# for camId in range(0,2):
#     try:
#         cam = CamDevice(camId, False)
#         CAMS.append(cam)
#     except Exception,e:
#         CAMS.append(None)

#他妈的这个SB摄像头驱动，在类中初始化会他娘的失败，不知道什么JB原因。所以在外部初始化3个，再由配置文件对应。他娘了个腚的。

class VideoCaptureAndParser(TestResource):
    TEMP_PHOTO_FILENAME = "TEMP_PHOTO.jpg"
    def __init__(self,initParam):
        pass
    
    def initResource(self):
        global CAMS
        if "barCodeCaptureId" in PARAM and PARAM["barCodeCaptureId"] != -1:
            self.barCodeCam = CAMS[int(PARAM["barCodeCaptureId"])]
        if "lcdCaptureId" in PARAM and PARAM["lcdCaptureId"] != -1:
            self.lcdCam = CAMS[int(PARAM["lcdCaptureId"])]
    
    def retrive(self):
        pass
    
    def captureLcdSnapshot(self,filename = TEMP_PHOTO_FILENAME):
        '''抓取LCD图片，返回文件名'''
        if self.lcdCam is None:return None
        try:
            self.lcdCam.saveSnapshot(filename)
            #TODO 处理图像切割
            return filename
        except Exception,e:
            raise AbortTestException(message=u"抓拍LCD图片异常,"+str(e))
        
    def captureBarcodeSnapshot(self,filename = TEMP_PHOTO_FILENAME):
        '''抓取条码图片，返回文件名'''
        try:
            self.barCodeCam.saveSnapshot(VideoCaptureAndParser.TEMP_PHOTO_FILENAME)
            return filename
        except Exception,e:
            raise AbortTestException(message=u"抓拍条码图片异常,"+str(e))
            
    def parseBarcode(self,filename = TEMP_PHOTO_FILENAME):
        '''识别条码'''
        dr = os.popen("zbarimg.exe %s"%filename)
        rst = dr.read().strip()
        if rst == "":raise TestItemFailException(failWeight=10,message=u"条码识别失败,请重新张贴")
        return rst.split(":")[1]
    
#    def parseText(self,filename = TEMP_PHOTO_FILENAME):
#        '''识别文字'''
#        if self.lcdCam is None: return None
#        try:
#            im = pytesser.Image.open(filename)
#            return pytesser.image_to_string(im)
#        except IOError,e:
#            print e,"no captured photo:",filename
#            raise e
