# -*- coding: utf-8 -*-
# 读取 pmOS USB 串口 (COM5) 的输出，看系统状态
import serial, sys, time

PORT = 'COM5'
BAUD = 115200
try:
    s = serial.Serial(PORT, BAUD, timeout=2)
except Exception as e:
    print('打开串口失败:', e)
    sys.exit(1)

print('已连接 %s @ %d，先读 5 秒现有输出...' % (PORT, BAUD))
s.reset_input_buffer()
# 先发个回车，触发 shell 提示符或登录提示
s.write(b'\r\n')
time.sleep(1)

buf = b''
start = time.time()
while time.time() - start < 6:
    n = s.in_waiting
    if n:
        data = s.read(n)
        buf += data
    else:
        time.sleep(0.2)

text = buf.decode('utf-8', 'replace')
print('===== 串口输出 (最近) =====')
print(text[-4000:] if len(text) > 4000 else text)
print('===== 结束 =====')
s.close()
