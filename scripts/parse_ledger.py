# -*- coding: utf-8 -*-
"""货盘表解析：把「一件代发价」工作表按口味拆成单品，输出 JSON + CSV。

用法：
    python parse_ledger.py <xlsx> [--out-dir DIR] [--markup 1.05] [--with-mixed]
"""
import argparse
import csv
import json
import os
import re

import openpyxl

SHEET = "一件代发价"
HEADER_ROW = 3

# ---------------- 品牌映射 ----------------
# 货盘表 A 列是「商品名」，不等于平台品牌。平台品牌要按下面的规则拆。
# 用户 2026-11-06 明确的口径：
#   百事可乐含糖 / 百事可乐无糖 / 七喜              -> 百事可乐
#   康师傅冰糖雪梨 / 蜂蜜柚子 / 每日C橙 / 水晶葡萄
#   / 水蜜桃 / 热带冰红茶 / 茉莉蜜茶 / 低糖冰红茶
#   / 无糖冰红茶                                    -> 康师傅
#   怡泉苏打水                                      -> 怡泉+C
# 用户 2026-11-06 补充：A 列前几个字符就是品牌；无前缀的按下表显式指定。
# 判定优先级：显式映射 > 品牌前缀 > 同款推断 > 待确认
BRAND_MAP = {
    # —— 用户明确指定（名称里不含品牌前缀，必须写死）——
    "百事可乐含糖": "百事可乐",
    "百事可乐无糖": "百事可乐",
    "七喜": "百事可乐",
    "蜂蜜柚子": "康师傅",
    "每日C橙": "康师傅",
    "水晶葡萄": "康师傅",
    "水蜜桃": "康师傅",
    "热带冰红茶": "康师傅",
    "茉莉蜜茶": "康师傅",
    "低糖冰红茶": "康师傅",
    "无糖冰红茶": "康师傅",
    "怡泉苏打水": "怡泉+C",
    "绿葡萄": "美汁源",
    "红葡萄": "美汁源",
    # —— 名称本身以品牌开头，可自证（同时作为前缀规则的兜底）——
    "可口可乐": "可口可乐",
    "无糖可口可乐": "可口可乐",
    "雪碧": "雪碧",
    "无糖雪碧": "雪碧",
    "芬达": "芬达",
    "无糖芬达": "芬达",
    "康师傅冰红茶": "康师傅",
    "康师傅冰糖雪梨": "康师傅",
    "怡泉+C": "怡泉+C",
    "美年达橙": "美年达",
    "美汁源果粒橙": "美汁源",
}

# 品牌前缀：A 列以这些字符开头即可判定品牌（长词优先）
BRAND_TOKENS = ["百事可乐", "可口可乐", "康师傅", "美汁源", "美年达", "怡泉", "雪碧", "芬达", "七喜"]
BRAND_TOKENS.sort(key=len, reverse=True)

# 前缀归一：货盘表写「怡泉」，平台品牌是「怡泉+C」
BRAND_ALIAS = {"怡泉": "怡泉+C"}

# 容量 → 单位（硬映射，覆盖原先「≤330 记罐」的粗推断）
CAP_UNIT = {
    "200ML": "罐",
    "330ML": "罐",
    "300ML": "瓶",   # 百事 / 美年达 / 无糖可乐 300ml 均为 PET 瓶
    "450ML": "瓶",
    "500ML": "瓶",
    "888ML": "瓶",
    "1.25L": "瓶",
}

# 包装形态覆盖：拿到实拍后以实物为准，与容量映射冲突时以此表为准
PACKAGE_OVERRIDE = {
    "美年达-300ML": "瓶",   # 实拍为 PET 瓶，非易拉罐
}

# 同款推断：A 列同时存在「康师傅冰糖雪梨」与「冰糖雪梨」，判断为同一商品省略了前缀
DUP_INFER = {"冰糖雪梨": "康师傅"}


