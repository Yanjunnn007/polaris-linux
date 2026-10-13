#!/bin/sh
# 切换为 OTG 主机模式 (开启 5V 升压供电)
echo host > /sys/class/usb_role/a600000.usb-role-switch/role
echo "已切换为 USB Host 模式，5V VBUS 供电已开启"
