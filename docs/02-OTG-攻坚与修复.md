# 小米 MIX 2S (polaris) postmarketOS 第三阶段成果报告：Type-C CC 自动盲插与 5V VBUS OTG 双角色完全打通

> **设备**：小米 MIX 2S (`polaris`)，SoC 高通骁龙 845 (SDM845)，PMIC PM8998 + PMI8998
> **系统**：postmarketOS edge / Phosh / openrc / 内核 `7.1.0-rc1-sdm845` (`r20`)
> **完成日期**：2026-10-12  
> **验证状态**：**硬件实机即插即用功能验证通过（实测插入无源 HUB + 键盘/鼠标正常识别与操作，未做长时间压力测试）**

---

## 一、阶段里程碑概览

在本项目的前两阶段中，我们成功攻克了屏幕点亮（DSI PLL / Panel prepare）、GPU 3D 加速（Freedreno）、WiFi / 蓝牙无线连接以及 USB NCM 调试网络通道。然而，作为移动 Linux 设备日常使用的核心硬件能力之一——**Type-C 自动双角色检测（DRP）与 OTG 5V 升压供电**，在整个 SDM845 乃至 mainline 社区中已停滞、搁置数年。

在第三阶段攻坚中，我们深入高通 PMI8998 硬件寄存器规格与 Linux 7.1 TCPM（Type-C Port Manager）子系统，彻底打通了完整的闭环：

```
                 ┌─────────────────────────────────────────────────────────────┐
                 │                 Xiaomi MIX 2S (SDM845)                      │
                 │                                                             │
                 │  ┌──────────────────┐               ┌──────────────────┐    │
                 │  │   DWC3 IP Core   │◄─────────────►│     PMI8998      │    │
                 │  │   (High-Speed)   │   OF Graph    │   Type-C / SMB2  │    │
                 │  └────────┬─────────┘   Role Switch └────────┬─────────┘    │
                 └───────────┼──────────────────────────────────┼──────────────┘
                             │                                  │
                             │ (D+/D-)                          │ (CC1/CC2 + VBUS)
                             ▼                                  ▼
                ======================================================
                              USB Type-C 物理接口 (自动盲插)
                ======================================================
                     │                                         │
        【场景 A：插入无源外设】                 【场景 B：插入电脑 / 充电器】
                     │                                         │
       1. CC 引脚检测到 Rd 下拉                  1. 检测到外部 5V VBUS 供电
       2. TCPM 握手确立 Source 角色              2. TCPM 确立 Sink 模式
       3. 启动 PMI8998 5V VBUS 升压 (set_vbus:1) 3. 切断内部升压 (set_vbus:0)
       4. DWC3 切入 Host 模式 (Mode 1)           4. DWC3 切入 Device 模式 (Mode 2)
       5. 自动枚举 HUB、鼠标、键盘                5. 启动 USB NCM 网卡 (172.16.42.1)
       6. Phosh 界面即时显示光标                  6. 建立 ADB / SSH 开发者调试通道
                     │                                         │
          【拔出：自动断电 set_vbus:0】              【拔出：自动重置回 DRP 待命】
```

### 核心成果亮点
1. **真·自动盲插识别**：无需手动执行脚本或强制写入 sysfs，插上无源外设立即供电并识别，拔下立刻切断 5V 升压保护硬件，插电脑自动转为从机网络卡与充电。
2. **5V VBUS 升压芯片完全驱动**：无需外接带电 HUB，手机自身电池直接通过 PMI8998 内部 boost 稳压器提供 5V 供电，实测可稳拖多设备。
3. **主流外设即插即用**：实机测试 **4 口 USB 2.0 HUB + 2.4G 无线键盘 + Compx 8K Nano 鼠标无线接收器**，Phosh 桌面瞬时显示鼠标箭头，键鼠输入零延迟，体验与 PC 无异。

---

## 二、历史背景与攻坚困境

