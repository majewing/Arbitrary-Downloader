#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ICONSET_DIR="${SCRIPT_DIR}/icon.iconset"
ICNS_PATH="${SCRIPT_DIR}/icon.icns"
PNG_PATH="${SCRIPT_DIR}/icon.png"

python3 << 'PYEOF'
import struct, zlib, math

w, h = 512, 512
radius = 90
pixels = bytearray()

for y in range(h):
    pixels.append(0)
    for x in range(w):
        in_rect = True
        for cx_c, cy_c in [(radius, radius), (w - 1 - radius, radius),
                           (radius, h - 1 - radius), (w - 1 - radius, h - 1 - radius)]:
            if ((x < radius or x > w - 1 - radius) and (y < radius or y > h - 1 - radius)):
                if math.hypot(x - cx_c, y - cy_c) > radius:
                    in_rect = False
                    break

        if not in_rect:
            pixels.extend(b'\x00\x00\x00\x00')
            continue

        t = y / h
        r = int(40 + t * 35)
        g = int(100 + t * 60)
        b = int(210 - t * 20)

        cx, cy = w // 2, h // 2

        shaft_hw = 24
        shaft_top = int(h * 0.22)
        shaft_bot = int(h * 0.46)
        in_shaft = abs(x - cx) <= shaft_hw and shaft_top <= y <= shaft_bot

        arr_top = int(h * 0.38)
        arr_bot = int(h * 0.62)
        in_head = False
        if arr_top <= y <= arr_bot:
            prog = (y - arr_top) / max(arr_bot - arr_top, 1)
            hw = int(65 * prog)
            in_head = abs(x - cx) <= hw

        bar_y = int(h * 0.65)
        bar_hw = 75
        bar_h = 14
        in_bar = abs(x - cx) <= bar_hw and bar_y <= y <= bar_y + bar_h

        sw = 14
        in_ls = cx - bar_hw - sw <= x <= cx - bar_hw and bar_y - 28 <= y <= bar_y + bar_h
        in_rs = cx + bar_hw <= x <= cx + bar_hw + sw and bar_y - 28 <= y <= bar_y + bar_h

        if in_shaft or in_head or in_bar or in_ls or in_rs:
            r, g, b = 255, 255, 255

        pixels.extend(struct.pack('BBBB', r, g, b, 255))

raw = bytes(pixels)

def chunk(ctype, data):
    c = ctype + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

ihdr = struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)

import os
out = os.path.join(os.environ['ICON_DIR'], 'icon.png')
with open(out, 'wb') as f:
    f.write(b'\x89PNG\r\n\x1a\n')
    f.write(chunk(b'IHDR', ihdr))
    f.write(chunk(b'IDAT', zlib.compress(raw, 9)))
    f.write(chunk(b'IEND', b''))
PYEOF

rm -rf "${ICONSET_DIR}"
mkdir -p "${ICONSET_DIR}"

sips -z 16 16     "${PNG_PATH}" --out "${ICONSET_DIR}/icon_16x16.png"       >/dev/null 2>&1
sips -z 32 32     "${PNG_PATH}" --out "${ICONSET_DIR}/icon_16x16@2x.png"    >/dev/null 2>&1
sips -z 32 32     "${PNG_PATH}" --out "${ICONSET_DIR}/icon_32x32.png"       >/dev/null 2>&1
sips -z 64 64     "${PNG_PATH}" --out "${ICONSET_DIR}/icon_32x32@2x.png"    >/dev/null 2>&1
sips -z 128 128   "${PNG_PATH}" --out "${ICONSET_DIR}/icon_128x128.png"     >/dev/null 2>&1
sips -z 256 256   "${PNG_PATH}" --out "${ICONSET_DIR}/icon_128x128@2x.png"  >/dev/null 2>&1
sips -z 256 256   "${PNG_PATH}" --out "${ICONSET_DIR}/icon_256x256.png"     >/dev/null 2>&1
sips -z 512 512   "${PNG_PATH}" --out "${ICONSET_DIR}/icon_256x256@2x.png"  >/dev/null 2>&1
sips -z 512 512   "${PNG_PATH}" --out "${ICONSET_DIR}/icon_512x512.png"     >/dev/null 2>&1
cp "${PNG_PATH}" "${ICONSET_DIR}/icon_512x512@2x.png"

iconutil -c icns "${ICONSET_DIR}" -o "${ICNS_PATH}"

rm -rf "${ICONSET_DIR}" "${PNG_PATH}"
echo "Icon created: ${ICNS_PATH}"
