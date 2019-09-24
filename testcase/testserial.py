'''
Created on 2014-11-7

@author: user
'''


import serial
import time

s = serial.Serial("com3")
state = False
while True:
    time.sleep(0.2)
    if s.getCTS() != state:
        print state
        state = not state