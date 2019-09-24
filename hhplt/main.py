#encoding:utf-8

'''
SHHIC工装平台应用程序入口

命令行入参：
    -f 配置文件
    -w 窗口模式（0-全屏，1-左边，2-右边）


'''
import os

from PyQt4 import QtGui,QtCore
from hhplt.ui.mainWnd import MainWnd

from hhplt.parameters import PARAM,SESSION,GLOBAL
import sys, getopt


#引入的测试对象：
# import hhplt.productsuite.gs10
#import hhplt.productsuite.gs10debug
#import hhplt.productsuite.gs10packaging
#import hhplt.productsuite.gs10patch
#import hhplt.productsuite.mockproduct
#import hhplt.productsuite.gs15
#import hhplt.productsuite.generaluhf
#import hhplt.productsuite.gs15packaging
#import hhplt.productsuite.gs15lanzhou
#import hhplt.productsuite.spotag
#import hhplt.productsuite.gs11
#import hhplt.productsuite.gs11patch
#import hhplt.productsuite.gs11packaging
#import hhplt.productsuite.gs15lanzhou

#import hhplt.productsuite.gs25

#import hhplt.productsuite.rd40
#import hhplt.productsuite.gs11sh
#import hhplt.productsuite.cpc433check
#import hhplt.productsuite.gs10cqpatch


#import hhplt.productsuite.HrShelve
#import hhplt.productsuite.CPC_NEW

#引入的本地工具
#import hhplt.localutil.gs15lz
import hhplt.productsuite.RD50C
import hhplt.productsuite.RD52
# import hhplt.productsuite.OBU
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
#######################################################

def __processCliParam():
    '''处理命令行参数'''
    opts, args = getopt.getopt(sys.argv[1:], "f:w:")
    argSet = set()
    for op, value in opts:
        if op == "-f":
            PARAM.__init__(value)
        if op == '-w':
            GLOBAL["WINDOW_MODE"] = (int(value))
        argSet.add(op)
    #以下处理默认参数
    if "-f" not in argSet:
        PARAM.__init__("hhplt/config.json") #如果命令行里没有指定配置文件，则使用此默认配置文件
    if "-w" not in argSet:
        GLOBAL["WINDOW_MODE"] = 0
        
    
def __initMainWindowSize(mode=0):
    '''处理窗口尺寸'''
    #mode:0-全屏,1-左边，2-右边
    global mainWnd
    desktopRect = QtGui.QApplication.desktop().availableGeometry()
    if mode == 0:
        mainWnd.setGeometry (10, 30,desktopRect.width()-30 , desktopRect.height()-25)
        mainWnd.setWindowState(QtCore.Qt.WindowMaximized)
    elif mode == 1:
        mainWnd.setGeometry (10, 30,desktopRect.width()/2-30 , desktopRect.height()-25)
    elif mode == 2:
        mainWnd.setGeometry (desktopRect.width()/2, 30, desktopRect.width()/2-30, desktopRect.height()-25)
    mainWnd.initDashbaord()
    
if __name__ == '__main__':
    # os.startfile(r'D:\Work\Project\RSU_RD50C_RD52\henan-c\TFTPSRV.EXE')
    __processCliParam()
    QtGui.QApplication.setStyle("Cleanlooks")
    app = QtGui.QApplication( sys.argv )
    mainWnd = MainWnd()
    __initMainWindowSize(GLOBAL["WINDOW_MODE"])
    mainWnd.show()
    GLOBAL["mainWnd"] = mainWnd
    app.exec_()


    
    
    
    


