# 补丁说明

这些补丁针对 **Linux 7.1.0-rc1**（[sdm845-mainline](https://gitlab.com/sdm845-mainline/linux) fork，
`origin/sdm845/7.1-dev` 分支）。

编号顺序与 `config/APKBUILD` 的 `source=` 列表一致 —— 也就是 `pmbootstrap`
实际构建时使用的顺序，**请按此顺序应用**。

## 应用方法

```bash
git clone https://gitlab.com/sdm845-mainline/linux -b sdm845/7.1-dev linux-polaris
cd linux-polaris

# 注意 -C1：这些补丁由 diff -ruN 生成，行号上下文带偏移
for p in ../patches/0*.patch; do
    echo "==> $p"
    git apply -C1 "$p" || echo "    !! 失败，请检查应用顺序"
done
```

> ⚠️ **必须加 `-C1`**。这些补丁基于"部分补丁已应用"的树生成，行号有偏移。
> `git apply` 默认要求上下文严格匹配会失败；`-C1` 允许 1 行宽松匹配，
> 实测 **11 个补丁全部通过**。
>
> 用 `pmbootstrap` 构建则不必操心 —— `APKBUILD` 用的是 `patch` 命令，
> 它本身容忍行偏移。

> `0011-libcamera-*.patch` **不要**应用到内核，它属于
> [libcamera](https://git.libcamera.org/libcamera/libcamera.git) 项目。

## 清单

### 内核补丁（0001–0010）

| # | 文件 | 改动文件 | 说明 |
|---|---|---|---|
| 0001 | `0001-drm-msm-dsi-10nm-pll-digtop-fix.patch` | `drivers/gpu/drm/msm/dsi/phy/dsi_phy_10nm.c` | DSI PLL digtop 配置修复（显示三连 bug 之一） |
| 0002 | `0002-drm-panel-nt35596s-prepare-prev-first.patch` | `drivers/gpu/drm/panel/panel-novatek-nt35596s.c` | panel 初始化顺序修正，消除 prepare 竞争 |
| 0003 | `0003-arm64-dts-sdm845-polaris-wifi-snoc-quirk.patch` | `arch/arm64/boot/dts/qcom/sdm845-xiaomi-polaris.dts` | WiFi NoC 路径 quirk |
| 0004 | `0004-arm64-dts-sdm845-polaris-audio-tas2559-tas2560.patch` | 同上 | **音频**：ADSP + TAS2559/TAS2560 双 Smart PA + 声卡 |
| 0005 | `0005-regulator-qcom-usb-vbus-pmi8998.patch` | `drivers/regulator/qcom_usb_vbus-regulator.c` | VBUS 稳压器支持 PMI8998 |
| 0006 | `0006-usb-dwc3-drd-vbus-control.patch` | `drivers/usb/dwc3/core.h`、`drivers/usb/dwc3/drd.c` | DRP 下允许控制 VBUS |
| 0007 | `0007-typec-qcom-pmic-typec-pmi8998-tcpm.patch` | `drivers/power/supply/qcom_smbx.c`、`drivers/usb/typec/tcpm/qcom/*`（8 文件，含 2 新增） | **OTG 核心**：PMI8998 完整 TCPM 支持 |
| 0008 | `0008-arm64-dts-sdm845-polaris-usb-otg.patch` | `arch/arm64/boot/dts/qcom/sdm845-xiaomi-polaris.dts` | OTG 设备树：`battery` + `pmi8998_charger` + VBUS + Type-C + DWC3 DRP |
| 0009 | `0009-arm64-dts-sdm845-polaris-camera.patch` | 同上、`drivers/media/i2c/imx363.c`、`drivers/media/i2c/ak7375.c` | **相机**：CAMSS/CCI/IMX363 全分辨率 + VCM 对焦 |
| 0010 | `0010-arm64-dts-sdm845-polaris-battery-fg.patch` | `arch/arm64/boot/dts/qcom/sdm845-xiaomi-polaris.dts` | **电量计**：启用 `pmi8998_fg`，关联 charger 与 battery |

### libcamera 补丁（0011）

| # | 文件 | 改动文件 | 说明 |
|---|---|---|---|
| 0011 | `0011-libcamera-imx363-sensor-properties.patch` | `src/ipa/libipa/camera_sensor_helper.cpp`、`src/libcamera/sensor/camera_sensor_properties.cpp` | IMX363 的 black level、增益模型、测试图模式 |

## 顺序依赖

**五个补丁改同一个 dts 文件**（0003 / 0004 / 0008 / 0009 / 0010），顺序敏感：

```
0003 (wifi quirk)
      ↓
0004 (audio)            ← 位置重要：APKBUILD 中 audio 排在 OTG 之前
      ↓
0008 (otg)              ← 新增 battery、pmi8998_charger、VBUS、Type-C
      ↓
0010 (battery-fg)       ← 硬依赖 0008 创建的 &pmi8998_charger 节点
      ↓
0009 (camera)
```

**0010 对 0008 有硬依赖**。`0010` 的全部内容就是：

```dts
 &pmi8998_charger {              ← 这个节点由 0008 引入
         monitored-battery = <&battery>;
         status = "okay";
 };
+
+&pmi8998_fg {                   ← 0010 在此处插入
+        power-supplies = <&pmi8998_charger>;
+        monitored-battery = <&battery>;
+        status = "okay";
+};
+
 &pmi8998_lsid0 {
```

所以 **0010 必须在 0008 之后**，反过来 apply 会失败。

编译依赖汇总：

```
显示:  0001 → 0002
音频:  0004（依赖 fork 的 sound/soc/codecs/tas2559.c）
OTG:   0005 → 0006 → 0007 → 0008
电量:  0010（依赖 0008）
相机:  0009（内核） + 0011（libcamera）
```

## 重要提示

### 补丁格式

这些补丁由 `diff -ruN` 生成，**不是** `git format-patch` 格式
（没有 commit message 和 `Signed-off-by`）。本地编译没问题；
若要提交到上游社区，需要重新整理成规范格式。

### 音频补丁的上游依赖

`0004` 引用的 `ti,tas2559` 驱动**不在 Linux 主线**。上游 `sound/soc/codecs/`
里只有 `tas2557.c`，而 `tas2559.c` 是 sdm845-mainline fork 独有的
（作者 Joel Selvaraj）。

因此音频功能**只能在 sdm845-mainline fork 上工作**。若将来该驱动上游，
此补丁可直接跟随。

### config/

`config/` 目录下是 postmarketOS 内核包的构建定义：

- `APKBUILD` — `linux-postmarketos-qcom-sdm845` 包定义（`pkgrel=28`）
- `config-postmarketos-qcom-sdm845.aarch64` — 内核 config

`APKBUILD` 里 `source=` 的排列顺序就是补丁的权威应用顺序。
如果你改动了任何补丁，`sha512sums` 需要重新生成：

```bash
pmbootstrap checksum linux-postmarketos-qcom-sdm845
```
