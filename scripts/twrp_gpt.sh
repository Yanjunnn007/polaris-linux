#!/sbin/sh
# 直接解析 sda21 的 GPT, 用 4096 扇区
DEV=/dev/block/sda21
echo "=== GPT header signature (should be 'EFI PART') ==="
dd if=$DEV bs=4096 skip=1 count=1 2>/dev/null | od -c | head -1
echo ""
echo "=== Partition entries: name + unique GUID ==="
# GPT 条目区在 LBA2, 每条 128 字节, 读前 2 条
# 条目偏移: 0-15 type GUID, 16-31 unique GUID, 56-127 name(UTF16LE)
dd if=$DEV bs=4096 skip=2 count=1 2>/dev/null > /tmp/entries.bin
# entry1 name at offset 56, entry2 at 128+56
echo "--- entry 1 name ---"
dd if=/tmp/entries.bin bs=1 skip=56 count=72 2>/dev/null | tr -d '\0' | od -c | head -2
echo "--- entry 1 unique GUID (bytes 16-31) ---"
dd if=/tmp/entries.bin bs=1 skip=16 count=16 2>/dev/null | od -A n -t x1
echo "--- entry 2 name ---"
dd if=/tmp/entries.bin bs=1 skip=$((128+56)) count=72 2>/dev/null | tr -d '\0' | od -c | head -2
echo "--- entry 2 unique GUID (bytes 144-159) ---"
dd if=/tmp/entries.bin bs=1 skip=$((128+16)) count=16 2>/dev/null | od -A n -t x1
