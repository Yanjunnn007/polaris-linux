#!/bin/bash
PASS=pmos
IP=172.16.42.1
sshpass -p $PASS ssh -o PreferredAuthentications=password -o StrictHostKeyChecking=no user@$IP << 'EOF'
cat << 'EOSCRIPT' > /home/user/otg_hub_test.sh
#!/bin/bash
# OTG 无源 HUB / U盘 / 鼠标测试脚本 (带延时启动与自动恢复)

DELAY=${1:-0}
if [ "$DELAY" -gt 0 ]; then
    echo "=== 延时 $DELAY 秒启动：请在此期间拔掉电脑线，插上无源 HUB 和 U盘/鼠标 ==="
    sleep "$DELAY"
fi

LOG=/home/user/otg_test.log
exec > >(tee -a "$LOG") 2>&1

echo "=========================================="
echo "=== OTG Host 测试开始: $(date) ==="
echo "=========================================="

echo "[1] 切前状态:"
echo "  USB Role: $(cat /sys/class/usb_role/a600000.usb-role-switch/role 2>/dev/null)"
echo "  VBUS State: $(cat /sys/class/regulator/regulator.44/state 2>/dev/null)"

echo "[2] 释放 Gadget UDC (断开从机)..."
echo "" > /config/usb_gadget/g1/UDC 2>/dev/null
sleep 1

echo "[3] 切换为 Host 模式 (激活 PMI8998 5V VBUS 升压)..."
echo host > /sys/class/usb_role/a600000.usb-role-switch/role
sleep 2

echo "[4] 切后供电与角色:"
echo "  USB Role: $(cat /sys/class/usb_role/a600000.usb-role-switch/role 2>/dev/null)"
echo "  VBUS State: $(cat /sys/class/regulator/regulator.44/state 2>/dev/null)"
echo "  VBUS Users: $(cat /sys/class/regulator/regulator.44/num_users 2>/dev/null)"

echo "[5] 监控 USB 设备枚举 (测试 25 秒)..."
for i in $(seq 1 12); do
    echo "--- [${i}/12] (间隔 2s) ---"
    echo "USB 设备列表 (lsusb):"
    lsusb
    echo "存储块设备 (lsblk):"
    lsblk -o NAME,SIZE,TYPE,MOUNTPOINT 2>/dev/null
    sleep 2
done

echo "[6] dmesg 最新日志:"
dmesg | tail -30

echo "[7] 自动切回 Device 模式 (恢复 USB 从机供电安全与网络)..."
echo device > /sys/class/usb_role/a600000.usb-role-switch/role 2>/dev/null
sleep 1
echo "a600000.usb" > /config/usb_gadget/g1/UDC 2>/dev/null
sleep 2

echo "[8] 恢复后状态:"
echo "  USB Role: $(cat /sys/class/usb_role/a600000.usb-role-switch/role 2>/dev/null)"
echo "  VBUS State: $(cat /sys/class/regulator/regulator.44/state 2>/dev/null)"
echo "  UDC State: $(cat /sys/class/udc/a600000.usb/state 2>/dev/null)"

echo "=========================================="
echo "=== 测试结束: $(date) ==="
echo "=== 请插回电脑 USB 线恢复 SSH 连接 ==="
echo "=========================================="
EOSCRIPT

chmod +x /home/user/otg_hub_test.sh
echo "UPDATE_SUCCESS"
EOF