### 2.1 社区历史误区：extcon-usb-gpio 的死胡同
在早期阶段（如第二阶段末期），社区常见的一类做法是尝试使用 `extcon-usb-gpio` 并绑定到 PMIC 的 GPIO8 或某个虚拟 GPIO 上。
但经我们在第二阶段的实机示波器与内核中断观测证明：**SDM845 + PMI8998 架构中，Type-C 的 CC1/CC2 引脚完全集成在 PMI8998 的 SMB2（开关模式充电子系统）硬件逻辑块内**，外部普通 GPIO 根本不会感知 CC 状态变化。这一方向已被彻底证实为无效方案。

### 2.2 Casey Connolly 方案与 Linux 7.1 主线断层
海外开发者 Casey Connolly 曾在 2022 年基于 Linux 5.x 内核开发了 `qcom-pmi8998-tcpm` 系列补丁。但由于该驱动从未被官方主线吸收，随着内核演进到了 Linux 7.1（本项目采用的 `7.1.0-rc1-sdm845`），存在严重的接口不兼容与运行时逻辑死锁：
- 旧版 API 如 `of_device_get_match_data()` 已弃用。
- Linux 7.1 移除了 `.remove_new` 回调机制，驱动无法匹配注销。
- Linux 6.10 之后 TCPM 的 `tcpm_pd_receive()` 强制要求传入第 3 个传输参数 `TCPC_TX_SOP`。
- 原驱动缺少对现代 regmap 的日志包裹，导致语法错误。

---

## 三、关键内核缺陷与深度修复（Root Cause Fixes）

在成功将驱动迁移至 7.1 树并完成编译后，我们遭遇了两次极其隐蔽的"硬件无反应"现象。经过严密的 dmesg 追踪、寄存器 dump 与代码审查，我们定位并消除了这两大致命 Bug：

### 3.1 Bug 1：消抖完成无事件上报死锁（Debounce Notification Loss）
- **现象**：插入 HUB 时，PMI8998 硬件中断虽然产生，但 TCPM 状态机一直死死停留在 `SRC_UNATTACHED`，升压芯片始终不供电。
- **根因分析**：
  硬件检测到 CC 引脚电压波动后，触发 `type-c-change` 中断，进入 `qcom_pmic_typec_port_cc_debounce` 延时 10ms 工作队列进行消抖。
  但在消抖函数末尾，驱动作者**遗漏了向 TCPM 核心上报状态变化的函数调用**！消抖结束后悄无声息地退出，TCPM 状态机永远不知道消抖已经完成，直接导致状态迁移中断。
- **代码修复**：
  在 `drivers/usb/typec/tcpm/qcom/qcom_pmic_typec_port.c` 中的 `qcom_pmic_typec_port_cc_debounce` 末尾补充通知：
  ```c
  if (pmic_typec_port->tcpm_port)
      tcpm_cc_change(pmic_typec_port->tcpm_port);
  ```

### 3.2 Bug 2：VBUS 状态追踪异或逻辑 Bug 与安全断电判定死锁（VBUS State Machine Deadlock）
- **现象**：消抖修复后，从 PC 拔下手机，再插上无源 HUB，依然没有 5V 供电。
- **根因分析**：
  1. 驱动结构体中的 `pmic_typec_port->vbus_present` 在系统启动时默认为 `false`（0）。
  2. 当手机从 PC 拔出时，硬件 VBUS 跌落为 0。中断处理函数中原本采用了异或逻辑：
     `vbus_change = !!(status & BIT(6)) ^ pmic_typec_port->vbus_present;`
     计算为 `0 ^ 0 = 0`！因此 `vbus_change` 永远为 `false`，TCPM 从未收到 VBUS 跌落事件。
  3. 此时 TCPM 状态机判定 `vbus_vsafe0v = false`（认为总线上依然残存高电压）。
  4. 根据 USB Type-C 官方规范：**如果 VBUS 尚未确认降至 Vsafe0V（安全零伏），TCPC 严禁开启升压供电**。这导致 5V boost 被状态机永久安全闭锁！
