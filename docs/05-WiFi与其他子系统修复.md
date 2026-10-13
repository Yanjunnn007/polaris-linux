# WiFi / 蓝牙 / 其他子系统修复指南

> 主系统起来后的后续工作。当前状态见 README.md 第一节。

## WiFi (WCN3998, ath10k)

polaris 的 WiFi 芯片实测是 **WCN3998**（注意：固件包里目录名写的是 WCN3990，那是历史命名，芯片本体是 WCN3998，ath10k_snoc 驱动兼容）。

### 已知状态
- 固件已在 `firmware-xiaomi-polaris` 包内：
  - `ath10k/WCN3990/hw1.0/board-2.bin`（board 数据）
  - `qca/crbtfw21.tlv`、`qca/polaris/crnv21.bin`（蓝牙）
  - `qcom/sdm845/polaris/wlanmdsp.mbn`（WLAN DSP 固件）
- wiki 报告：5GHz 在 `apk update` 等大流量时会崩、2.4GHz 只能 ~1Mbps link / 20Mbps max → **Partial**

### 可能需要的一个 quirk
Icenowy 在 sdm845-mainline MR !85 里的另一个 commit（`3e6b21a7`）给 polaris dts 的 ath10k 节点加了：
```
qcom,snoc-host-cap-skip-quirk
```
作用：让 ath10k_snoc 能接受 Xiaomi 提供的固件 blob（不跳过会导致 firmware 校验失败、WiFi 起不来）。

检查方法（系统起来后）：
```sh
dmesg | grep -i ath10k
ip link        # 看有没有 wlan0
```
如果 ath10k 报 firmware 相关错误，需要在 dts 给 `&wifi` 节点加上面那个 quirk 重新编译内核（和我们打 panel patch 一样的流程）。

### 参考来源
- pmaports MR !4867（WiFi hotfix 随 panel 修复一起进过 pmaports）：
  https://gitlab.postmarketos.org/postmarketOS/pmaports/-/merge_requests/4867
- sdm845-mainline MR !85 commit `3e6b21a7`：
  https://gitlab.com/sdm845-mainline/linux/-/merge_requests/85

## 蓝牙
- 固件 `qca/crbtfw21.tlv` + `crnv21.bin` 已在包内，wiki 标 **工作**。

## 通话 / 短信 / 移动数据
- modem 固件 `qcom/sdm845/polaris/modem.mbn`、`mba.mbn`、`modemuw.jsn` 等在包内
- wiki：移动数据 **工作**、SMS **工作**、通话 **Partial**（能打通但无声音输入输出）
- 音频路由（voice call audio）在 SDM845 mainline 上是出了名的难，需要 q6asm/q6adm 配置，搁置

## 音频
- 扬声器/听筒：**Partial**（tas2559_uCDSP.bin 功放固件在包内）
- USB-C 音频：**不工作**（wiki 明确）

## 相机
- **Broken，2026 年仍无人修**，搁置。SDM845 的相机 ISP (Spectra 280) 在 mainline 基本没有可用驱动，社区共识是短期内不会有。

## 电池电量
- wiki 报告 sysfs `power_supply` 目录有时为空（电量读不到），待查。
