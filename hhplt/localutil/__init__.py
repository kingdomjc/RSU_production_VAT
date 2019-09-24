#encoding:utf-8
'''
本地工具集

所有本地工具在本包内实现，在main.py中进行注册

'''
from hhplt.parameters import GLOBAL


REGISTERED_LOCAL_UTIL = []

def registerUiToMenu(dlgCls):
    '''向“本地工具”菜单注册界面'''
    REGISTERED_LOCAL_UTIL.append(dlgCls)