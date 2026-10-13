# -*- coding: utf-8 -*-
import serial, time, sys
PORT='COM5'; BAUD=115200
s=serial.Serial(PORT,BAUD,timeout=2); s.reset_input_buffer()
def rd(w=2):
    time.sleep(w); o=b''
    while s.in_waiting: o+=s.read(s.in_waiting); time.sleep(0.2)
    return o.decode('utf-8','replace')
def send(c,w=2):
    s.write(c.encode()+b'\n'); return rd(w)
# 唤醒
send('',1.5)
print('WAKE:', repr(rd(1.5)[-200:]))
# 试回车看有没有 login 提示或 shell
r=send('',2)
print('ENTER:', repr(r[-300:]))
# 如果提示 login, 试 user
r=send('user',2.5)
print('USER:', repr(r[-300:]))
r=send('2832576070',2.5)
print('PASS:', repr(r[-300:]))
# 测试命令
r=send('id; uname -a',3)
print('CMD:', repr(r[-400:]))
s.close()