def resolve_brand(name, row_leader=None):
    """返回 (brand, source)。source: 规则 / 名称 / 前缀 / 同款推断 / 行内继承 / 待确认

    row_leader 是同一行 A 列的首个商品名。多口味行往往是同一品牌的系列
    （如「康师傅冰红茶/绿茶/茉莉蜜茶/…」），行首词可推出无前缀项的品牌。
    """
    if name in BRAND_MAP:
        src = "规则" if name not in ("可口可乐", "无糖可口可乐", "雪碧", "无糖雪碧",
                                     "芬达", "无糖芬达", "康师傅冰红茶", "康师傅冰糖雪梨",
                                     "怡泉+C", "美年达橙", "美汁源果粒橙") else "名称"
        return BRAND_MAP[name], src
    for t in BRAND_TOKENS:
        if name.startswith(t):
            return BRAND_ALIAS.get(t, t), "前缀"
    if name in DUP_INFER:
        return DUP_INFER[name], "同款推断"
    if row_leader and row_leader != name:
        lb, _ = resolve_brand(row_leader)
        if lb:
            return lb, "行内继承"
    return None, "待确认"

# 省份词典（长词优先，避免「内蒙」被「内蒙古」截断）
PROVINCES = [
    "黑龙江", "内蒙古", "内蒙", "新疆", "西藏", "青海", "海南", "北京", "上海",
    "天津", "重庆", "河北", "山西", "辽宁", "吉林", "江苏", "浙江", "安徽",
    "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "广西", "四川",
    "贵州", "云南", "陕西", "甘肃", "宁夏", "台湾", "香港", "澳门",
]
PROVINCES.sort(key=len, reverse=True)

UNIT_BY_CAP = {"ML": "罐", "ml": "罐", "L": "箱", "瓶": "瓶"}


def match_provinces(text):
    """从连写文本里切出省份，按出现顺序返回。"""
    out, i = [], 0
    while i < len(text):
        hit = None
        for p in PROVINCES:
            if text.startswith(p, i):
                hit = p
                break
        if hit:
            out.append("内蒙古" if hit == "内蒙" else hit)
            i += len(hit)
        else:
            i += 1
    return out


def parse_shipping(text):
    """解析加价区文本 -> {forbidden, surcharge, conditional, raw}"""
    res = {"forbidden": [], "surcharge": [], "conditional": [], "raw": text or ""}
    if not text:
        return res
    for seg in re.split(r"[，,；;]", text):
        seg = seg.strip()
        if not seg:
            continue
        nums = re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*(?:元|块)", seg)
        pro = match_provinces(seg)
        if "禁发" in seg:
            res["forbidden"].extend(pro)
        elif "占比" in seg or "超" in seg:
            item = {"provinces": pro, "pct": 10, "fee": float(nums[0]) if nums else None}
            m = re.search(r"超\s*([0-9]+)\s*%", seg)
            if m:
                item["pct"] = int(m.group(1))
            res["conditional"].append(item)
        else:
            res["surcharge"].append({"provinces": pro, "fee": float(nums[0]) if nums else None})
    res["forbidden"] = list(dict.fromkeys(res["forbidden"]))

    # 「A占比不超10%」与「超10%加1.5元」常被逗号拆成两段，合并成一条
    merged = []
    for c in res["conditional"]:
        if not c["provinces"] and merged:
            merged[-1]["fee"] = c["fee"]
            continue
        merged.append(c)
    res["conditional"] = merged
    return res


def split_brand(cell):
    """（天津仓）可口可乐/雪碧 -> (仓, [可口可乐, 雪碧])"""
    s = str(cell).strip()
    wh = ""
    m = re.match(r"^[（(](.+?)[)）]\s*(.*)$", s)
    if m:
        wh, s = m.group(1), m.group(2)
    flavors = [x.strip() for x in re.split(r"[/／]", s) if x.strip()]
    return wh, flavors


