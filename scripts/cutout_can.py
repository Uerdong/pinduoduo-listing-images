# -*- coding: utf-8 -*-
"""把白底/浅底的单罐图抠成透明 PNG。

用法：python cutout_can.py <src.png> <dst.png> [--light 205] [--sat 30] [--erode 5]

原理：从四边泛洪，把「够亮 + 低饱和」的连通区域判为背景置透明；
再腐蚀收边去掉反光残留的白边，最后 1px 羽化。
"""
import argparse
from collections import deque

from PIL import Image, ImageFilter


def cutout(src, dst, light=205, sat=30, erode=5):
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    px = im.load()

    def bg(p):
        r, g, b = p[0], p[1], p[2]
        return min(r, g, b) > light and (max(r, g, b) - min(r, g, b)) < sat

    seen = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bg(px[x, y]) and not seen[y][x]:
                seen[y][x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if bg(px[x, y]) and not seen[y][x]:
                seen[y][x] = True
                q.append((x, y))

    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and bg(px[nx, ny]):
                seen[ny][nx] = True
                q.append((nx, ny))

    alpha = Image.new("L", (w, h), 255)
    ap = alpha.load()
    for y in range(h):
        row = seen[y]
        for x in range(w):
            if row[x]:
                ap[x, y] = 0

    if erode:
        alpha = alpha.filter(ImageFilter.MinFilter(erode))
    alpha = alpha.filter(ImageFilter.GaussianBlur(1))
    im.putalpha(alpha)

    bb = im.getbbox()
    im = im.crop(bb)
    im.save(dst)
    print("cutout %dx%d -> %dx%d  %s" % (w, h, im.width, im.height, dst))
    return im


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--light", type=int, default=205)
    ap.add_argument("--sat", type=int, default=30)
    ap.add_argument("--erode", type=int, default=5, help="MinFilter 尺寸，须为奇数")
    a = ap.parse_args()
    cutout(a.src, a.dst, a.light, a.sat, a.erode)
