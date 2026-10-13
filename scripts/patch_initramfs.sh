#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
F="$HOME/pmaports-official/main/postmarketos-initramfs/init_functions.sh"
cp "$F" "$F.bak"
# Insert blkid cache-refresh before the find_root_partition at line 415
# (the one right after losetup inside the part_count==2 branch).
python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
lines = open(p).read().split('\n')
# find the exact block: line with 'subpartitions, but aren' then next 'find_root_partition'
idx = None
for i,l in enumerate(lines):
    if "subpartitions, but aren't our subpartition." in l:
        # next non-empty should be find_root_partition
        for j in range(i+1, i+4):
            if lines[j].strip() == 'find_root_partition':
                idx = j
                break
        break
if idx is None:
    print("INSERT POINT NOT FOUND"); sys.exit(1)
indent = '\t\t\t\t'
ins = [
    indent + "# Refresh the blkid cache so the loop sub-partitions just created",
    indent + "# by losetup become visible; 'blkid --uuid' below only reads the",
    indent + "# cache and would otherwise miss them (polaris auto-mount fix).",
    indent + "blkid >/dev/null 2>&1 || true",
]
lines[idx:idx] = ins
open(p,'w').write('\n'.join(lines))
print("inserted before line", idx+1)
PYEOF
echo "=== verify ==="
awk 'NR>=410 && NR<=424' "$F"
