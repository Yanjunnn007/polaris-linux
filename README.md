# Xiaomi Mi MIX 2S (polaris) — Linux 主线移植补丁集

让小米 MIX 2S（代号 **polaris**，高通骁龙 845 / SDM845）在 [postmarketOS](https://postmarketos.org)
上达到日常可用：**外放扬声器、Type-C OTG 双角色盲插、后置主摄出图**全部打通。

> 本项目是**移植记录 + 补丁集**，不是 ROM 分发。所有改动以 patch 形式提供，
> 可叠加到 [sdm845-mainline](https://gitlab.com/sdm845-mainline/linux) 源码自行编译。

---

## 一、成果概览

| 子系统 | 状态 | 说明 |
|---|---|---|
| 显示 + 触摸 + GPU | ✅ | 修复 3 个叠加的内核 bug（DSI PLL / panel 时序 / GPU 固件路径） |
| WiFi | ✅ | ath10k / WCN3998，开机自动加载 |
| 蓝牙 + 蓝牙音频 | ✅ | hci_uart（需杀 greetd 的 pulseaudio 实例，见已知问题） |
| **电池电量计 (PMI8998 FG)** | ✅ | **精确电量**：启用 PMI8998 库仑计/电量计，桌面顶栏与 UPower 实时显示准确电量、电压、温度与充放电状态 |
| **Type-C 自动盲插 + OTG 5V 升压** | ✅ | **本项目重点 1**：PMI8998 TCPM 硬件 CC 检测 + 5V boost 供电 + DWC3 DRP 动态切换 |
| **后置主摄（IMX363）** | ✅ | **本项目重点 2**：4032×3024 全分辨率出图、AK7372 VCM 物理调焦、libcamera 原生 3A |
| **内置双扬声器 + 听筒外放** | ✅ | **本项目重点 3**：TI TAS2559 + TAS2560 双 Smart PA、Hexagon ADSP 固件、ALSA UCM2 |
| USB-NCM + SSH | ✅ | 插电脑自动转 Device 模式，`172.16.42.1` |
| 移动数据 | ✅ | rmnet_ipa0 |
| 整机偶发冻结 | ⚠️ 未根治 | 长时间亮屏且无人操作后可能硬冻结，疑为 Adreno GPU 电源管理 |

详细的根因分析与排查过程见 `docs/`。

---

## 二、目录结构

```
.
├── patches/                 # 内核 / libcamera 补丁（按依赖顺序编号）
│   ├── 0001-...0011-*.patch
│   └── config/              # pmaports 内核包定义与 config
├── docs/                    # 中文技术文档：硬件参数、攻坚过程、坑与复盘
│   ├── 01-硬件参数实测.md    # 从原厂 dtb 提取的 GPIO / 供电 / I2C 全表
│   ├── 02-OTG-攻坚与修复.md
│   ├── 03-音频-攻坚与修复.md
│   ├── 04-相机-攻坚与修复.md
│   ├── 05-WiFi与其他子系统修复.md
│   ├── 06-音频-架构逆向.md
│   ├── 07-完整技术记录.md
│   └── 08-电池电量计-攻坚与修复.md
└── scripts/                 # 调试与运维脚本（串口 / OTG / 拍照 / 备份）
```

---

## 三、补丁清单

补丁针对 **Linux 7.1.0-rc1（sdm845-mainline fork）**。
**编号顺序与 `patches/config/APKBUILD` 的 `source=` 列表一致**，
即 `pmbootstrap` 实际构建顺序 —— 请按此顺序应用。

| # | 补丁 | 改动文件 | 作用 |
|---|---|---|---|
| 0001 | `drm-msm-dsi-10nm-pll-digtop-fix` | `dsi_phy_10nm.c` | 修复 DSI PLL digtop 配置，解决显示点不亮 |
| 0002 | `drm-panel-nt35596s-prepare-prev-first` | `panel-novatek-nt35596s.c` | 修正 panel 初始化顺序，消除时序竞争 |
| 0003 | `arm64-dts-sdm845-polaris-wifi-snoc-quirk` | `sdm845-xiaomi-polaris.dts` | WiFi NoC 路径 quirk，避免启动卡死 |
| 0004 | `arm64-dts-sdm845-polaris-audio-tas2559-tas2560` | `sdm845-xiaomi-polaris.dts` | **音频**：ADSP + TAS2559/TAS2560 双 Smart PA + 声卡 |
| 0005 | `regulator-qcom-usb-vbus-pmi8998` | `qcom_usb_vbus-regulator.c` | 让 VBUS 稳压器支持 PMI8998 |
| 0006 | `usb-dwc3-drd-vbus-control` | `dwc3/core.h`, `dwc3/drd.c` | DWC3 DRP 下允许控制 VBUS |
| 0007 | `typec-qcom-pmic-typec-pmi8998-tcpm` | `qcom_smbx.c`, `tcpm/qcom/*`（含 2 个新文件） | **OTG 核心**：为 PMI8998 添加完整 TCPM 支持 |
| 0008 | `arm64-dts-sdm845-polaris-usb-otg` | `sdm845-xiaomi-polaris.dts` | OTG 设备树：`battery` + `pmi8998_charger` + VBUS + Type-C + DWC3 DRP |
| 0009 | `arm64-dts-sdm845-polaris-camera` | `sdm845-xiaomi-polaris.dts`, `imx363.c`, `ak7375.c` | **相机**：CAMSS / CCI / IMX363 全分辨率 + VCM 对焦 |
| 0010 | `arm64-dts-sdm845-polaris-battery-fg` | `sdm845-xiaomi-polaris.dts` | **电量计**：启用 `pmi8998_fg`，上报容量与充放电状态 |
| 0011 | `libcamera-imx363-sensor-properties` | `camera_sensor_helper.cpp`, `camera_sensor_properties.cpp` | **给 libcamera 加 IMX363 支持**（发给 libcamera 项目，非内核） |

### 依赖关系

```
显示:   0001 → 0002
音频:   0004（依赖 fork 的 tas2559.c 驱动，见下）
OTG:    0005 → 0006 → 0007 → 0008
电量:   0010（硬依赖 0008 创建的 &pmi8998_charger 节点）
相机:   0009（内核） + 0011（libcamera）
```

**五个补丁改同一个 dts 文件**（0003 / 0004 / 0008 / 0009 / 0010），顺序敏感。
其中 `0010` 必须在 `0008` 之后，否则 apply 失败。

### ⚠️ 应用时必须加 `-C1`

这些补丁由 `diff -ruN` 基于"部分补丁已应用"的树生成，行号上下文带偏移。
`git apply` 默认严格匹配会失败：

```bash
for p in ../patches/0*.patch; do
    git apply -C1 "$p" || echo "FAILED: $p"
done
```

实测 10 个内核补丁在 `-C1` 下**全部通过**。
（用 `pmbootstrap` 构建则无需关心 —— `APKBUILD` 里的 `patch` 命令本身容忍偏移。）

### ⚠️ 重要依赖说明（音频）

补丁 0004 使用的 `tas2559` 驱动**不在 Linux 上游**（上游只有 `tas2557`），
它存在于 `sdm845-mainline/linux` 的 `sdm845/7.1-dev` 分支（作者 Joel Selvaraj）。
因此音频补丁只能在 **sdm845-mainline fork** 上编译。

---

## 四、编译与刷入

### 前提

- 一部已解锁 bootloader 的 MIX 2S（polaris）
- `pmbootstrap` 环境，或自行编译 sdm845-mainline 内核

### 方式 A：用 pmaports 构建（推荐）

```bash
# 1. 克隆 sdm845-mainline 内核源码
git clone https://gitlab.com/sdm845-mainline/linux -b sdm845/7.1-dev
cd linux

# 2. 应用补丁（必须 -C1，按编号顺序）
for p in /path/to/patches/0*.patch; do
    echo "==> $p"
    git apply -C1 "$p" || echo "    FAILED"
done

# 3. 用 config/ 里的配置编译
cp /path/to/patches/config/config-postmarketos-qcom-sdm845.aarch64 .config
make ARCH=arm64 LLVM=1 olddefconfig
make ARCH=arm64 LLVM=1 -j$(nproc)
```

> 更省事的做法：把 `patches/` 里的补丁直接放进
> `pmaports/device/community/linux-postmarketos-qcom-sdm845/`，
> 更新 `APKBUILD` 的 `source=` 与 `sha512sums`，然后
> `pmbootstrap build linux-postmarketos-qcom-sdm845`。
> 这样走的是 `patch` 命令，不需要 `-C1`。

### 方式 B：叠加到已有 pmOS 安装

见 `docs/07-完整技术记录.md` 的构建章节。

### 刷入

```bash
# boot 分区
fastboot flash boot boot.img
# 内核模块需同步（否则模块不加载）
# 详见 docs/ 中的刷机流程说明
```

> ⚠️ **刷机有风险，务必备份。** 建议先用 TWRP 完整备份所有分区。

---

## 五、已知问题

### 1. 整机偶发硬冻结（未根治）

- 长时间亮屏**且无人操作**后可能硬冻结（触摸/画面/USB 全无响应）；**操作屏幕时不会冻**
- 疑为 Adreno 630（`506a000.gmu`）运行时电源管理缺陷（GMU 从不上报 ready）
- **未根治**，介意者慎刷。排查记录见 `docs/07-完整技术记录.md`

### 2. 蓝牙音频需手工处理

- `greetd` 会拉起 `pulseaudio` 抢占 A2DP
- 临时解法：杀掉 greetd 的 pulseaudio 进程后重连耳机

---

## 六、技术要点（值得一读的部分）

这次移植里踩过 **3 个"想当然"导致的弯路**，都写在 `docs/` 里：

1. **参数来源错误**：早期排查用了 Mi 8 Pro（Equuleus）的 dtb 当参照，导致功放型号、GPIO 全部对不上。
   教训：**先确认参照物是不是目标机型**。

2. **错误归因**：把 `DMA txn failed` 当成"GPI DMA 控制器故障"，实际是 I2C 从设备 NACK 的报错形式
   （SDM845 的 QUP 禁用了 FIFO，所有传输必须走 GPI DMA，任何 NACK 都以这个形式出现）。

3. **双芯片架构**：TAS2559 驱动是**双芯片驱动**（同时管理 TAS2559 + TAS2560），
   probe 时向两个地址都写、且第二个的结果会覆盖第一个 —— 单芯片配置必然失败。

参考坐标：`docs/01-硬件参数实测.md` 有从原厂 dtb 提取的完整 GPIO / 供电 / I2C 表，
同机型移植可以直接用。

---

## 七、致谢

本项目站在这些工作的基础上：

- [sdm845-mainline](https://gitlab.com/sdm845-mainline/linux) — **Casey Connolly**、**Aster Boese**、**Joel Selvaraj**
  （尤其 `tas2559.c` 驱动）
- **Molly Sophia** — polaris 初始移植
- **Icenowy Zheng** — panel 修复
- **Dmitry Baryshkov**、**Luca Weiss** — DSI PLL 修复
- postmarketOS 社区

---

## 八、许可

- **内核补丁**：GPL-2.0-only（与 Linux 内核一致）
- **libcamera 补丁**：LGPL-2.1-or-later（与 libcamera 一致）
- **文档与脚本**：MIT（见 `LICENSE`）

> 本项目不重复分发固件二进制。所需固件由 postmarketOS 官方仓库的
> `firmware-xiaomi-polaris` 包提供，其中部分文件同时也存在于 linux-firmware。
> 注意该包的默认安装路径与 7.1 内核 dts 不一致，必须运行
> `scripts/patch_firmware.sh` 补齐 `Xiaomi/` 路径，否则 WiFi / 蓝牙 / GPU
> 都无法工作。

---

## 九、免责声明

刷机有风险，可能导致设备变砖或数据丢失。本项目作者不对任何损坏负责。
所有改动均在真机验证可用，但**不保证适用于其他设备或内核版本**。
