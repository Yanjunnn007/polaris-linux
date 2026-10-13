# -*- coding: utf-8 -*-
import serial, time, sys
# 监听 COM5 最多 60 秒，抓内核/initramfs 输出
try:
    s=serial.Serial('COM5',115200,timeout=2)
except Exception as e:
    print('open fail:', e); sys.exit(1)
s.reset_input_buffer()
t0=time.time(); buf=b''
print('listening 60s on COM5 ...'); sys.stdout.flush()
while time.time()-t0 < 60:
    if s.in_waiting:
        chunk=s.read(s.in_waiting); buf+=chunk
        sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
    else:
        time.sleep(0.2)
s.close()
print('\n=== END ===')
