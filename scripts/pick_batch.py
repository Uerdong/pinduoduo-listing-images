#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户未圈定商品范围时，按固定种子随机取样一批商品。

用法：
    python pick_batch.py products.json --n 5 --seed 20261106
    python pick_batch.py products.json --n 5 --exclude 天津-可口可乐-200ML-24 --out batch.json

取样策略：先按「容量 × 瓶数」分组，轮转各组各取一个，保证规格有覆盖；
取满后再从剩余池随机补足。固定种子 => 同一 seed 结果可复现。
"""
import argparse
import json
import random
from collections import defaultdict


def pick(rows, n=5, seed=20261106, exclude=None, min_count=6, allow_unconfirmed=False,
         counts=None, allow_irregular=False):
    exclude = set(exclude or [])
    pool = [r for r in rows
            if r.get("sku_id") not in exclude and int(r.get("count") or 0) >= min_count]
    if counts:
        pool = [r for r in pool if int(r.get("count") or 0) in counts]
    elif not allow_irregular:
        # 常规箱规 = 6 的倍数（6/12/18/24…）。1/3/5/8/15/17 这类非常规数量
        # 除非用户点名，否则不进取样池
        pool = [r for r in pool if int(r.get("count") or 0) % 6 == 0]
    if not allow_unconfirmed:
        # 品牌待确认的商品出不了标题、也填不了品牌属性，不进默认取样池
        pool = [r for r in pool if r.get("brand")]
    if not pool:
        raise SystemExit("排除后没有可选商品")

    groups = defaultdict(list)
    for r in pool:
        groups[(r.get("capacity"), r.get("count"))].append(r)

    rng = random.Random(seed)
    keys = sorted(groups.keys(), key=lambda k: (str(k[0]), str(k[1])))
    for k in keys:
        rng.shuffle(groups[k])
    rng.shuffle(keys)

    picked, i = [], 0
    while len(picked) < n and i < len(keys) * 3:
        k = keys[i % len(keys)]
        if groups[k]:
            picked.append(groups[k].pop())
        i += 1
    if len(picked) < n:
        rest = [r for k in keys for r in groups[k]]
        rng.shuffle(rest)
        picked.extend(rest[: n - len(picked)])
    return picked[:n]


def main():
    ap = argparse.ArgumentParser(description="按固定种子随机取样商品（用户未圈定范围时使用）")
    ap.add_argument("products", help="parse_ledger.py 产出的 products.json")
    ap.add_argument("--n", type=int, default=5, help="取几个，默认 5")
    ap.add_argument("--seed", type=int, default=20261106, help="随机种子，默认 20261106")
    ap.add_argument("--exclude", nargs="*", default=[], help="要排除的 sku_id，可多个")
    ap.add_argument("--allow-unconfirmed", action="store_true", help="允许选入品牌待确认的商品")
    ap.add_argument("--allow-irregular", action="store_true", help="允许非常规箱规（非 6 的倍数，如 15/17）")
    ap.add_argument("--counts", default="", help="指定允许的瓶数，逗号分隔，如 6,12,24")
    ap.add_argument("--min-count", type=int, default=6, help="最小瓶数，默认 6（单罐/单瓶不适合整箱上架）")
    ap.add_argument("--out", default=None, help="结果写入 json，便于批量脚本读取")
    a = ap.parse_args()

    rows = json.load(open(a.products, encoding="utf-8"))
    counts = set(int(x) for x in a.counts.split(",") if x.strip()) if a.counts else None
    picked = pick(rows, a.n, a.seed, a.exclude, a.min_count, a.allow_unconfirmed,
                  counts, a.allow_irregular)

    print("未圈定范围，按 seed=%d 随机取样 %d 款：" % (a.seed, len(picked)))
    for r in picked:
        print("  %-28s %-8s %s×%s  cost=%s  price=%s  %s"
              % (r["sku_id"], r.get("warehouse", ""), r.get("capacity", ""),
                 r.get("count", ""), r.get("cost"), r.get("price"), r.get("unit", "")))

    if a.out:
        json.dump(picked, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("->", a.out)
    print("\n提醒：这是随机取样，不是用户圈定的范围。交付时须在商品资料与回执里标明。")


if __name__ == "__main__":
    main()
