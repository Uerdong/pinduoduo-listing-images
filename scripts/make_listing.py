# -*- coding: utf-8 -*-
"""参数化拼多多套图生成器：读取 JSON 配置，输出 10 张主图 + 6 张详情图 + 详情长图。

用法：python make_listing.py config.json
"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_R = r"C:\Windows\Fonts\msyh.ttc"
WHITE = (255, 255, 255)
INK = (38, 38, 38)
GRAY = (108, 108, 108)
LGRAY = (244, 245, 247)


def F(size, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


def rr(d, box, r, **kw):
    d.rounded_rectangle(box, radius=r, **kw)


def dot(d, x, y, r, fill):
    d.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def fit(img, w):
    h = int(img.height * w / img.width)
    return img.resize((w, h), Image.LANCZOS)


def paste_round(c, im, box, radius):
    x0, y0, x1, y1 = box
    im = im.resize((x1 - x0, y1 - y0), Image.LANCZOS).convert("RGB")
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width, im.height), radius=radius, fill=255)
    c.paste(im, (x0, y0), mask)


def grid(n):
    """件数 -> (列, 行)：优先整除，整块宽高比接近 2:1。"""
    best, bd = (n, 1), 1e9
    for cols in range(1, n + 1):
        if n % cols:
            continue
        rows = n // cols
        d = abs(cols / rows - 2.0)
        if d < bd:
            bd, best = d, (cols, rows)
    return best


class Kit:
    def __init__(self, cfg):
        self.c = cfg
        self.out = cfg["out_dir"]
        self.md = os.path.join(self.out, "主图")
        self.ddir = os.path.join(self.out, "详情图")
        os.makedirs(self.md, exist_ok=True)
        os.makedirs(self.ddir, exist_ok=True)
        self.theme = tuple(cfg.get("theme", [226, 20, 40]))
        self.can = Image.open(cfg["can_image"]).convert("RGBA")
        # 源图分辨率：主图母版 2048，产品高度通常 700~1200px，放大超过 1.5 倍必然发软
        self.src_h = self.can.height
        self.max_upscale = round(1200.0 / max(1, self.src_h), 2)
        self.spec = cfg.get("spec_text") or "%s × %d%s/箱" % (cfg["volume"], cfg["count"], cfg["unit"])
        self.brand_cn = cfg["brand_cn"]
        self.flavor = cfg["flavor"]

    def can_w(self, h):
        return self.can.resize((int(self.can.width * h / self.can.height), h), Image.LANCZOS)

    def W(self):
        return self.theme

    # ---------------- 主图 ----------------
    def md01(self):
        W = H = 2048
        c = Image.new("RGB", (W, H), WHITE)
        d = ImageDraw.Draw(c)
        d.text((150, 120), self.c.get("brand_en", ""), font=F(126), fill=self.W())
        d.text((154, 286), "%s %s%s" % (self.brand_cn, self.flavor, self.c.get("category", "")),
               font=F(56, False), fill=GRAY)
        rr(d, (1350, 140, 1898, 252), 56, fill=WHITE, outline=self.W(), width=5)
        d.text((1350 + (548 - d.textlength(self.spec, font=F(48))) / 2, 196),
               self.spec, font=F(48), fill=self.W(), anchor="lm")
        im = self.can_w(1000)
        cx = (W - im.width) // 2
        for dx in (-int(im.width * 0.88), int(im.width * 0.88)):
            c.paste(im, (cx + dx, 1620 - im.height), im)
        c.paste(im, (cx, 1620 - im.height), im)
        rr(d, (146, 1700, 1902, 1950), 34, fill=self.W())
        d.text((206, 1800), "%s × %d%s 整箱装" % (self.c["volume"], self.c["count"], self.c["unit"]),
               font=F(90), fill=WHITE, anchor="lm")
        c.save(os.path.join(self.md, "MD-01.jpg"), quality=95)

    def md02(self):
        W = H = 2048
        c = Image.new("RGB", (W, H), WHITE)
        d = ImageDraw.Draw(c)
        n = self.c["count"]
        d.text((150, 110), "一整箱 %d %s" % (n, self.c["unit"]), font=F(104), fill=self.W())
        cols, rows = grid(n)
        d.text((154, 262), "%d × %d 排布，一箱 %d %s" % (cols, rows, n, self.c["unit"]),
               font=F(52, False), fill=GRAY)
        top = 380
        avail_w, avail_h = 1790, 1560
        hh = min((avail_h - (rows - 1) * 6) // rows, int(avail_w / cols / (self.can.width / self.can.height)))
        im = self.can_w(hh)
        stepx = im.width + 4
        x0 = (W - stepx * cols) // 2
        for r in range(rows):
            for i in range(cols):
                if r * cols + i >= n:
                    break
                c.paste(im, (x0 + i * stepx, top + r * (hh + 6)), im)
        rr(d, (1290, 118, 1898, 268), 60, fill=self.W())
        d.text((1290 + (608 - d.textlength("%d %s/箱" % (n, self.c["unit"]), font=F(56))) / 2, 194),
               "%d %s/箱" % (n, self.c["unit"]), font=F(56), fill=WHITE, anchor="lm")
        c.save(os.path.join(self.md, "MD-02.jpg"), quality=95)

    def md03(self):
        W = H = 2048
        c = Image.new("RGB", (W, H), WHITE)
        d = ImageDraw.Draw(c)
        d.text((150, 110), self.c.get("slogan", "%s 经典好味" % self.flavor), font=F(100), fill=self.W())
        d.text((154, 262), "%s 小%s装，一次一%s刚刚好" % (self.c["volume"], self.c["unit"], self.c["unit"]),
               font=F(54, False), fill=GRAY)
        im = self.can_w(1100)
        c.paste(im, (130, 1780 - im.height), im)
        items = self.c.get("points") or [
            (self.flavor, "熟悉的口感，气泡充足"),
            ("畅爽带劲", "冰镇后开%s，口感更畅快" % self.c["unit"]),
            ("%s 小%s" % (self.c["volume"], self.c["unit"]), "一人一%s，不用担心喝不完" % self.c["unit"]),
            ("整箱 %d %s" % (self.c["count"], self.c["unit"]), "家庭常备，囤货更省心"),
        ]
        y = 430
        for k, v in items[:4]:
            rr(d, (860, y, 1920, y + 250), 24, fill=LGRAY)
            dot(d, 912, y + 84, 13, self.W())
            d.text((942, y + 84), k, font=F(52), fill=INK, anchor="lm")
            d.text((912, y + 176), v, font=F(38, False), fill=GRAY, anchor="lm")
            y += 278
        c.save(os.path.join(self.md, "MD-03.jpg"), quality=95)

    def _scene(self, name, bg, can_h, xs, base, title, sub, shadow=True):
        W = H = 2048
        c = Image.open(bg).convert("RGB").resize((W, H), Image.LANCZOS)
        d = ImageDraw.Draw(c)
        im = self.can_w(can_h)
        for x in xs:
            if shadow:
                lay = Image.new("RGBA", c.size, (0, 0, 0, 0))
                ImageDraw.Draw(lay).ellipse((x + im.width // 2 - im.width // 2, base - 20,
                                             x + im.width // 2 + im.width // 2, base + 26),
                                            fill=(20, 20, 25, 70))
                lay = lay.filter(ImageFilter.GaussianBlur(18))
                c.paste(lay, (0, 0), lay)
            c.paste(im, (x, base - im.height), im)
        rr(d, (150, 60, 1740, 300), 26, fill=WHITE)
        d.text((200, 112), title, font=F(74), fill=self.W())
        d.text((204, 214), sub, font=F(42, False), fill=GRAY)
        rr(d, (150, 1700, 1898, 1950), 26, fill=WHITE)
        d.text((200, 1786), self.spec, font=F(52), fill=self.W(), anchor="lm")
        d.text((200, 1874), "%s  |  整箱 %d %s" % (self.flavor, self.c["count"], self.c["unit"]),
               font=F(40, False), fill=GRAY, anchor="lm")
        c.save(os.path.join(self.md, name), quality=95)

    def md04_md06(self):
        sc = self.c["scenes"]
        im = self.can_w(680)
        step = int(im.width * 0.78)
        self._scene("MD-04.jpg", sc["ice"], 680, [1150, 1150 + step, 1150 + step * 2], 1640,
                    "冰镇后开%s 更畅快" % self.c["unit"],
                    "%s 一人一%s，冰过更好喝" % (self.c["volume"], self.c["unit"]))
        im2 = self.can_w(460)
        st2 = int(im2.width * 0.86)
        W = 2048
        x0 = (W - (st2 * 4 + int(im2.width * 0.14))) // 2
        self._scene("MD-05.jpg", sc["fridge"], 460, [x0 + i * st2 for i in range(4)], 1000,
                    "冷藏存放 随时开%s" % self.c["unit"], "整箱放得下，想喝随手拿", shadow=False)
        self._scene("MD-06.jpg", sc["desk"], 620, [1170], 1650,
                    "办公下午茶", "%s 小%s，桌上不占地方" % (self.c["volume"], self.c["unit"]))

    def md07_md08(self):
        """场景图一律用「空场景 + 本品合成」，禁止直接贴其它品牌的实拍。"""
        sc = self.c["scenes"]
        for k in ("party", "food"):
            if k not in sc:
                raise KeyError("scenes.%s 缺失：场景图必须用无品牌空场景，不能贴其它品牌实拍" % k)
        W = H = 2048

        im = self.can_w(620)
        step = int(im.width * 0.8)
        self._scene("MD-07.jpg", sc["party"], 620,
                    [1030, 1030 + step, 1030 + 2 * step], 1690,
                    "开%s畅饮 聚会分享" % self.c["unit"],
                    "冰镇后开%s，气泡更足" % self.c["unit"])

        c = Image.open(sc["food"]).convert("RGB").resize((W, H), Image.LANCZOS)
        d = ImageDraw.Draw(c)
        rr(d, (110, 70, 1830, 330), 26, fill=WHITE)
        d.text((160, 128), "佐餐好搭档", font=F(86), fill=self.W())
        d.text((164, 236), "家常菜、烧烤、外卖都能搭", font=F(44, False), fill=GRAY)
        can = self.can_w(700)
        x = 1290
        lay = Image.new("RGBA", c.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse((x - 50, 1380, x + can.width + 50, 1440), fill=(20, 20, 25, 70))
        lay = lay.filter(ImageFilter.GaussianBlur(18))
        c.paste(lay, (0, 0), lay)
        c.paste(can, (x, 1400 - can.height), can)
        rr(d, (110, 1420, 1830, 1930), 26, fill=WHITE)
        rows = [("一口菜一口%s" % self.c["unit"], "清爽畅快，开%s即饮" % self.c["unit"]),
                ("小%s不占桌" % self.c["unit"], "%s 一人一%s，喝完不剩" % (self.c["volume"], self.c["unit"])),
                ("整箱更划算", "%d %s一箱，家里常备" % (self.c["count"], self.c["unit"]))]
        y = 1462
        for k, v in rows:
            dot(d, 158, y + 26, 10, self.W())
            d.text((186, y + 26), k, font=F(44), fill=INK, anchor="lm")
            d.text((186 + d.textlength(k, font=F(44)) + 36, y + 30), v,
                   font=F(36, False), fill=GRAY, anchor="lm")
            y += 80
        d.text((158, 1830), self.spec, font=F(62), fill=self.W(), anchor="lm")
        c.save(os.path.join(self.md, "MD-08.jpg"), quality=95)

    def md09_md10(self):
        W = H = 2048
        c = Image.new("RGB", (W, H), WHITE)
        d = ImageDraw.Draw(c)
        d.text((150, 110), "规格说明", font=F(104), fill=self.W())
        d.text((154, 262), "单%s %s，一箱 %d %s" % (self.c["unit"], self.c["volume"], self.c["count"], self.c["unit"]),
               font=F(52, False), fill=GRAY)
        im = self.can_w(760)
        c.paste(im, (300, 1240 - im.height), im)
        d.text((980, 560), "1 %s = %s" % (self.c["unit"], self.c["volume"]), font=F(74), fill=INK)
        d.text((980, 686), "× %d %s = 1 箱" % (self.c["count"], self.c["unit"]), font=F(74), fill=self.W())
        d.text((980, 812), "整箱发货，箱规 %s" % self.spec, font=F(38, False), fill=GRAY)
        rows = [("规格", self.spec), ("口味", "%s（%s）" % (self.flavor, self.brand_cn)), ("包装", "整箱发货")]
        y = 930
        for k, v in rows:
            rr(d, (960, y, 1898, y + 130), 20, fill=LGRAY)
            d.text((1000, y + 42), k, font=F(32), fill=GRAY, anchor="lm")
            d.text((1000, y + 92), v, font=F(38), fill=INK, anchor="lm")
            y += 150
        rr(d, (150, 1600, 1898, 1930), 30, fill=self.W())
        d.text((206, 1700), self.spec, font=F(80), fill=WHITE, anchor="lm")
        d.text((206, 1834), "%s  |  整箱发货" % self.flavor, font=F(44), fill=(255, 228, 230), anchor="lm")
        c.save(os.path.join(self.md, "MD-09.jpg"), quality=95)

        c = Image.new("RGB", (W, H), self.W())
        d = ImageDraw.Draw(c)
        im = self.can_w(960)
        c.paste(im, ((W - im.width) // 2, 1500 - im.height), im)
        d.text((150, 150), self.c.get("brand_en", self.brand_cn), font=F(130), fill=WHITE)
        d.text((154, 330), "%s · %s × %d%s" % (self.flavor, self.c["volume"], self.c["count"], self.c["unit"]),
               font=F(58), fill=(255, 232, 234))
        d.text((154, 1560), self.c.get("taste_line1", "气泡充足，口感畅爽"), font=F(54), fill=WHITE)
        d.text((154, 1655), self.c.get("taste_line2", "冰镇后饮用风味更佳"), font=F(54), fill=WHITE)
        d.text((154, 1800), self.spec, font=F(46), fill=(255, 232, 234))
        c.save(os.path.join(self.md, "MD-10.jpg"), quality=95)

    # ---------------- 详情图 ----------------
    def dt(self):
        W, H = 750, 1000

        def base():
            c = Image.new("RGB", (W, H), WHITE)
            return c, ImageDraw.Draw(c)

        def head(d, t, s):
            d.rectangle((0, 0, W, 8), fill=self.W())
            d.text((56, 56), t, font=F(52), fill=self.W())
            d.text((58, 128), s, font=F(24, False), fill=GRAY)

        c, d = base()
        head(d, "%s %s" % (self.brand_cn, self.flavor), "%s × %d%s 整箱" % (self.c["volume"], self.c["count"], self.c["unit"]))
        im = self.can_w(430)
        c.paste(im, ((W - im.width) // 2, 640 - im.height), im)
        rows = [("商品名称", "%s %s" % (self.brand_cn, self.c.get("category", ""))),
                ("单%s容量" % self.c["unit"], self.c["volume"]),
                ("装箱规格", "%d %s / 箱" % (self.c["count"], self.c["unit"])),
                ("口味", self.flavor),
                ("发货方式", "整箱发货")]
        y = 672
        for k, v in rows:
            rr(d, (56, y, 694, y + 56), 12, fill=LGRAY)
            d.text((78, y + 28), k, font=F(22), fill=self.W(), anchor="lm")
            d.text((186, y + 28), v, font=F(22, False), fill=INK, anchor="lm")
            y += 62
        c.save(os.path.join(self.ddir, "DT-01.jpg"), quality=95)

        c, d = base()
        head(d, "产品卖点", "这些是它值得囤的理由")
        items = self.c.get("points") or [
            (self.flavor, "熟悉的口感，气泡充足"),
            ("畅爽带劲", "冰镇后开%s，口感更畅快" % self.c["unit"]),
            ("%s 小%s" % (self.c["volume"], self.c["unit"]), "一人一%s，不用担心喝不完" % self.c["unit"]),
            ("整箱 %d %s" % (self.c["count"], self.c["unit"]), "家庭常备，囤货更省心"),
        ]
        y = 228
        for k, v in items[:4]:
            rr(d, (56, y, 694, y + 164), 18, fill=WHITE, outline=(232, 232, 234), width=2)
            rr(d, (56, y, 66, y + 164), 5, fill=self.W())
            dot(d, 106, y + 50, 11, self.W())
            d.text((134, y + 50), k, font=F(31), fill=INK, anchor="lm")
            d.text((88, y + 112), v, font=F(22, False), fill=GRAY)
            y += 184
        c.save(os.path.join(self.ddir, "DT-02.jpg"), quality=95)

        c, d = base()
        head(d, "产品参数", "按实际规格填写")
        rows = [("商品名称", "%s %s" % (self.brand_cn, self.c.get("category", ""))),
                ("口味", self.flavor),
                ("单%s容量" % self.c["unit"], self.c["volume"]),
                ("装箱数", "%d %s / 箱" % (self.c["count"], self.c["unit"])),
                ("包装方式", "箱装"),
                ("发货方式", "整箱发货")]
        y = 240
        for i, (k, v) in enumerate(rows):
            fill = LGRAY if i % 2 == 0 else WHITE
            rr(d, (56, y, 694, y + 96), 12, fill=fill)
            d.text((82, y + 34), k, font=F(24), fill=GRAY, anchor="lm")
            d.text((82, y + 70), v, font=F(28), fill=INK, anchor="lm")
            y += 96
        rr(d, (56, 838, 694, 962), 14, fill=LGRAY)
        d.text((82, 872), "说明", font=F(24), fill=self.W(), anchor="lm")
        d.text((82, 916), "以上信息按本商品实际规格填写，图片仅供参考，以实物为准。", font=F(21, False), fill=GRAY, anchor="lm")
        c.save(os.path.join(self.ddir, "DT-03.jpg"), quality=95)

        c, d = base()
        head(d, "饮用场景", "什么时候开都合适")
        # 场景里必须出现产品，纯空场景不算详情图
        panel = Image.open(self.c["scenes"]["food"]).convert("RGB").resize((638, 412), Image.LANCZOS)
        pim = self.can_w(300)
        panel = self._panel_product(panel, pim, 638 - pim.width - 44, 412 - 34)
        paste_round(c, panel, (56, 224, 694, 636), 20)
        rows = [("日常自饮", "%s 一次一%s，不用担心喝不完" % (self.c["volume"], self.c["unit"])),
                ("佐餐搭配", "烧烤、家常菜、外卖都能搭"),
                ("聚会分享", "整箱 %d %s，人多也够分" % (self.c["count"], self.c["unit"]))]
        y = 686
        for k, v in rows:
            dot(d, 74, y + 20, 8, self.W())
            d.text((96, y + 20), k, font=F(26), fill=INK, anchor="lm")
            d.text((96, y + 62), v, font=F(22, False), fill=GRAY, anchor="lm")
            y += 100
        c.save(os.path.join(self.ddir, "DT-04.jpg"), quality=95)

        c, d = base()
        head(d, "发货说明", "整箱发出，收货请检查")
        blocks = [("包装方式", ["整箱规格发货，外箱按商品原包装寄出"]),
                  ("签收提醒", ["收到后请检查外箱是否完好", "如有破损请当场拍照并联系在线客服"]),
                  ("存放建议", ["阴凉干燥处存放，避免暴晒"]),
                  ("售后说明", ["商品问题请在收货后及时联系在线客服处理"])]
        y = 236
        for t, lines in blocks:
            hh = 74 + 44 * len(lines)
            rr(d, (56, y, 694, y + hh), 16, fill=WHITE, outline=(234, 234, 236), width=2)
            rr(d, (56, y, 64, y + hh), 4, fill=self.W())
            d.text((86, y + 34), t, font=F(27), fill=self.W(), anchor="lm")
            yy = y + 78
            for ln in lines:
                d.text((88, yy), ln, font=F(22, False), fill=INK)
                yy += 44
            y += hh + 20
        c.save(os.path.join(self.ddir, "DT-05.jpg"), quality=95)

        c, d = base()
        head(d, "购买须知", "配送与运费规则，下单前请知悉")
        sh = self.c["shipping"]
        # 运费说明必须读本商品配置，不能写死上一款的规则
        sur = sh.get("surcharge") or []
        sur_lines = []
        for s in sur:
            sur_lines.append("%s：每件加收运费 %s 元" % ("、".join(s.get("provinces", [])), s.get("fee", "")))
        for x in (sh.get("conditional") or []):
            sur_lines.append("%s：订单占比超过 %s%% 时加收 %s 元/单"
                             % ("、".join(x.get("provinces", [])), x.get("pct", 10), x.get("fee", "")))
        if not sur_lines:
            sur_lines = ["本商品全区域包邮（禁发区域除外）"]
        sur_lines.append("其余地区按商品页显示运费为准")
        blocks = [("禁发区域", [forbidden_line(sh["forbidden"]), "以上地区暂不支持配送，请勿下单"], self.W()),
                  ("运费说明", sur_lines[:3], (208, 130, 42)),
                  ("发货仓", [self.c.get("warehouse_note", "所有订单统一仓库发出")], (52, 96, 168)),
                  ("售后提醒", ["收到商品如有疑问，请第一时间联系在线客服处理"], (0, 140, 90))]
        y = 226
        for t, lines, col in blocks:
            hh = 74 + 46 * len(lines)
            rr(d, (56, y, 694, y + hh), 16, fill=WHITE, outline=(234, 234, 236), width=2)
            rr(d, (56, y, 64, y + hh), 4, fill=col)
            d.text((86, y + 34), t, font=F(27), fill=col, anchor="lm")
            yy = y + 78
            for ln in lines:
                d.text((88, yy), ln, font=F(22, False), fill=INK)
                yy += 46
            y += hh + 20
        c.save(os.path.join(self.ddir, "DT-06.jpg"), quality=95)

        long = Image.new("RGB", (750, 6000), WHITE)
        for i in range(1, 7):
            long.paste(Image.open(os.path.join(self.ddir, "DT-0%d.jpg" % i)).convert("RGB"), (0, (i - 1) * 1000))
        long.save(os.path.join(self.ddir, "DT-详情长图.jpg"), quality=92)

    def write_spec(self):
        """产出 商品资料.md，字段口径见 SKILL 第六节。缺字段不猜，进「待确认项」。"""
        c = self.c
        ship = c.get("shipping", {}) or {}

        def units(s):
            """平台计数：中文/全角算 2，西文数字算 1，乘号 × 按 1 计。"""
            u = 0
            for ch in s or "":
                if ch == "\u00d7" or ch.isascii():
                    u += 1
                else:
                    u += 2
            return u

        title = c.get("title", "")
        price = c.get("price")
        single = c.get("price_single")
        ref = c.get("price_ref")
        cost = c.get("cost")
        gross = ("%.2f 元" % (price - cost)) if (cost is not None and price is not None) else "—"

        todo = []
        if cost is None:
            todo.append("代发成本未提供，毛利无法核算")
        if not ship.get("forbidden"):
            todo.append("禁发区未配置")
        if c.get("production_date_placeholder"):
            todo.append("生产日期为占位值，提审前必须替换")
        if not c.get("qualification"):
            todo.append("资质（仅销售预包装食品备案凭证）未上传，草稿可存但不可提审")
        if c.get("stock_default"):
            todo.append("库存按默认 %s 预填，用户尚未确认（可调）" % (c.get("stock", 50)))
        if c.get("range_random"):
            todo.append("本批商品范围为随机取样，非用户书面圈定")
        if getattr(self, "src_h", 9999) < 900:
            todo.append("产品图源高仅 %dpx，主图放大约 %.1f 倍会发软；建议换长边 ≥1200px 原图，"
                        "或用同款实拍重新取图" % (self.src_h, self.max_upscale))
        for x in c.get("unconfirmed", []) or []:
            todo.append(str(x))

        L = []
        L.append("# %s %s %s %d%s%s 商品资料" % (c["brand_cn"], c["flavor"], c["volume"],
                                                c["count"], c["unit"], ""))
        L.append("")
        L.append("- 品牌：%s（%s）" % (c["brand_cn"], c.get("brand_en", "")))
        L.append("- 口味：%s" % c["flavor"])
        L.append("- 品类：%s" % c.get("category", ""))
        L.append("- 规格：%s" % self.spec)
        L.append("- SKU：%s / %d%s整箱" % (c["flavor"], c["count"], c["unit"]))
        L.append("")
        L.append("## 标题")
        L.append("```")
        L.append(title or "（未提供）")
        L.append("```")
        if title:
            L.append("平台计数 %d/60，字符数 %d" % (units(title), len(title)))
        L.append("")
        L.append("## 价格")
        L.append("| 项 | 值 |")
        L.append("|---|---|")
        L.append("| 拼单价 | %s |" % ("%.2f" % price if price is not None else "—"))
        L.append("| 单买价 | %s |" % ("%.2f" % single if single is not None else "—"))
        L.append("| 参考价 | %s |" % ("%.2f" % ref if ref is not None else "—"))
        L.append("| 代发成本 | %s |" % ("%.2f" % cost if cost is not None else "—"))
        L.append("| 毛利 | %s |" % gross)
        L.append("| 库存 | %s%s |" % (
            c["stock"] if c.get("stock") is not None else "—",
            "（默认，可调）" if c.get("stock_default") else ""))
        L.append("")
        L.append("## 配送")
        L.append("- 禁发：%s" % ("、".join(ship.get("forbidden", [])) or "（未配置）"))
        if ship.get("surcharge"):
            L.append("- 加价：%s" % "；".join("%s +%s 元" % ("、".join(s.get("provinces", [])), s.get("fee", "")) for s in ship["surcharge"]))
        if ship.get("conditional"):
            L.append("- 占比加价（只写详情页）：%s" % "；".join("%s 超 %s%% +%s 元" % ("、".join(x.get("provinces", [])), x.get("pct", ""), x.get("fee", "")) for x in ship["conditional"]))
        L.append("- 发货仓：%s" % c.get("warehouse_note", "—"))
        L.append("")
        L.append("## 图片清单")
        plan = c.get("plan")
        info = getattr(self, "plan_info", None)
        if plan and info:
            cnt, probs = info
            L.append("- 主图 %d 张（版式族覆盖 %d 个）：" % (len(plan), len(cnt)))
            for i, p in enumerate(plan, 1):
                L.append("  - MD-%02d ｜ %s ｜ 版式 %s%s" % (
                    i, p.get("family", "—"), p.get("layout", "studio_white"),
                    " ｜ 背景：" + os.path.basename(p["bg"]) if p.get("bg") else ""))
            if probs:
                L.append("- **版式合规问题**：%s" % "；".join(probs))
            else:
                L.append("- 版式合规：覆盖 ≥4 族、同族 ≤3 张，符合规范")
        else:
            L.append("- 主图 10 张：MD-01~MD-10，2048×2048（白底首图 / 整箱 / 特写 / 冰镇 / 冷藏 / 办公 / 聚会 / 佐餐 / 规格 / 品牌卡）")
        L.append("- 详情图 6 张：DT-01~DT-06，750×1000（总览 / 卖点 / 参数 / 场景 / 发货 / 购买须知）")
        L.append("- 详情长图：750×6000，**仅本地预览，不上传**")
        L.append("- 参考图：%s" % c.get("ref_image_note", "—"))
        L.append("")
        L.append("## 待确认项")
        if todo:
            for t in todo:
                L.append("- %s" % t)
        else:
            L.append("- 无")
        L.append("")
        with open(os.path.join(self.out, "商品资料.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(L))

    # ================= 版式族引擎（plan 模式） =================
    # 版式族 = 背景世界观 + 光位色温 + 色彩关系 + 构图留白 + 道具材质。
    # 同一套 10 张主图至少覆盖 4 族、同族不超过 3 张，见 SKILL 第四节。
    LAYOUTS = ("studio_white", "fullbleed_left", "fullbleed_top", "minimal_center",
               "matrix", "split_color", "spec_panel", "brand_card",
               "matrix_pyramid", "matrix_film", "matrix_row", "matrix_hero")

    def _th(self, spec):
        return tuple(spec.get("theme") or self.theme)

    def _bg(self, spec):
        """背景：给了图片就用图片；没图用程序绘制，保证离线可跑。"""
        S = 2048
        src = spec.get("bg")
        if src and os.path.exists(src):
            return Image.open(src).convert("RGB").resize((S, S), Image.LANCZOS)
        mode = spec.get("bg_mode") or "solid"
        th = self._th(spec)
        if mode == "grad":
            top = tuple(spec.get("grad_top") or th)
            bot = tuple(spec.get("grad_bottom") or (255, 255, 255))
            c = Image.new("RGB", (S, S))
            d = ImageDraw.Draw(c)
            for y in range(S):
                t = y / (S - 1)
                d.line([(0, y), (S, y)],
                       fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
            return c
        if mode == "ice":
            import random
            random.seed(spec.get("seed", 7))
            c = Image.new("RGB", (S, S), (222, 238, 250))
            d = ImageDraw.Draw(c)
            for _ in range(80):
                x, y = random.randint(-120, S), random.randint(-120, S)
                s = random.randint(70, 240)
                d.rounded_rectangle([x, y, x + s, y + s], radius=s // 6,
                                    fill=(242, 250, 255) if random.random() > .5 else (205, 226, 244))
            return c.filter(ImageFilter.GaussianBlur(3))
        col = spec.get("bg_color")
        if col is None:
            return Image.new("RGB", (S, S), WHITE)
        if isinstance(col, int):
            col = (col, col, col)
        return Image.new("RGB", (S, S), tuple(col))

    def _shadow(self, c, x, y, w):
        """在产品底部画椭圆投影，避免贴图感。"""
        h = max(28, int(w * 0.07))
        lay = Image.new("RGBA", c.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse([x + int(w * 0.10), y - h // 2,
                                     x + int(w * 0.90), y + h // 2], fill=(0, 0, 0, 78))
        c.paste(Image.new("RGB", c.size, (0, 0, 0)), (0, 0), lay.filter(ImageFilter.GaussianBlur(16)))

    def _chip(self, d, x, y, text, th, fs=42):
        f = F(fs)
        h = fs + 46
        w = int(d.textlength(text, font=f)) + 110
        d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=(255, 255, 255))
        dot(d, x + 34, y + h // 2, 11, th)
        d.text((x + 62, y + 20), text, font=f, fill=INK)
        return y + h + 18

    def _strip(self, c, d, main, sub, th, band=300):
        W, H = c.size
        top = H - 70 - band
        d.rounded_rectangle([70, top, W - 70, H - 70], radius=48, fill=th)
        d.text((130, top + 34), main, font=F(76), fill=WHITE)
        if sub:
            d.text((134, top + 126), sub, font=F(44, False), fill=(255, 255, 255))

    def lay_studio_white(self, spec, S=2048):
        th = self._th(spec)
        c = self._bg(spec if spec.get("bg") or spec.get("bg_color") else dict(spec, bg_color=(255, 255, 255)))
        d = ImageDraw.Draw(c)
        d.text((110, 110), self.c.get("brand_en", self.brand_cn), font=F(120), fill=th)
        d.text((114, 250), "%s %s" % (self.brand_cn, self.flavor), font=F(58, False), fill=GRAY)
        n = max(1, min(int(spec.get("qty", 3)), 4))
        im = self.can_w(900)
        gap = int(im.width * 0.04)
        total = im.width * n + gap * (n - 1)
        x = (S - total) // 2
        for i in range(n):
            c.paste(im, (x + i * (im.width + gap), 1600 - im.height), im)
        self._strip(c, d, spec.get("strip") or self.spec,
                    spec.get("strip_sub") or ("%s 整箱装" % self.brand_cn), th)
        return c

    def lay_fullbleed_left(self, spec, S=2048):
        th = self._th(spec)
        c = self._bg(spec)
        d = ImageDraw.Draw(c)
        x = int(S * 0.07)
        d.text((x, int(S * 0.11)), spec.get("head") or "%s 畅爽开%s" % (self.flavor, self.c["unit"]),
               font=F(132), fill=th)
        d.text((x + 6, int(S * 0.11) + 170), spec.get("sub") or self.spec, font=F(56, False), fill=INK)
        y = int(S * 0.11) + 300
        for t in (spec.get("chips") or [self.spec, "%d%s整箱" % (self.c["count"], self.c["unit"]), "开%s即饮" % self.c["unit"]])[:4]:
            y = self._chip(d, x, y, t, th)
        n = max(1, min(int(spec.get("qty", 3)), 3))
        im = self.can_w(int(S * 0.42))
        base = int(S * float(spec.get("anchor", 0.80)))
        gap = int(im.width * 0.16)
        xs = int(S * 0.92) - im.width * n - gap * (n - 1)
        for i in range(n):
            c.paste(im, (xs + i * (im.width + gap), base - im.height), im)
        return c

    def lay_fullbleed_top(self, spec, S=2048):
        th = self._th(spec)
        c = self._bg(spec)
        d = ImageDraw.Draw(c)
        d.text((110, 110), spec.get("head") or ("%s %s" % (self.brand_cn, self.flavor)),
               font=F(126), fill=th)
        d.text((114, 262), spec.get("sub") or self.spec, font=F(54, False), fill=INK)
        base = int(S * float(spec.get("anchor", 0.86)))
        im = self.can_w(int(S * float(spec.get("scale", 0.56))))
        self._shadow(c, (S - im.width) // 2, base, im.width)
        c.paste(im, ((S - im.width) // 2, base - im.height), im)
        return c

    def lay_minimal_center(self, spec, S=2048):
        th = self._th(spec)
        c = self._bg(spec if spec.get("bg") or spec.get("bg_mode") else dict(spec, bg_color=(246, 246, 244)))
        d = ImageDraw.Draw(c)
        line = spec.get("head") or "%s　%s" % (self.flavor, self.spec)
        f = F(44, False)
        w = d.textlength(line, font=f)
        d.text(((S - w) / 2, 150), line, font=f, fill=GRAY)
        im = self.can_w(int(S * 0.62))
        c.paste(im, ((S - im.width) // 2, int(S * 0.52) - im.height // 2), im)
        b = self.brand_cn
        w2 = d.textlength(b, font=F(40, False))
        d.text(((S - w2) / 2, S - 210), b, font=F(40, False), fill=th)
        return c

    def lay_matrix(self, spec, S=2048):
        th = self._th(spec)
        c = self._bg(spec if (spec.get("bg") or spec.get("bg_mode")) else dict(spec, bg_mode="ice"))
        d = ImageDraw.Draw(c)
        d.text((110, 110), spec.get("head") or "一整箱 %d%s" % (self.c["count"], self.c["unit"]), font=F(120), fill=th)
        d.text((114, 252), spec.get("sub") or self.spec, font=F(50, False), fill=INK)
        n = self.c["count"]
        # 件数可能是质数（17/13 等），整除排布会退化成一行，改为近似 2:1 的网格并留空位
        import math
        cols = max(1, min(6, int(math.ceil(math.sqrt(n * 2)))))
        rows = int(math.ceil(n / cols))
        top, bottom, side = 460, 1680, 120
        aw, ah = S - side * 2, bottom - top
        hh = min((ah - (rows - 1) * 8) // rows, int((aw - (cols - 1) * 8) / cols / (self.can.width / self.can.height)))
        im = self.can_w(hh)
        stepx = (aw - im.width * cols) // max(1, (cols - 1)) + im.width if cols > 1 else im.width
        stepy = (ah - im.height * rows) // max(1, (rows - 1)) + im.height if rows > 1 else im.height
        idx = 0
        for r in range(rows):
            for k in range(cols):
                if idx >= n:          # 质数件数会留空位，不能多画
                    break
                c.paste(im, (side + k * stepx, top + r * stepy), im)
                idx += 1
        self._strip(c, d, self.spec, "%d%s/箱 整箱发货" % (n, self.c["unit"]), th, band=260)
        return c

    def _panel_product(self, panel, pim, x, yb):
        """把小尺寸场景面板里合成产品，带接触阴影。"""
        lay = Image.new("RGBA", panel.size, (0, 0, 0, 0))
        h = max(14, int(pim.width * 0.07))
        ImageDraw.Draw(lay).ellipse([x + int(pim.width * 0.10), yb - h // 2,
                                     x + int(pim.width * 0.90), yb + h // 2], fill=(0, 0, 0, 90))
        lay = lay.filter(ImageFilter.GaussianBlur(10))
        out = panel.convert("RGBA")
        out.alpha_composite(lay)
        out.alpha_composite(pim, (x, yb - pim.height))
        return out.convert("RGB")

    def _grid_boxes(self, n, cols, rows, x0, y0, aw, ah, gapx=4, gapy=4):
        """按 cols×rows 算每个单体的 (left, bottom, width)，超出 n 的不返回。"""
        cw = (aw - gapx * (cols - 1)) / cols
        ch = (ah - gapy * (rows - 1)) / rows
        ratio = self.can.width / self.can.height
        w = min(cw, ch * ratio)
        h = w / ratio
        out, idx = [], 0
        for r in range(rows):
            for k in range(cols):
                if idx >= n:
                    return out
                x = x0 + k * (cw + gapx) + (cw - w) / 2
                y = y0 + r * (ch + gapy) + (ch - h) / 2
                out.append((int(x), int(y + h), int(w)))
                idx += 1
        return out

    def _stack(self, c, n, base_y, per=6, overlap=0.80, max_h=420, scale_dec=0.97, x_center=None):
        """按层堆叠排布并绘制，返回整组包围盒 (x0, y0, x1, y1)。"""
        import math
        per = max(2, min(7, per))
        layers, remain = [], n
        while remain > 0:
            take = min(per, remain)
            layers.append(take)
            remain -= take
        hgt = int(min(max_h, (base_y - 560) / max(1, len(layers)) / max(0.3, overlap)))
        hgt = max(160, hgt)
        y = base_y
        xs, ys = [], []
        for i, cnt in enumerate(layers):
            im = self.can_w(int(hgt * (scale_dec ** i)))
            gap = max(2, int(im.width * 0.015))
            total = im.width * cnt + gap * (cnt - 1)
            x0 = int((x_center if x_center is not None else c.width // 2) - total // 2)
            for k in range(cnt):
                xx = x0 + k * (im.width + gap)
                self._shadow(c, xx, y, im.width)
                c.paste(im, (xx, y - im.height), im)
                xs += [xx, xx + im.width]
                ys += [y - im.height, y]
            y -= int(im.height * overlap)
        return (min(xs), min(ys), max(xs), max(ys))

    def lay_matrix_pyramid(self, spec, S=2048):
        """分层堆叠：底层最多、逐层收窄，模拟整箱堆放的 3/4 视角。"""
        import math
        th = self._th(spec)
        c = self._bg(spec if (spec.get("bg") or spec.get("bg_mode")) else dict(spec, bg_color=(250, 250, 250)))
        d = ImageDraw.Draw(c)
        n = self.c["count"]
        d.text((110, 110), spec.get("head") or "一整箱 %d%s" % (n, self.c["unit"]), font=F(118), fill=th)
        d.text((114, 250), spec.get("sub") or self.spec, font=F(50, False), fill=INK)
        self._stack(c, n, 1700, per=max(3, min(6, int(math.ceil(n / 3.0)))),
                    overlap=0.80, max_h=420)
        self._strip(c, d, self.spec, "%d%s/箱 整箱发货" % (n, self.c["unit"]), th, band=240)
        return c

    def lay_matrix_film(self, spec, S=2048):
        """收缩膜整包：瓶身紧贴、行间叠压，再套一层半透明膜与斜向高光。"""
        import math
        th = self._th(spec)
        c = self._bg(spec if (spec.get("bg") or spec.get("bg_mode")) else dict(spec, bg_color=(252, 252, 252)))
        d = ImageDraw.Draw(c)
        n = self.c["count"]
        d.text((110, 100), spec.get("head") or "整箱 %d%s · 原箱未拆" % (n, self.c["unit"]),
               font=F(104), fill=th)
        d.text((114, 240), spec.get("sub") or self.spec, font=F(48, False), fill=INK)
        # 前后错位的整箱块：后排先画、位置略高，前排压在后排前面
        rows = 2 if n <= 8 else 3
        cols = max(1, int(math.ceil(n / rows)))
        hh = int(min(560, (1600 - 430) / (1 + (rows - 1) * 0.20)))
        im = self.can_w(hh)
        gapx = max(2, int(im.width * 0.02))
        step_y = int(im.height * 0.20)
        base = 1620
        xs, ys, left = [], [], n
        for i in range(rows):          # i=0 后排
            cnt = min(cols, left)
            left -= cnt
            total = im.width * cnt + gapx * (cnt - 1)
            x0 = (S - total) // 2
            y = base - (rows - 1 - i) * step_y
            for k in range(cnt):
                xx = x0 + k * (im.width + gapx)
                self._shadow(c, xx, y, im.width)
                c.paste(im, (xx, y - im.height), im)
                xs += [xx, xx + im.width]
                ys += [y - im.height, y]
        bx0, by0, bx1, by1 = min(xs), min(ys), max(xs), max(ys)
        pad = 44
        x0, y0, x1, y1 = bx0 - pad, by0 - pad, bx1 + pad, by1 + 26
        film = Image.new("RGBA", c.size, (0, 0, 0, 0))
        fd = ImageDraw.Draw(film)
        fd.rounded_rectangle([x0, y0, x1, y1], radius=52, fill=(255, 255, 255, 22))
        for i in range(5):
            xx = x0 + (x1 - x0) * (0.10 + 0.19 * i)
            fd.line([(xx, y0 + 20), (xx + 90, y1 - 20)], fill=(255, 255, 255, 60), width=18)
        base = c.convert("RGBA")
        base.alpha_composite(film)
        c = base.convert("RGB")
        d = ImageDraw.Draw(c)
        d.rounded_rectangle([x0, y0, x1, y1], radius=52, outline=(203, 208, 216), width=6)
        self._strip(c, d, self.spec, "%d%s/箱 原箱收缩膜" % (n, self.c["unit"]), th, band=240)
        return c

    def lay_matrix_row(self, spec, S=2048):
        """并列展示：件数少时单排相切，件数多时自动转双排，避免把单品压得过小。"""
        import math
        th = self._th(spec)
        c = self._bg(spec if (spec.get("bg") or spec.get("bg_mode")) else dict(spec, bg_color=(255, 255, 255)))
        d = ImageDraw.Draw(c)
        n = self.c["count"]
        d.text((110, 110), spec.get("head") or "一排 %d%s" % (n, self.c["unit"]), font=F(108), fill=th)
        d.text((114, 246), spec.get("sub") or self.spec, font=F(48, False), fill=INK)

        rows = 1 if n <= 8 else 2
        per = int(math.ceil(n / rows))
        step_ratio = 0.86
        hh = int(min(S * 0.54, (S - 260) / max(1, per - 1) / step_ratio
                     * (self.can.height / self.can.width)))
        im = self.can_w(hh)
        step = int(im.width * step_ratio)
        idx, base = 0, 1700
        for r in range(rows):
            cnt = min(per, n - idx)
            total = step * (cnt - 1) + im.width
            x0 = (S - total) // 2
            for k in range(cnt):
                self._shadow(c, x0 + k * step, base, im.width)
                c.paste(im, (x0 + k * step, base - im.height), im)
            idx += cnt
            base -= int(im.height * 0.52)
        self._strip(c, d, self.spec, "%d%s/箱 整箱发货" % (n, self.c["unit"]), th, band=240)
        return c

    def lay_matrix_hero(self, spec, S=2048):
        """主图 + 阵列：左侧小件阵列，右侧一件大图，信息分两栏。"""
        import math
        th = self._th(spec)
        c = self._bg(spec if (spec.get("bg") or spec.get("bg_mode")) else dict(spec, bg_color=(250, 250, 252)))
        d = ImageDraw.Draw(c)
        n = self.c["count"]
        d.text((110, 120), self.c.get("brand_cn", ""), font=F(104), fill=th)
        d.text((114, 250), spec.get("head") or "整箱 %d%s" % (n, self.c["unit"]), font=F(72, False), fill=INK)

        small = max(3, n - 1)
        # 左侧用紧凑堆叠，避免件数多时被排成一堆小点
        self._stack(c, small, 1700, per=max(3, min(6, int(math.ceil(small / 2.5)))),
                    overlap=0.74, max_h=330, x_center=int(S * 0.28))

        big = self.can_w(1120)
        bx = S - big.width - 140
        self._shadow(c, bx, 1690, big.width)
        c.paste(big, (bx, 1690 - big.height), big)
        self._strip(c, d, self.spec, "%d%s/箱 整箱发货" % (n, self.c["unit"]), th, band=240)
        return c

    def lay_split_color(self, spec, S=2048):
        th = self._th(spec)
        c = self._bg(spec if spec.get("bg") else dict(spec, bg_mode="grad",
                                                      grad_top=th, grad_bottom=tuple(max(0, v - 90) for v in th)))
        d = ImageDraw.Draw(c)
        d.text((110, 300), spec.get("head") or self.brand_cn, font=F(150), fill=WHITE)
        d.text((116, 500), spec.get("sub") or self.flavor, font=F(64, False), fill=(255, 255, 255))
        # 产品白卡：任何罐色都有对比，罐底也不会被规格条压住
        px0, py0, py1 = int(S * 0.50), int(S * 0.12), S - 340
        d.rounded_rectangle([px0, py0, S - 90, py1], radius=56, fill=(255, 255, 255))
        im = self.can_w(min(int(S * 0.50), py1 - py0 - 90))
        cx = px0 + ((S - 90 - px0) - im.width) // 2
        base = py1 - 45
        self._shadow(c, cx, base, im.width)
        c.paste(im, (cx, base - im.height), im)
        d.rounded_rectangle([110, S - 300, S - 110, S - 110], radius=40, fill=(255, 255, 255))
        d.text((160, S - 250), self.spec, font=F(64), fill=th)
        return c

    def lay_spec_panel(self, spec, S=2048):
        th = self._th(spec)
        c = Image.new("RGB", (S, S), WHITE)
        d = ImageDraw.Draw(c)
        d.text((110, 110), spec.get("head") or "规格说明", font=F(120), fill=th)
        d.text((114, 252), spec.get("sub") or "单%s %s，一箱 %d%s" % (self.c["unit"], self.c["volume"], self.c["count"], self.c["unit"]),
               font=F(50, False), fill=INK)
        im = self.can_w(900)
        c.paste(im, (150, 700), im)
        rows = [(("规格"), self.spec), (("口味"), "%s（%s）" % (self.flavor, self.brand_cn)), (("包装"), "整箱发货")]
        y = 640
        for k, v in rows:
            d.rounded_rectangle([1080, y, S - 110, y + 210], radius=32, fill=LGRAY)
            d.text((1130, y + 40), k, font=F(40, False), fill=GRAY)
            d.text((1130, y + 108), v, font=F(58), fill=INK)
            y += 240
        return c

    def lay_brand_card(self, spec, S=2048):
        th = self._th(spec)
        c = Image.new("RGB", (S, S), th)
        d = ImageDraw.Draw(c)
        d.text((120, 150), spec.get("head") or self.c.get("brand_en", self.brand_cn), font=F(170), fill=WHITE)
        d.text((126, 380), spec.get("sub") or "%s %s" % (self.brand_cn, self.flavor), font=F(70, False), fill=(255, 255, 255))
        im = self.can_w(1000)
        c.paste(im, ((S - im.width) // 2, int(S * 0.90) - im.height), im)
        d.text((132, S - 250), self.spec, font=F(56, False), fill=(255, 255, 255))
        return c

    def check_plan(self, plan):
        from collections import Counter
        fams = [p.get("family") or p.get("layout") for p in plan]
        cnt = Counter(fams)
        probs = []
        if len(plan) != 10:
            probs.append("主图数量 %d 张，规范要求 10 张" % len(plan))
        if len(cnt) < 4:
            probs.append("版式族仅 %d 个，规范要求 ≥4" % len(cnt))
        for f, k in cnt.items():
            if k > 3:
                probs.append("版式族「%s」占 %d 张，规范要求 ≤3" % (f, k))
        return cnt, probs

    def run_plan(self, plan):
        cnt, probs = self.check_plan(plan)
        for i, spec in enumerate(plan, 1):
            lay = spec.get("layout") or "studio_white"
            if lay not in self.LAYOUTS:
                raise SystemExit("未知版式 %s，可选：%s" % (lay, " / ".join(self.LAYOUTS)))
            img = getattr(self, "lay_" + lay)(spec)
            img.convert("RGB").save(os.path.join(self.md, "MD-%02d.jpg" % i), quality=95)
        self.plan_info = (cnt, probs)
        print("版式族覆盖 %d 个：%s" % (len(cnt), "、".join("%s×%d" % (k, v) for k, v in cnt.items())))
        for p in probs:
            print("WARN:", p)
        self.dt()

    def run(self):
        plan = self.c.get("plan")
        self.plan_info = None
        if plan:
            self.run_plan(plan)
        else:
            self.md01(); self.md02(); self.md03(); self.md04_md06()
            self.md07_md08(); self.md09_md10(); self.dt()
        self.write_spec()
        print("done ->", self.out)


def forbidden_line(lst):
    return "、".join(lst)


USAGE = """用法：
    python make_listing.py <config.json>

必填字段：brand_en, brand_cn, flavor, category, volume, count, unit,
          can_image, out_dir, scenes{ice,fridge,desk,party,food}
可选字段：theme, spec_text, shipping.forbidden, warehouse_note, title,
          price, price_single, price_ref, cost, production_date_placeholder,
          ref_image_note, unconfirmed
产出：主图 10 张（2048×2048）、详情图 6 张（750×1000）、详情长图（750×6000）、商品资料.md
样例见 templates/cola-200ml-24.json
"""


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0)
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    Kit(cfg).run()
