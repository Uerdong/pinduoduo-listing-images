#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为单个商品抽取场景组合，保证同类不重复、跨商品不撞车。

用法：
    python pick_scenes.py                       # 抽 3 个场景，seed 取当天
    python pick_scenes.py --n 3 --seed 20261106
    python pick_scenes.py --n 3 --avoid ice_bucket,fridge_shelf   # 避开上一款用过的

规则：
1. 每个场景属于一个「类」（冰饮 / 冷藏 / 餐饮 / 休闲 / 出行 / 节庆 / 极简）
2. 同一商品内不重复取同一类，保证画面差异
3. 固定 seed 结果可复现，写进任务卡便于追溯
4. --avoid 用来跨商品轮换，避免每款都冰箱 + 烧烤
"""
import argparse
import json
import random

# id: (名称, 类, 一句话画面)
SCENES = {
    "ice_bucket":    ("冰桶冰镇", "冰饮", "产品斜插入装满冰块的金属冰桶，冷凝水珠"),
    "ice_surface":   ("冰面水花", "冰饮", "产品立于碎冰面，周围水花冻结在半空"),
    "fridge_shelf":  ("冰箱层板", "冷藏", "冰箱中层玻璃隔板，产品直立贴板，冷光倒影"),
    "cooler_door":   ("便利店冷柜", "冷藏", "玻璃门冷柜层板，白冷光，门面轻微反光"),
    "bbq_table":     ("烧烤餐桌", "餐饮", "炭火烧烤与烤串，暖光，桌面油亮"),
    "hotpot":        ("火锅餐桌", "餐饮", "沸腾火锅与配菜，蒸汽，暖红调"),
    "home_dinner":   ("家常餐桌", "餐饮", "家常三菜一汤，木桌，午後自然光"),
    "dessert_bar":   ("甜品台", "餐饮", "浅色大理石台面，蛋糕与柑橘切片柔焦"),
    "office_desk":   ("办公桌", "休闲", "浅木办公桌，键盘与绿植，窗边侧光"),
    "gaming_desk":   ("电竞桌面", "休闲", "暗色桌面，冷调氛围灯，键盘鼠标虚焦"),
    "picnic_grass":  ("野餐草地", "休闲", "草地格纹布，暖阳逆光，柠檬与薄荷"),
    "sofa_living":   ("客厅沙发", "休闲", "布艺沙发与木几，暖黄落地灯"),
    "car_holder":    ("车载杯架", "出行", "车内中央扶手杯架，透过挡风玻璃的日光"),
    "gym_bench":     ("健身房", "出行", "健身房长凳与毛巾，冷调侧光"),
    "camp_outdoor":  ("露营天幕", "出行", "露营天幕下的折叠桌，黄昏暖光"),
    "festival_gift": ("节日礼盒", "节庆", "红金礼盒与灯笼虚影，暖调"),
    "studio_color":  ("纯色棚拍", "极简", "品牌撞色渐变背景，硬光，产品悬空带投影"),
}


def pick(n=3, seed=None, avoid=None):
    avoid = set(avoid or [])
    rng = random.Random(seed)
    pool = [(k, v) for k, v in SCENES.items() if k not in avoid]
    rng.shuffle(pool)
    picked, used_cat = [], set()
    for sid, meta in pool:
        if meta[1] in used_cat:
            continue
        picked.append((sid, meta))
        used_cat.add(meta[1])
        if len(picked) >= n:
            break
    return picked


def main():
    ap = argparse.ArgumentParser(description="抽场景组合，保证同类不重复")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--seed", type=int, default=None, help="默认取当天日期，便于复现")
    ap.add_argument("--avoid", default="", help="要避开的场景 id，逗号分隔")
    ap.add_argument("--out", default=None, help="写入 json，便于任务卡引用")
    a = ap.parse_args()

    import datetime
    seed = a.seed if a.seed is not None else int(datetime.date.today().strftime("%Y%m%d"))
    picked = pick(a.n, seed, [x for x in a.avoid.split(",") if x])

    print("seed=%d，抽 %d 个场景（同类不重复）：" % (seed, len(picked)))
    for sid, (name, cat, desc) in picked:
        print("  %-14s %-4s %s" % (sid, cat, desc))
    print("\n把上面的场景 id 写进任务卡，并要求本批相邻商品的场景不重复。")

    if a.out:
        json.dump([{"id": s, "name": m[0], "category": m[1], "desc": m[2]}
                   for s, m in picked],
                  open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("->", a.out)


if __name__ == "__main__":
    main()
