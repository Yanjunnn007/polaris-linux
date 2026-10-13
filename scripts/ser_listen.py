# -*- coding: utf-8 -*-
import serial, time
PORT='COM5'; BAUD=115200
s=serial.Serial(PORT,BAUD,timeout=3)
s.reset_input_buffer()
# 多读一会,看有没有系统输出(启动日志/登录提示)
buf=b''
start=time.time()
while time.time()-start<8:
    if s.in_waiting:
        buf+=s.read(s.in_waiting)
    else:
        time.sleep(0.3)
print('=== 8秒串口输出 ===')
print(buf.decode('utf-8','replace')[-3000:])
# 发回车触发提示符
s.write(b'\r\n'); time.sleep(2)
b2=b''
while s.in_waiting: b2+=s.read(s.in_waiting); time.sleep(0.2)
print('=== 回车后 ===')
print(b2.decode('utf-8','replace')[-1000:])
s.close()
