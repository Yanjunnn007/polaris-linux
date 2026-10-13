#!/bin/sh
# 切换为从机模式 (恢复连接电脑 / 安全断电)
echo device > /sys/class/usb_role/a600000.usb-role-switch/role
echo "已切换为 USB Device 模式，5V VBUS 供电已关闭"
