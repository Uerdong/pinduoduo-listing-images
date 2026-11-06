# -*- coding: utf-8 -*-
"""拼多多标题生成与校验。

口径：平台按「字符单位」计数，**中文（全角）算 2，西文/数字算 1**，上限 60。
实测：一条 52 汉字 + 8 西文的标题，计数器显示 112/60，与 2 倍口径吻合。

用法：
    python title_builder.py --brand 可口可乐 --flavor 经典原味 --category 碳酸饮料 \
        --volume 200ml --count 24 --unit 罐
    python title_builder.py --check "某条现成标题"
"""
import argparse
import sys
import re

TARGET = 60  # 平台单位上限

BANNED = [
    "正品保证", "正品保障", "品质保证", "正品", "假一赔十", "原厂", "官方授权",
    "第一", "最有效", "最好", "最强", "顶级", "国家级", "绝无仅有",
    "解油解腻", "健康轻盈", "治疗", "治愈", "功效",
]

POOL = [
    "家庭聚会", "聚餐", "办公室囤货", "开罐即饮", "冰镇更佳", "外出携带",
    "整箱更划算", "小罐装", "易拉罐", "常备饮品", "囤货装", "随身带",
]


def _is_wide(c):
    o = ord(c)
    return (0x4E00 <= o <= 0x9FFF      # CJK 汉字
            or 0x3000 <= o <= 0x303F   # 中文标点
            or 0xFF00 <= o <= 0xFFEF)  # 全角符号


def units(s):
    """平台计数：汉字/中文标点/全角符号计 2，其余（含 ×、字母、数字）计 1。

    实测：× (U+00D7) 平台按 1 计，所以不能简单用「非 ASCII 就 2」。
    """
    return sum(2 if _is_wide(c) else 1 for c in s)


def check(title, target=TARGET):
    problems = []
    u = units(title)
    if u > target:
        problems.append("平台计数 %d，超出上限 %d（中文算 2，西文算 1）" % (u, target))
    if u < target - 6:
        problems.append("平台计数 %d，偏短，建议补到 %d 附近" % (u, target))
    for w in BANNED:
        if w in title:
            problems.append("命中禁用词：%s" % w)
    if " " in title:
        problems.append("含空格")
    if units(title) > target:
        problems.append("超出平台上限，提审可能被拦")
    return (not problems), problems, u


def _fill_exact(remaining, pool):
    """在词池里找能正好填满 remaining 单位的组合，优先靠前的词。"""
    for i, w in enumerate(pool):
        u = units(w)
        if u == remaining:
            return [w]
        if u < remaining:
            sub = _fill_exact(remaining - u, pool[i + 1:])
            if sub is not None:
                return [w] + sub
    return None if remaining else []


def build(brand, flavor, category, volume, count, unit,
          extras=None, target=TARGET, tail=None):
    b, f = brand or "", flavor or ""
    # 品牌与商品名互相包含时不要叠加，否则出现「芬达芬达」「芬达无糖芬达」
    name = f if (b and b in f) else (b + f)
    head = ["%s%s" % (name, category), "%s×%d%s" % (volume, count, unit)]
    segs = head + ["整箱装"] + list(extras or [])
    out = ""
    for s in segs:
        if units(out + s) <= target:
            out += s
    rest = target - units(out)
    pool = list(POOL)
    # 「开罐即饮」只适用于罐装，瓶装要改成「开瓶即饮」
    if unit and unit != "罐":
        pool = ["开%s即饮" % unit if w == "开罐即饮" else w for w in pool]
        pool = [w for w in pool if w != "易拉罐"]   # 瓶装不能写易拉罐
    # 大规格不能写「小罐装」：500ml/888ml 这类会被判文案与规格不符
    digits = "".join(ch for ch in str(volume) if ch.isdigit() or ch == ".")
    ml = float(digits) if digits else 0.0
    if ml > 250:
        pool = [w for w in pool if w != "小罐装"]
    if tail:
        pool = [tail] + pool
    # 词池里都是偶数单位，若剩余为奇数则最多填到 target-1，属正常
    picked = []
    for w in pool:
        # 跳过与已选词重复的（如先选「囤货」又选「囤货装」）
        if any(w[:2] == p[:2] or w in p or p in w for p in picked):
            continue
        if units(out + w) <= target:
            out += w
            picked.append(w)
    # 兜底去重：把「囤货囤货装」这类相邻重复段收成一段
    for n in (3, 2):
        out = re.sub(r"(.{%d})\1" % n, r"\1", out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand")
    ap.add_argument("--flavor", default="")
    ap.add_argument("--category", default="")
    ap.add_argument("--volume", default="200ml")
    ap.add_argument("--count", type=int, default=24)
    ap.add_argument("--unit", default="罐")
    ap.add_argument("--extras", default="")
    ap.add_argument("--tail", default="")
    ap.add_argument("--check", default="")
    a = ap.parse_args()

    # 体积必须带单位。只给数字会生成「200×24罐」这种缺单位的标题。
    if a.volume and a.volume.strip().isdigit():
        a.volume = a.volume.strip() + "ml"
        print("WARN: --volume 只给了数字，已按 ml 补单位；非液体商品请显式写 200g / 1.25L 这类带单位的值",
              file=sys.stderr)

    if a.check:
        ok, probs, u = check(a.check)
        print(("OK" if ok else "FAIL"), "| 平台计数=%d | 字符数=%d" % (u, len(a.check)))
        for p in probs:
            print(" -", p)
        return

    extras = [x for x in a.extras.split(",") if x]
    t = build(a.brand or "", a.flavor, a.category, a.volume, a.count, a.unit,
              extras=extras, tail=a.tail)
    ok, probs, u = check(t)
    print(t)
    print("平台计数=%d  字符数=%d  %s" % (u, len(t), "OK" if ok else "FAIL"))
    for p in probs:
        print(" -", p)


if __name__ == "__main__":
    main()
