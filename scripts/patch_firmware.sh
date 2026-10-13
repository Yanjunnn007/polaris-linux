#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
DIR="$HOME/pmaports-official/device/archived/firmware-xiaomi-polaris"
F="$DIR/APKBUILD"
cp "$F" "$F.bak"

# 1) package(): also install zap shader to the Xiaomi/ path the 7.1 dts expects
python3 - "$F" <<'PYEOF'
import sys
p=sys.argv[1]; s=open(p).read()
old='''	for i in $(cat "$srcdir"/firmware.files); do
		install -Dm644 "$i" "$pkgdir/$i"
	done
}'''
new='''	for i in $(cat "$srcdir"/firmware.files); do
		install -Dm644 "$i" "$pkgdir/$i"
	done
	# linux >= 7.1 dts (sdm845-xiaomi-polaris.dts) requests the zap shader at
	# qcom/sdm845/Xiaomi/polaris/a630_zap.mbn; provide it there too so the
	# Adreno 630 GPU can finish probe and EGL/render nodes come up.
	install -Dm644 "$srcdir/$pkgname-$_version/lib/firmware/qcom/sdm845/polaris/a630_zap.mbn" \\
		"$pkgdir/lib/firmware/qcom/sdm845/Xiaomi/polaris/a630_zap.mbn"
}'''
assert old in s, "package() block not found"
s=s.replace(old,new)
open(p,'w').write(s)
print("package() patched")
PYEOF

# 2) initramfs gpu-firmware list: add Xiaomi path so GPU works from initramfs too
G="$DIR/30-gpu-firmware.files"
cp "$G" "$G.bak"
grep -q 'Xiaomi/polaris/a630_zap' "$G" || cat >> "$G" <<'EOF'
/lib/firmware/qcom/sdm845/Xiaomi/polaris/a630_zap.mbn
EOF
echo "=== 30-gpu-firmware.files now ==="
cat "$G"

# 3) bump pkgrel to force rebuild
sed -i 's/^pkgrel=0/pkgrel=1/' "$F"
grep -E 'pkgver=|pkgrel=' "$F"