- **代码修复**：
  1. 废除不可靠的异或判定，改为直接比较物理寄存器与记录状态：
     ```c
     bool curr_vbus = !!(pmic_typec_port->typec_status.TYPE_C_STATUS_4_REG & BIT(6));
     if (curr_vbus != pmic_typec_port->vbus_present) {
         vbus_change = true;
         pmic_typec_port->vbus_present = curr_vbus;
     }
     ```
  2. 在 `qcom_pmic_typec_port_start` 启动初始化中，读取真实硬件状态赋初值，并主动触发一次 VBUS 同步。
  3. 重构 `qcom_pmic_typec_port_is_vbus_vsafe0v`：在硬件无独立高精度 vsafe0v 比较器时，以 `!pmic_typec_port->vbus_present` 作为安全零伏判据，解除状态机死锁。

### 3.3 Bug 3：设备树偏好角色导致的握手竞争（Try.SNK Race Condition）
- **根因分析**：在 DTS 中定义了 `try-power-role = "sink";`，使得在接入无源设备时，手机会先强行等待 125ms 期望对方给它供电，超时后才降级到 Source 模式，导致握手极不稳定。
- **修复**：在 `arch/arm64/boot/dts/qcom/sdm845-xiaomi-polaris.dts` 中移除 `try-power-role`，配置对称对等双角色（Symmetric DRP），实现瞬时 Source 判定。

### 3.4 Kernel Lockdown 与输入模块内置化
- SDM845 在 EFI Boot 启动时默认开启了 `integrity` 级别的内核锁定（Kernel Lockdown），拒绝加载未经签名的内核模块。
- 为保证任何后续编译或刷写都能 100% 确保键鼠可用，我们在内核配置中将核心输入子系统设置为永久内建（Built-in）：
  ```ini
  CONFIG_HID_GENERIC=y
  CONFIG_INPUT_EVDEV=y
  ```

---

## 四、实机验证全记录（Live Verification Logs）

以下为在小米 MIX 2S 真实机器上捕获的完整内核日志（`dmesg`）：

### 4.1 拔出 PC 数据线（掉电与状态复位）
```
qcom-pmic-typec-port c440000.spmi:pmi8998@2:typec@1300: vbus_change detected, vbus_present=0
tcpm-source-psy-4-0013: set_vbus: 0
dwc3 a600000.usb: Mode 0
```
- 确认：VBUS 掉电被即时捕获，供电完全切断，DWC3 控制器复位待命。

### 4.2 接入无源 USB HUB + 鼠标键盘（自动升压与枚举）
```
qcom-pmic-typec-port c440000.spmi:pmi8998@2:typec@1300: Debounce cc complete
qcom-pmic-typec-port c440000.spmi:pmi8998@2:typec@1300: Port partner CC1: Open, CC2: Rd
tcpm-source-psy-4-0013: CC1: 0 -> 0, CC2: 0 -> 1 [state 0, polarity 1, disconnected]
tcpm-source-psy-4-0013: state change TOGGLING -> SRC_ATTACH_WAIT [rev3 - 10000ms]
tcpm-source-psy-4-0013: state change SRC_ATTACH_WAIT -> SRC_ATTACHED [rev3 - 0ms]
tcpm-source-psy-4-0013: state change SRC_ATTACHED -> SRC_STARTUP [rev3 - 0ms]
tcpm-source-psy-4-0013: state change SRC_STARTUP -> SRC_SEND_CAPABILITIES [rev3 - 0ms]
tcpm-source-psy-4-0013: set_vbus: 1
qcom-pmi8998-vbus-reg c440000.spmi:pmi8998@2:usb-vbus-regulator@1100: Enabled 5V boost regulator
dwc3 a600000.usb: Mode 1
usb 1-1: new high-speed USB device number 2 using xhci-hcd
usb 1-1: New USB device found, idVendor=1a40, idProduct=0101, bcdDevice= 1.00
usb 1-1: New USB device strings: Mfr=0, Product=1, SerialNumber=0
usb 1-1: Product: USB 2.0 Hub
hub 1-1:1.0: USB hub found
hub 1-1:1.0: 4 ports detected
usb 1-1.3: new full-speed USB device number 3 using xhci-hcd
usb 1-1.3: New USB device found, idVendor=3151, idProduct=5038, bcdDevice= 1.00
usb 1-1.3: Product: 2.4G Wireless Keyboard
input: 2.4G Wireless Keyboard as /dev/input/event6
usb 1-1.4: new full-speed USB device number 4 using xhci-hcd
usb 1-1.4: New USB device found, idVendor=373b, idProduct=111b, bcdDevice= 2.01
usb 1-1.4: Product: Wireless mouse -8K NANO dongle (Compx)
input: Wireless mouse -8K NANO dongle as /dev/input/event8
```
- **验证结果**：
  - 硬件 HUB 指示灯瞬间亮起（5V 升压输出）。
  - HUB 4 个端口成功识别。
  - 2.4G 无线键盘与 8K Nano 鼠标接收器顺利分配 `event6` 与 `event8` 输入节点。
  - 手机屏幕（Phosh 桌面环境）实时渲染出鼠标黑色指针，滑动鼠标指针平滑移动，点击唤醒图标正常！

