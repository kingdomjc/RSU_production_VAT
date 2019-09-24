#-*-coding:utf-8-*-
"""
Save test log for all
@author: Dawei
"""
import os
import time
import threading


file_p = None
log_file_prefix = r"log_file_"
print_lock = None
print_data_lock = None


def log_init():
    global file_p
    global print_lock
    global print_data_lock
    loop = 0
    print_lock = threading.Lock()
    print_data_lock = threading.Lock()
    while True:
        path = log_file_prefix + str(loop) + ".txt"
        if os.path.exists(path):
            loop += 1
            continue
        else:
            file_p = open(path, 'w+b')
            info = "save log to file: " + path + "\r\n"
            print info
            file_p.write(info)
            time_str = time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime(time.time()))
            log_str = "\r\n--------log start at:" + time_str + "--------"
            print log_str
            file_p.write(log_str)
            file_p.write("\r\n")
            break


def print_start(data):
    global file_p
    global print_lock
    print_lock.acquire()
    if type(data) is str:
        data_str = data
    else:
        data_str = "".join(data)

    strs = "\r\n/***************" + data_str + " START ***************/"
    print strs
    file_p.write(strs)
    file_p.write("\r\n")
    print_lock.release()


def print_end(data):
    global file_p
    global print_lock
    print_lock.acquire()
    if type(data) is str:
        data_str = data
    else:
        data_str = "".join(data)
    strs = "/***************" + data_str + " END ***************/"
    print strs
    file_p.write(strs)
    file_p.write("\r\n")
    print_lock.release()


def print_log(data):
    global file_p
    global print_lock
    print_lock.acquire()
    if type(data) is str:
        data_str = data
    else:
        data_str = "".join(data)
    print data_str
    file_p.write(data_str)
    file_p.write("\r\n")
    print_lock.release()


def print_data(data, info=''):
    global print_data_lock
    print_data_lock.acquire()
    if type(data) is list:
        data = data
    elif type(data) is str:
        data = [ord(x) for x in data]
    else:
        print "Type Error!"

    cnt = 0
    log_str = ""
    if len(info):
        print_log(info)
    for d in data:
        cnt += 1
        log_str += "0x%02x " % d
        if cnt % 16 == 0:
            print_log(log_str)
            log_str = ""
    if len(data) < 16:
        print_log("   [" + log_str + "]")
        print_data_lock.release()
        return
    if cnt % 16 != 0:
        print_log(log_str)
        #print_log('')
    print_data_lock.release()


def print_hex(data,datalen,info=''):
    global print_data_lock
    print_data_lock.acquire()
    if type(data) is list:
        data = data
    elif type(data) is str:
        data = [ord(x) for x in data]

    if len(info):
        print_log(info)

    for i in range(datalen):
        if i and i % 16 == 0:
            print ('')
        print '0x%02x ' % (data[i]),
    #print ''
    print_data_lock.release()


def print_error(data):
    global file_p
    global print_lock
    print_lock.acquire()
    if type(data) is str:
        data_str = data
    else:
        data_str = "".join(data)
    file_p.write(data_str)
    file_p.write("\r\n")

    time_str = time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime(time.time()))
    log_str = "\r\n--------log error at:" + time_str + "--------\r\n"
    print log_str
    file_p.write(log_str)
    print_lock.release()
    raise Exception(data_str)


def log_end(data=None):
    global file_p
    global print_lock
    print_lock.acquire()
    if data is None:
        info = "--------log end--------"
    else:
        if type(data) is str:
            info = data
        else:
            info = "".join(data)
    if file_p is not None:
        file_p.write(info)
        file_p.write("\r\n")
        time_str = time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime(time.time()))
        log_str = "\r\n--------log end at:" + time_str + "--------"
        print log_str
        file_p.write(log_str)
        file_p.close()
        file_p = None
    print_lock.release()




