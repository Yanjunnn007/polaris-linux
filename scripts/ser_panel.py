# -*- coding: utf-8 -*-
# 查 polaris 面板驱动状态: 内核版本 / panel driver / DRM / DSI / backlight
import serial, time
PORT='COM5'; BAUD=115200
s=serial.Serial(PORT,BAUD,timeout=4); s.reset_input_buffer()
def send(c,w=4):
    s.write(c.encode()+b'\n'); time.sleep(w)
    o=b''
    while s.in_waiting: o+=s.read(s.in_waiting); time.sleep(0.3)
    return o.decode('utf-8','replace')
send('',1.5)
print('=== uname ===')
print(send('uname -a',3)[-300:])
print('=== nt35596 / panel driver in modules ===')
print(send('grep -ri nt35596 /lib/modules/ 2>/dev/null | head -5; ls /lib/modules/*/kernel/drivers/gpu/drm/panel/ 2>/dev/null | head -30',5)[-1500:])
print('=== dmesg: panel/dsi/drm/backlight ===')
print(send('dmesg 2>/dev/null | grep -iE "panel|dsi|drm|nt35596|backlight|wled|mdss" | head -40',5)[-3000:])
print('=== dmesg: errors ===')
print(send('dmesg 2>/dev/null | grep -iE "fail|error|probe" | head -20',4)[-2000:])
s.close()
