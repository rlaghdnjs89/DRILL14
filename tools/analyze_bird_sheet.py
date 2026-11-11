"""bird_animation.png 스프라이트 시트 분석 도구.

외부 라이브러리(PIL 등) 없이 PNG 를 직접 디코딩하여
1) 연결 성분(connected component) 분석으로 각 프레임의 실제 그림 영역(bbox)을 구하고
2) 파란 눈동자 픽셀의 무게중심으로 프레임마다 새 몸의 기준점(anchor)을 구한다.

출력은 bird.py 의 FRAME_DATA 에 그대로 붙여 넣을 수 있는 파이썬 리터럴이다.

사용법:  python tools/analyze_bird_sheet.py bird_animation.png
"""
import struct
import sys
import zlib


def load_rgba(path):
    data = open(path, 'rb').read()
    pos, idat = 8, b''
    while pos < len(data):
        length, = struct.unpack('>I', data[pos:pos + 4])
        chunk = data[pos + 4:pos + 8]
        if chunk == b'IHDR':
            w, h, depth, color = struct.unpack('>IIBB', data[pos + 8:pos + 18])
            assert depth == 8 and color == 6, 'RGBA 8bit PNG 만 지원'
        elif chunk == b'IDAT':
            idat += data[pos + 8:pos + 8 + length]
        pos += 12 + length

    raw, bpp = zlib.decompress(idat), 4
    stride = w * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else b if pb <= pc else c
                line[x] = (line[x] + pred) & 255
        rows.append(line)
        prev = line
    return w, h, rows


def find_components(w, h, rows):
    """8-이웃 연결 성분. 반환: [(x0, y0, x1, y1), ...] (위쪽 원점, 포함 좌표)"""
    seen = [bytearray(w) for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if rows[y][x * 4 + 3] and not seen[y][x]:
                stack = [(x, y)]
                seen[y][x] = 1
                x0 = x1 = x
                y0 = y1 = y
                while stack:
                    cx, cy = stack.pop()
                    x0, x1 = min(x0, cx), max(x1, cx)
                    y0, y1 = min(y0, cy), max(y1, cy)
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            nx, ny = cx + dx, cy + dy
                            if (0 <= nx < w and 0 <= ny < h and not seen[ny][nx]
                                    and rows[ny][nx * 4 + 3]):
                                seen[ny][nx] = 1
                                stack.append((nx, ny))
                comps.append((x0, y0, x1, y1))
    return comps


def eye_center(rows, box):
    """bbox 안의 파란 눈동자 픽셀 무게중심 (위쪽 원점)."""
    x0, y0, x1, y1 = box
    sx = sy = n = 0
    for y in range(y0, y1 + 1):
        r = rows[y]
        for x in range(x0, x1 + 1):
            R, G, B, A = r[x * 4:x * 4 + 4]
            if A > 200 and B > 150 and R < 80 and G < 150:
                sx, sy, n = sx + x, sy + y, n + 1
    return sx / n, sy / n


def main(path):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    w, h, rows = load_rgba(path)
    comps = find_components(w, h, rows)
    # 재생 순서: 행(위→아래) 우선, 같은 행에서는 왼쪽→오른쪽.
    # 행 구분은 눈 위치의 y 로 한다 (bbox 상단은 날개 때문에 들쭉날쭉하다).
    frames = []
    for box in comps:
        ex, ey = eye_center(rows, box)
        frames.append((box, ex, ey))
    frames.sort(key=lambda f: (int(f[2] // (h / 3)), f[1]))

    print(f'# sheet {w}x{h}, {len(frames)} frames')
    print('# (left, top, right, bottom, eye_x, eye_y)  -- 위쪽 원점, right/bottom 포함')
    print('FRAME_DATA = (')
    for (x0, y0, x1, y1), ex, ey in frames:
        print(f'    ({x0}, {y0}, {x1}, {y1}, {ex:.1f}, {ey:.1f}),')
    print(')')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'bird_animation.png')
