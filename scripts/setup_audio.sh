#!/bin/sh
# Xiaomi MIX 2S (polaris) 扬声器与音频环境配置脚本
# 功能：配置 ALSA UCM2 拓扑映射，激活 TI TAS2559/TAS2560 Smart PA，并设置 PulseAudio 默认外放通道

set -e

echo "[1/4] 配置 ALSA UCM2 拓扑链接..."
sudo mkdir -p "/usr/share/alsa/ucm2/conf.d/sdm845"
sudo ln -sf ../../Xiaomi/beryllium/beryllium.conf "/usr/share/alsa/ucm2/conf.d/sdm845/Xiaomi Mi MIX 2S.conf"

echo "[2/4] 重载 ALSA UCM 状态并激活 HiFi 外放..."
alsaucm -c hw:0 reload || true
alsaucm -c hw:0 set _verb HiFi set _enadev Speaker1 || true

echo "[3/4] 开启 QDSP6 MI2S 路由并设置放大器增益..."
amixer -c 0 cset name='QUAT_MI2S_RX Audio Mixer MultiMedia1' 1 || true
amixer -c 0 cset name='TAS2560 DAC Playback Volume' 15 || true
amixer -c 0 cset name='TAS2559 DAC Playback Volume' 15 || true
sudo alsactl store || true

echo "[4/4] 切换 PulseAudio 默认 Sink 为外放扬声器..."
pactl set-card-profile alsa_card.platform-sound "Voice Call (Headphones, Mic, Speaker)" 2>/dev/null || true
pactl set-default-sink alsa_output.platform-sound.Voice_Call__Speaker__sink 2>/dev/null || true

echo "=== 音频配置完成！==="
echo "测试发声: paplay /usr/share/sounds/alsa/Front_Center.wav"
