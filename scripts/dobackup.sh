#!/sbin/sh
# polaris 全分区备份脚本（在 TWRP 的 adb shell 里运行）
# 用法: adb push dobackup.sh /tmp/ && adb shell "sh /tmp/dobackup.sh"
# 备份到手机 /sdcard/polaris_backup/，然后 adb pull 拉回电脑
OUT=/sdcard/polaris_backup
mkdir -p $OUT
cd /dev/block/bootdevice/by-name
for p in boot system vendor persist modem modemst1 modemst2 devinfo dtbo \
         xbl_a xbl_b abl_a abl_b tz_a tz_b hyp_a hyp_b cmnlib_a cmnlib_b \
         keymaster_a keymaster_b storsec_a storsec_b devcfg_a devcfg_b \
         aop_a aop_b qupfw_a qupfw_b logo splash vbmeta fsg sec limits; do
  if [ -e "$p" ]; then
    dd if=/dev/block/bootdevice/by-name/$p of=$OUT/$p.img bs=4096 2>/dev/null \
      && echo "OK  $p" || echo "FAIL $p"
  fi
done
echo "=== done, files in $OUT ==="
ls -la $OUT
