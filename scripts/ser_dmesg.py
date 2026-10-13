# -*- coding: utf-8 -*-
import serial, time
PORT='COM5'; BAUD=115200
s=serial.Serial(PORT,BAUD,timeout=4); s.reset_input_buffer()
def send(c,w=3.5):
    s.write(c.encode()+b'\n'); time.sleep(w)
    o=b''
    while s.in_waiting: o+=s.read(s.in_waiting); time.sleep(0.3)
    return o.decode('utf-8','replace')
send('',1.5)
# 把关键日志写到 pmOS 日志盘可能复杂, 直接读 dmesg 最后 + init_functions 片段
print('=== dmesg 里 loop/mount/ext4 相关 ===')
r=send('dmesg 2>/dev/null | grep -iE "loop|ext4|mount|sda21|gpt|partition" | tail -20',4)
print(r[-2500:])
s.close()
