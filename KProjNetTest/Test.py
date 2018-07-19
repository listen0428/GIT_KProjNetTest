# -*- coding: utf-8 -*-
__author__ = 'few'
# 创建时间 2018/3/24 12:27 

import re


ip = '192.168.1.1'
# complier = '[1-2][0-9][0-9].(1[0-9][0-9])'
result = re.search('(^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',ip)
print(result.span())
print(len(ip))
if result.span()[1]==len(ip):
    x = re.split('\.',ip)
if len(x) == 4:
    for temp in x:
        if int(temp) < 256:
            result0 = True
            print(int(temp))
        else:
            result0 = False
            break

print(result0)
print(x)
import time
time.sleep(10)