def parse(path, markup=1.05, with_mixed=False, sheet=None, header_row=None):
    wb = openpyxl.load_workbook(path, data_only=True)
    name = sheet or SHEET
    if name not in wb.sheetnames:
        raise SystemExit(
            "工作表「%s」不存在。该文件可用工作表：%s\n"
            "用 --sheet 指定表名；表头行不是第 %d 行时用 --header-row 指定。"
            % (name, " / ".join(wb.sheetnames), header_row or HEADER_ROW))
    ws = wb[name]
    hrow = header_row or HEADER_ROW
    rows = []
    brand = cap = None
    for r in range(hrow + 1, ws.max_row + 1):
        b = ws.cell(r, 1).value
        c = ws.cell(r, 2).value
        if b:
            brand = str(b).strip()
        if c:
            cap = str(c).strip()
        bottles = ws.cell(r, 3).value
        cost = ws.cell(r, 6).value
        if bottles is None or cost is None or not brand:
            continue
        wh, flavors = split_brand(brand)
        where = ws.cell(r, 7).value or wh
        ship = parse_shipping(ws.cell(r, 8).value)
        n = int(bottles)
        cost = round(float(cost), 2)
        price = round(cost * markup, 2)
        # 单位按容量硬映射（300ML 是 PET 瓶，330ML 才是易拉罐）
        key = str(cap).upper().replace(" ", "")
        if key in CAP_UNIT:
            unit = CAP_UNIT[key]
        elif key.endswith("ML") or key.endswith("L"):
            unit = "瓶"
        else:
            unit = UNIT_BY_CAP.get(str(cap), "箱")
        for fl in flavors:
            bd, bsrc = resolve_brand(fl, flavors[0])
            # 实拍包装优先于容量推断
            u = PACKAGE_OVERRIDE.get("%s-%s" % (bd, str(cap).upper()), unit)
            rows.append({
                "sku_id": "%s-%s-%s-%d" % (where, fl, cap, n),
                "warehouse": where,
                "brand": bd,
                "brand_source": bsrc,
                "flavor": fl,
                "capacity": cap,
                "count": n,
                "unit": u,
                "spec_text": "%s × %d%s/箱" % (cap.replace("ML", "ml"), n, u),
                "cost": cost,
                "price": price,
                "gross": round(price - cost, 2),
                "shipping": ship,
            })
    if with_mixed:
        rows.extend(build_mixed(rows, markup))
    return rows


def build_mixed(rows, markup):
    """可选：按仓+容量+瓶数生成两口味混包，成本每多一个口味 +0.1 操作费。"""
    from itertools import combinations
    groups = {}
    for r in rows:
        groups.setdefault((r["warehouse"], r["capacity"], r["count"]), []).append(r)
    out = []
    for key, items in groups.items():
        for a, b in combinations(items, 2):
            cost = round(a["cost"] + 0.1, 2)
            price = round(cost * markup, 2)
            out.append({
                "sku_id": "%s-%s+%s-%s-%d" % (key[0], a["flavor"], b["flavor"], key[1], key[2]),
                "warehouse": key[0],
                "brand": "%s+%s" % (a["flavor"], b["flavor"]),
                "flavor": "%s+%s" % (a["flavor"], b["flavor"]),
                "capacity": key[1],
                "count": key[2],
                "unit": a["unit"],
                "spec_text": "%s × %d%s/箱" % (key[1], key[2], a["unit"]),
                "cost": cost,
                "price": price,
                "gross": round(price - cost, 2),
                "shipping": a["shipping"],
                "mixed": True,
            })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("--out-dir", default=r"D:\pinduoduo\data")
    ap.add_argument("--markup", type=float, default=1.05)
    ap.add_argument("--with-mixed", action="store_true")
    ap.add_argument("--sheet", default=None, help="工作表名，默认「一件代发价」")
    ap.add_argument("--header-row", type=int, default=None, help="表头所在行，默认 3")
    a = ap.parse_args()

    rows = parse(a.xlsx, a.markup, a.with_mixed, a.sheet, a.header_row)
    os.makedirs(a.out_dir, exist_ok=True)
    jp = os.path.join(a.out_dir, "products.json")
    cp = os.path.join(a.out_dir, "products.csv")
    json.dump(rows, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    with open(cp, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["sku_id", "发货地", "口味", "容量", "瓶数", "单位", "规格",
                    "代发价", "售价", "毛利", "禁发区", "加价区"])
        for r in rows:
            sur = ";".join("%s+%s" % ("/".join(s["provinces"]), s["fee"]) for s in r["shipping"]["surcharge"])
            cond = ";".join("%s超%d%%+%s" % ("/".join(c["provinces"]), c["pct"], c["fee"])
                            for c in r["shipping"]["conditional"])
            w.writerow([r["sku_id"], r["warehouse"], r["flavor"], r["capacity"], r["count"],
                        r["unit"], r["spec_text"], r["cost"], r["price"], r["gross"],
                        "/".join(r["shipping"]["forbidden"]), "|".join(x for x in (sur, cond) if x)])
    print("rows=%d -> %s , %s" % (len(rows), jp, cp))


if __name__ == "__main__":
    main()
