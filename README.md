# pinduoduo-listing-images

拼多多商品上架的**全链路**生产流水线。从一份货盘表出发，一路做到商品进入草稿箱、字段回读无误，并把数据交回经营分析。

不是只做图。覆盖 8 个环节：**解析 → 取样 → 运费 → 出图 → 标题 → 商品资料 → 发品上传 → 回读验收**。

---

## 它到底管什么

| # | 环节 | 输入 | 产出 | 操作人 |
|---|---|---|---|---|
| 1 | **货盘表解析** | 一件代发价 Excel | `products.json`：口味 × 容量 × 箱规拆成可上架单品，含品牌映射、包装单位、多仓取价 | 主控 |
| 2 | **取样** | products.json | 本批要做的商品清单（范围未圈定时按固定种子随机取，只取常规箱规） | 主控 |
| 3 | **运费分组** | products.json | 几百个单品收敛成 4 组运费模板规则（禁发 / 加价 / 包邮三类降级） | 主控 |
| 4 | **出图** | 单件产品图 + 场景底图 | 10 张主图 + 6 张详情图 + 详情长图，12 种版式、17 个场景池 | 设计专家 |
| 5 | **标题** | 品牌 / 口味 / 规格 | 平台计数 ≤60 的标题，含禁用词语义校验 | 主控 |
| 6 | **商品资料** | 上述全部 | `商品资料.md`：标题、三档价格、毛利、配送、图片清单、待确认项 | 主控 |
| 7 | **发品上传** | 图片 + 商品资料 | 拼多多草稿箱里的商品，字段按后台坑位填好 | 电商管家 |
| 8 | **回读验收** | 草稿 | 逐字段回读结果，差异清单，可交经营分析的干净数据 | 主控 / 数据分析专家 |

一句话：**中间没有断点**。出图完不是交付终点，字段填对、草稿存上、回读无误才算完。

---

## 流水线怎么跑

```
货盘表.xlsx
   │  parse_ledger.py        拆单品 + 品牌映射 + 单位判定 + 多仓取价
   ▼
products.json  ── pick_batch.py ──▶ 本批清单（范围未圈定时随机取样）
   │
   │  plan_shipping.py       收敛运费规则
   ▼
运费模板分组（4 组）
   │
   │  pick_scenes.py         抽场景（同类不重复、跨商品轮换）
   ▼
   │  make_listing.py        12 种版式出图
   ▼
主图 10 张 + 详情图 6 张 + 长图 + 商品资料.md
   │
   │  —— 发品环节（电商管家）——
   ▼
拼多多草稿箱 → 逐字段回读 → 差异修复 → 待资质提审
   │
   ▼
经营数据回看（数据分析专家）
```

---

## 各环节的关键约束

**解析**
- A 列是商品名不是品牌，要过 `BRAND_MAP` 映射；无前缀的按「行内继承」取行首品牌
- 包装单位按容量硬映射：200/330ML 记罐，**300ML 记瓶**（PET），450/500/888ML/1.25L 记瓶；品牌级覆盖优先于容量表
- 同一规格多仓并存时取最低代发价仓

**运费**
- 平台「指定区域加收」只有 9 个省可选。不可加价的省份分两类：`--demote` 降禁发（北京上海）、`--drop-surcharge` 降包邮（云贵川渝），其余默认禁发（海南）

**出图**
- 程序绘制负责文案、色块、排版；模型只负责单品提取、场景合成、光影修复
- 10 主图覆盖 ≥4 种版式族，同族 ≤3 张；场景图不设下限
- 场景必须含产品、必须落在承托面、比例合理
- 质量门槛：抠图后 <600px 停止出图，600~900px 出图但必须反馈源图偏软
- 罐体、中文标签、净含量禁止重绘，重绘即判废

**发品**
- 只存草稿，不提审不上架；长图不上传（1:8 不符平台 ≥1:3）
- 保存后刷新再回读，错误计数以刷新后为准
- 资质未上传停在草稿，不代填编号

---

## 目录结构

```
pinduoduo-listing-images/
├── SKILL.md                      完整规程：口径、流程、核验清单、后台坑位、操作人
├── README.md                     本文件
├── references/
│   └── prompt-library.md         提示词库：版式族、变体矩阵、借鉴边界
├── scripts/
│   ├── parse_ledger.py           货盘表 → products.json
│   ├── pick_batch.py             范围未圈定时随机取样
│   ├── pick_scenes.py            场景抽取（同类不重复、跨商品轮换）
│   ├── plan_shipping.py          运费规则 → 模板分组
│   ├── title_builder.py          60 单位标题生成与禁用词校验
│   ├── cutout_can.py             白底抠图（透明底）
│   └── make_listing.py           参数化出图
├── templates/
│   ├── cola-200ml-24.json        罐装基础配置
│   ├── fanta-200ml-24.json       同规格换口味
│   ├── mirinda-grape-300ml-17.json  瓶装 + 整箱多拍法
│   └── plan-10style-example.json 十版式配置
└── assets/
    ├── can/                      单件产品图（透明底 PNG）
    └── scenes/                   场景底图
```

---

## 环境

