#!/sbin/sh
modprobe loop 2>/dev/null
L=$(losetup -fP --show --sector-size 4096 /dev/block/sda21)
echo "loop=$L"
ls -la ${L}p1 ${L}p2
echo "=== blkid ==="
blkid ${L}p1 ${L}p2
echo "=== expected ==="
echo "boot=<boot-partition-uuid> root=<rootfs-partition-uuid>"
echo "(刷机前先记录 blkid 输出，或用脚本参数传入)"
losetup -d $L