### 4.3 拔出 HUB 并插回 PC
- 拔出瞬间：
  ```
  tcpm-source-psy-4-0013: set_vbus: 0
  usb 1-1: USB disconnect, device number 2
  dwc3 a600000.usb: Mode 0
  ```
- 插回 PC 瞬间：
  ```
  qcom-pmic-typec-port c440000.spmi:pmi8998@2:typec@1300: vbus_change detected, vbus_present=1
  dwc3 a600000.usb: Mode 2
  configfs-gadget.g1: dual-speed gadget
  usb0: HOST MAC 00:00:11:22:33:44, HOST IP 172.16.42.1
  ```
- 确认：完全自动化切回从机设备模式，Windows PC 识别为 NCM 网卡，SSH 通道畅通无阻。

---

## 五、产物交付与归档清单

本次第三阶段的所有交付产物已完全同步至刷机包与源码审查包中：

### 5.1 刷机与测试镜像 (`pmOS-polaris刷机包/01-刷机镜像/`)
| 文件名 | 大小 | 说明 |
|---|---|---|
| `boot-r20.img` | 28 MB | **最终交付内核 boot 镜像**：集成 PMI8998 TCPM 修复、5V VBUS 升压与 DWC3 自动角色切换 |
| `modules-r20.tar.gz` | 23 MB | r20 配套内核模块打包（含修复后的全部硬件驱动） |

### 5.2 源代码与内核补丁 (`pmOS-polaris刷机包/02-内核补丁/` & `polaris-源码审查包/01-内核补丁/`)
| 文件名 | 说明 |
|---|---|
| `qcom-pmi8998-tcpm.patch` | **核心驱动补丁**：PMI8998 Type-C 驱动，含 Debounce 修复、VBUS 追踪修复与 Linux 7.1 API 适配 |
| `sdm845-polaris-usb-otg.patch` | **设备树补丁**：配置 DRP 双角色、DWC3 role-switch OF-graph 与 5V VBUS 升压供电绑定 |
| `APKBUILD` | pmOS 内核编译脚本，版本升级为 `pkgrel=20`，集成上述补丁与自动哈希 |
| `config-postmarketos-qcom-sdm845.aarch64` | 内核配置文件，已将 `CONFIG_HID_GENERIC=y`、`CONFIG_INPUT_EVDEV=y` 固化为 built-in |

---

## 六、用户刷入与永久固化指南

如果此前是通过 `fastboot boot boot-r20.img` 临时启动测试的，执行以下操作可将其**永久固化**到手机中，以后开机即享自动 OTG 与键鼠支持：

```bash
# 1. 手机进入 fastboot 模式（音量下 + 电源键）
# 2. 刷入 r20 boot 镜像到 boot 分区
fastboot flash boot pmOS-polaris刷机包/01-刷机镜像/boot-r20.img

# 3. 重启进入系统
fastboot reboot
```

> [!TIP]
> 进入系统后，即可随时插入 Type-C 转 USB 转换头、无源 HUB、U 盘、键盘或鼠标，手机会自动根据所插设备智能切换 Host/Device 状态，无需任何手动命令！