- Python 3.8+
- `pip install pillow openpyxl`
- 中文字体：默认按平台查找（微软雅黑 / 苹方 / 思源黑体），找不到时用环境变量指定

```bash
export PDD_FONT_BOLD=/path/to/NotoSansCJK-Bold.ttc
export PDD_FONT_REGULAR=/path/to/NotoSansCJK-Regular.ttc
```

出图允许联网调用图像模型做增强。脚本本身离线可跑，模型用于单品提取、场景合成、光影修复与超分。

---

## 快速开始

```bash
# 1. 解析货盘表
python scripts/parse_ledger.py 货盘表.xlsx --out-dir data --sheet "一件代发价" --header-row 3

# 2. 范围没定就随机取样（固定种子可复现）
python scripts/pick_batch.py data/products.json --n 5 --seed 20261106

# 3. 运费分组
python scripts/plan_shipping.py data/products.json \
    --demote "北京,上海" --drop-surcharge "云南,贵州,四川,重庆"

# 4. 抽场景（避开上一款用过的）
python scripts/pick_scenes.py --n 3 --seed 20261106 --avoid ice_bucket,fridge_shelf

# 5. 标题
python scripts/title_builder.py --brand 芬达 --flavor 经典橙味 --volume 200ml --count 24

# 6. 出图
python scripts/make_listing.py templates/plan-10style-example.json
```

产出：`output/<配置名>/主图/`、`详情图/`、`商品资料.md`

---

## 配置字段

必填：`brand_en` / `brand_cn` / `flavor` / `volume` / `count` / `unit` / `can_image` / `out_dir` / `scenes`

常用可选：`theme`、`spec_text`、`shipping`（禁发/加价）、`title`、`price`、`price_single`、`price_ref`、`cost`、`stock`、`warehouse_note`、`ref_image_note`

### plan 模式：逐张指定版式

```json
"plan": [
  {"family": "白底棚拍", "layout": "studio_white", "qty": 3},
  {"family": "收缩膜整包", "layout": "matrix_film"},
  {"family": "冷柜冷光", "layout": "fullbleed_top", "bg": "assets/scenes/fridge.png",
   "anchor": 0.50, "scale": 0.30}
]
```

**12 种 layout**：`studio_white`、`fullbleed_left`、`fullbleed_top`、`minimal_center`、`matrix`、`split_color`、`spec_panel`、`brand_card`、`matrix_pyramid`、`matrix_film`、`matrix_row`、`matrix_hero`

**整箱数量图的 5 种拍法**：网格平铺 / 分层堆叠 / 收缩膜整包 / 并列展示 / 主图加阵列。质数箱规（17/13）自动改近似 2:1 网格，不排成一行。

`anchor` 控制产品底部基线，`scale` 控制产品高度占比——场景图里产品必须落在承托面上，这两个参数就是干这个的。

自动校验：主图必须 10 张、版式族 ≥4、同族 ≤3。不合规打 WARN 并写进 `商品资料.md`，不阻断出图。

---

## 硬规则

1. **数据可追溯**：每个价格、规格、配送值都要能追回货盘表某一行
2. **箱规取常规值**：只做 6 的倍数，1/3/5/8/15/17 这类除非用户点名
3. **品牌不等于商品名**：A 列要过映射；品牌库只有基础品牌时，属性与标题同时降级
4. **单位按容量 + 品牌覆盖**：300ML 是瓶不是罐
5. **文案程序绘制**：中文不交给模型写，会出现方块与压图
6. **禁用词按语义查**：「清爽解腻」不在词表但同样违规
7. **首图守平台机制**：主体完整、无边框水印、无促销角标、文字不压产品
8. **场景不重复**：每款抽不同场景，跨商品轮换，不许每款都冰箱配烧烤

---

## 常见坑

| 现象 | 原因 |
|---|---|
| 标题少个 `ml` | `--volume` 只给数字，要写 `200ml` |
| 标题叠字「芬达芬达」 | 品牌被商品名包含，脚本已自动去重 |
| 中文变方块 | 字体未加载，设 `PDD_FONT_BOLD` |
| 瓶身被抠坏 | `--erode` 开太大，800px 源图用 1 |
| 产品悬在冰箱中间 | 缺 `anchor`，产品没落在层板上 |
| 17 瓶排成一行 | 质数箱规要近似 2:1 网格 |
| 解析直接崩 | 工作表名不同，用 `--sheet` 指定 |

---

## 先读 SKILL.md

README 只讲怎么跑。口径、红线、后台字段坑、操作人分工，都在 SKILL.md：

- 第零节 启动前置：货盘表拿不到就别开工
- 第一节 口径：单品拆分、品牌映射、箱规、单位、价格
- 第四节 主图配比与版式多样性
- 第五节 核验清单：出图后逐条过
- 第九节 发品衔接：后台字段坑
- 第十一节 操作规则：谁做什么、做到什么程度算完成

---

## 许可

未附带许可证文件，作者可自行选择（MIT / Apache-2.0 / 私有）。内置版式与流程来自实际项目迭代，不含第三方受版权保护的素材；使用他人产品图需自行确认授权。
