# pinduoduo-listing-images

拼多多商品上架素材的标准化生产流水线。给一份货盘表和一张商品实拍，产出整套可直接上架的素材。

一个小工具包，解决四件事：

1. **解析货盘表** → 拆成可上架的单品（口味 × 容量 × 箱规）
2. **算运费** → 把几百个单品收敛成几条运费模板规则
3. **出图** → 10 张主图 + 6 张详情图 + 详情长图，多版式
4. **生成标题与商品资料** → 平台计数校验 + 可直接交给发品环节的清单

---

## 目录结构

```
pinduoduo-listing-images/
├── SKILL.md                      完整操作规程（口径、流程、核验清单、常见坑）
├── README.md                     本文件
├── references/
│   └── prompt-library.md         提示词库：六族版式 + 变体矩阵 + 借鉴边界
├── scripts/
│   ├── parse_ledger.py           货盘表 → products.json
│   ├── pick_batch.py             范围未圈定时随机取样
│   ├── plan_shipping.py          快递规则 → 运费模板分组
│   ├── title_builder.py          60 单位标题生成与校验
│   ├── cutout_can.py             白底抠图（透明底）
│   └── make_listing.py           参数化出图
├── templates/
│   ├── cola-200ml-24.json        基础配置样例
│   ├── fanta-200ml-24.json       同规格换口味
│   ├── mirinda-grape-300ml-17.json  瓶装 + 多版式
│   └── plan-10style-example.json 十版式配置
└── assets/
    ├── can/                      单件产品图（透明底 PNG）
    └── scenes/                   场景底图（冰桶/冰箱/桌面/聚会/餐桌）
```

---

## 环境

- Python 3.8+
- `pip install pillow openpyxl`
- 中文字体：默认按平台查找（微软雅黑 / 苹方 / 思源黑体）。找不到时用环境变量指定：

```bash
export PDD_FONT_BOLD=/path/to/NotoSansCJK-Bold.ttc
export PDD_FONT_REGULAR=/path/to/NotoSansCJK-Regular.ttc
```

---

## 快速开始

```bash
# 1. 解析货盘表（表名与表头行按实际填）
python scripts/parse_ledger.py 货盘表.xlsx --out-dir data --sheet "一件代发价" --header-row 3

# 2. 范围没定就先随机取样（固定种子可复现）
python scripts/pick_batch.py data/products.json --n 5 --seed 20261106

# 3. 算运费分组
python scripts/plan_shipping.py data/products.json \
    --demote "北京,上海" --drop-surcharge "云南,贵州,四川,重庆"

# 4. 生成标题
python scripts/title_builder.py --brand 芬达 --flavor 经典橙味 --volume 200ml --count 24

# 5. 出图
python scripts/make_listing.py templates/plan-10style-example.json
```

产出目录：`output/<配置名>/主图/`、`详情图/`、`商品资料.md`

---

## 先读 SKILL.md

README 只讲怎么跑，**口径和红线在 SKILL.md 里**。动手前至少看这几节：

- 第零节 启动前置检查：货盘表拿不到就别开工
- 第一节 口径：单品拆分、品牌映射、箱规、单位、价格
- 第四节 主图配比与版式多样性
- 第五节 核验清单：出图后逐条过
- 第九节 发品衔接：后台字段坑（单位、品牌库、运费模板单选组等）

---

## 配置字段

必填：

| 字段 | 说明 |
|---|---|
| `brand_en` / `brand_cn` | 品牌英文 / 中文 |
| `flavor` | 口味或商品名 |
| `volume` / `count` / `unit` | 容量、件数、单位（罐/瓶） |
| `can_image` | 单件产品图路径（透明底 PNG） |
| `out_dir` | 输出目录 |
| `scenes` | 五个场景底图路径 |

常用可选：`theme`（主题色 RGB）、`spec_text`、`shipping`（禁发/加价）、`title`、`price`、`price_single`、`price_ref`、`cost`、`stock`、`warehouse_note`、`ref_image_note`。

### plan 模式：逐张指定版式

给 `plan` 数组可以逐张指定版式；不给则走旧版固定 10 张。

```json
"plan": [
  {"family": "白底棚拍", "layout": "studio_white", "qty": 3},
  {"family": "收缩膜整包", "layout": "matrix_film"},
  {"family": "分层堆叠", "layout": "matrix_pyramid"},
  {"family": "主图加阵列", "layout": "matrix_hero"}
]
```

12 种 layout：

`studio_white`（白底棚拍）、`fullbleed_left`（满幅左文右品）、`fullbleed_top`（满幅顶部大字）、`minimal_center`（极简留白）、`matrix`（网格）、`split_color`（撞色白卡）、`spec_panel`（信息图）、`brand_card`（品牌色卡）、`matrix_pyramid`（分层堆叠）、`matrix_film`（收缩膜整包）、`matrix_row`（并列展示）、`matrix_hero`（主图加阵列）

自动校验：主图必须 10 张、版式族 ≥4、同族 ≤3。不合规打 WARN 并写进 `商品资料.md`，不阻断出图。

---

## 素材准备

- `assets/can/`：单件产品图，透明底 PNG，长边建议 ≥800px
- `assets/scenes/`：场景底图，`ice` / `fridge` / `desk` / `party` / `food` 五张
- 没有素材时**先问用户要**，别去猜、别用别的口味顶替

多件合影不能直接竖切成窄条，会切掉罐身标签；邻件与主体相连时改用图生图提取，提取后核对标签没被重绘。

---

## 硬规则（违反会返工）

1. **数据可追溯**：每个价格、规格、配送值都要能追回货盘表某一行，不许估值
2. **箱规取常规值**：默认只做 6 的倍数（6/12/18/24/30/36/48）；1/3/5/8/15/17 这类除非用户点名
3. **品牌不等于商品名**：A 列是商品名，要过映射表才得到平台品牌
4. **单位按容量推断，实拍优先**：≤330ML 罐、≥400ML 瓶；拿到实拍以实物为准
5. **文案程序绘制**：中文不交给模型写，会出现方块乱码和压图
6. **禁用词按语义查**：「清爽解腻」不在词表里，但和「解油解腻」同类，照样违规
7. **首图守平台机制**：主体完整、无边框水印、无促销角标、文字不压产品

---

## 常见坑

| 现象 | 原因 |
|---|---|
| 标题少个 `ml` | `--volume` 只给了数字，要写 `200ml` |
| 标题出现「芬达芬达」 | 品牌被商品名包含时重复拼接，脚本已自动去重 |
| 中文变方块 | 字体没加载，设 `PDD_FONT_BOLD` |
| 罐底被色条切 | 色条会压住产品轮廓，属于切边 |
| 17 瓶排成一行 | 质数箱规要用近似 2:1 网格 |
| 解析直接崩 | 工作表名不同，用 `--sheet` 指定 |

---

## 许可

未附带许可证文件。作者可在发布时自行选择（MIT / Apache-2.0 / 私有）。

内置的版式与流程来自实际项目迭代，不含任何第三方受版权保护的素材。若使用他人产品图，需自行确认授权。
