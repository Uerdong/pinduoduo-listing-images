# -*- coding: utf-8 -*-
"""把商品清单按「快递规则指纹」分组，输出可复用的运费模板规划表。

用法：python plan_shipping.py products.json [--out shipping_templates.md]
"""
import argparse
import json
import os
from collections import OrderedDict


DEMOTE = []  # 平台加不了价、按业务口径降级为禁发的省份


# 拼多多「指定区域加收运费」下拉只开放这些省份，其余省份即使货盘表写了加价也做不到
PLATFORM_SUR_OK = {"香港", "澳门", "台湾", "新疆", "西藏", "青海", "宁夏", "内蒙古", "甘肃"}
DROPPED = set()          # 平台不可加价但保留为包邮的省份
DROPPED_FORBID = set()   # 平台不可加价且未要求包邮，降级为禁发的省份
DROP_SUR = set()         # 来自 --drop-surcharge


def sig(r):
    s = r["shipping"]
    forbid = list(s["forbidden"])
    sur_items = []
    for x in s["surcharge"]:
        keep = []
        for p in x["provinces"]:
            if p in DEMOTE:
                # --demote：平台不可加价，统一降级为禁发
                if p not in forbid:
                    forbid.append(p)
                continue
            if p in DROP_SUR:
                # --drop-surcharge：用户明确要求保留渠道，降级为包邮
                DROPPED.add(p)
                continue
            if p in PLATFORM_SUR_OK:
                keep.append(p)
            else:
                # 平台不开放加价、用户也没说包邮 → 保守处理为禁发，避免倒贴运费
                DROPPED_FORBID.add(p)
                if p not in forbid:
                    forbid.append(p)
        if keep:
            sur_items.append((tuple(keep), x["fee"]))
    sur = tuple(sur_items)
    cond = tuple((tuple(c["provinces"]), c["pct"], c["fee"]) for c in s["conditional"])
    return (tuple(forbid), sur, cond)


def label(no, key):
    forb, sur, cond = key
    head = "T%d 禁发%d地" % (no, len(forb))
    return head


def build(rows):
    groups = OrderedDict()
    for r in rows:
        groups.setdefault(sig(r), []).append(r)
    ordered = sorted(groups.items(), key=lambda kv: -len(kv[1]))

    lines = ["# 运费模板规划（按规则组复用）", ""]
    lines.append("商品总数 %d，规则组 %d 个。同一组的商品共用同一个模板，模板数量 = 规则组数量，不随商品数增长。"
                 % (len(rows), len(ordered)))
    lines.append("")
    lines.append("| 模板 | 覆盖商品数 | 禁发地区 | 加价地区与金额 | 占比条件加价 |")
    lines.append("|---|---|---|---|---|")
    detail = []
    for i, (key, items) in enumerate(ordered, 1):
        forb, sur, cond = key
        sur_txt = "；".join("%s +%s元" % ("/".join(p), f) for p, f in sur) or "无"
        cond_txt = "；".join("%s 超%d%% +%s元" % ("/".join(p), pct, f) for p, pct, f in cond) or "无"
        name = label(i, key)
        lines.append("| %s | %d | %s | %s | %s |" % (name, len(items), "/".join(forb), sur_txt, cond_txt))
        detail.append({
            "template": name,
            "count": len(items),
            "forbidden": list(forb),
            "surcharge": [{"provinces": list(p), "fee": f} for p, f in sur],
            "conditional": [{"provinces": list(p), "pct": pct, "fee": f} for p, pct, f in cond],
            "examples": [x["sku_id"] for x in items[:3]],
        })
    lines += ["", "## 落模板时的处理规则", "",
              "1. 禁发地区直接写入「不配送区域」。",
              "2. 加价地区先判断平台是否开放：拼多多「指定区域加收运费」只开放偏远省份，"
              "北京、上海这类不在可选范围的，需业务拍板改为禁发或包邮承担，不能硬写。",
              "3. 「订单占比超 X% 才加价」是经营口径，不写进模板，只写详情页。",
              "4. 模板命名固定为「T序号-禁发摘要」，便于批量商品直接引用。", ""]
    return "\n".join(lines), detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("products")
    ap.add_argument("--out", default=r"D:\pinduoduo\data\shipping_templates.md")
    ap.add_argument("--demote", default="", help="平台不可加价、降级为禁发的省份，逗号分隔")
    ap.add_argument("--drop-surcharge", default="", help="平台不可加价但保留渠道、降级为包邮的省份，逗号分隔")
    a = ap.parse_args()
    global DEMOTE, DROP_SUR
    DEMOTE = [x for x in a.demote.split(",") if x]
    DROP_SUR = set(x.strip() for x in a.drop_surcharge.split(",") if x.strip())
    rows = json.load(open(a.products, encoding="utf-8"))
    md, detail = build(rows)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(md)
    json.dump(detail, open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(md)
    print("-> %s" % a.out)


if __name__ == "__main__":
    main()
