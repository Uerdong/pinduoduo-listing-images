# 提示词库（拼多多套图）

两类提示词：**单品提取**（把实拍图里的单个商品分离出来）和**空场景生成**（只出背景，不含产品）。
文字与版式一律程序绘制，模型提示词里**不要**要求生成中文文案。

---

## 1. 单品提取（image_edit）

用途：从多件合影里取出一件干净单品，保留真实标签。

```
Asset type: single product packshot for an e-commerce listing.
From the reference image, isolate only the {目标单品} and render it as one standalone item,
upright and centred on a pure white background.
The entire item must be visible with clear white margin on every side: top, full body, bottom.
Keep the printed design exactly as on the reference — {主色/图案}, {品牌标识}, {中文标签文字},
{材质边缘描述}。
No other products, no banner, no text overlays, no drop shadow, no reflection.
```

must_keep：主色与质感、品牌标识、中文标签、材质边缘、比例
must_change：只保留单个商品、纯白底、完整不裁切、去掉其它商品与横幅

要点：
- 图片比例按商品实际形状给（饮料罐用 2:3）
- 目标单品必须在合影里处于最前层，否则会被邻件遮挡

---

## 2. 空场景生成（image_generate）

用途：补齐场景图。**只生成背景，不含任何产品与文字**，产品由程序合成。

通用后缀（每张都要带）：
`Empty centre foreground area where a product would be placed. No text, no logos, no products, no people.`

### 冰桶 / 冰镇
```
Commercial product photography background. A galvanised metal ice bucket filled with crushed ice
and clear ice cubes, standing on a light wooden outdoor terrace table, bright summer daylight
from the left, soft natural shadows, blurred green plants and a wooden chair far behind,
shallow depth of field. {通用后缀}
```

### 冰箱 / 冷藏
```
Photorealistic background. Interior of an open modern refrigerator with clean empty clear glass
shelves, cool white LED lighting, bright and hygienic, slight reflection on the glass,
shallow depth of field. {通用后缀}
```

### 办公桌
```
Photorealistic background. A clean light-wood office desk surface with warm daylight from a
window on the left, a closed dark notebook and a small potted plant softly blurred behind,
soft shadows, shallow depth of field. {通用后缀}
```

### 可扩展场景（同结构替换主体）
- 餐桌：浅色餐桌 + 餐盘虚化 + 侧光
- 露营：木质野餐桌 + 草地虚化 + 午后逆光
- 便利店冷柜：玻璃门冷柜 + 白冷光
- 厨房台面：白色石英台面 + 窗户侧光

---

## 3. 合成规范（程序侧）

- 产品置于场景的水平承托线上，底部加椭圆柔光阴影（模糊半径 ≈ 18px，透明度 60~80）
- 抠图后必须做「近白 + 低饱和」连通区域置透明 → 腐蚀 2px → 羽化 1px，否则彩色底会出现白边
- 场景图上加文字时用半透明白色面板承载，避免文字直接压在复杂背景上
- **色块与卡片不得覆盖产品轮廓**，罐身被卡片盖住等同于切边（已踩过）
- 场景图上的文案只写体验/场景，不写价格、活动、销量

---

## 4. 禁止的提示词写法

- 要求模型生成中文海报文案（会乱码）
- 要求模型「重新设计包装/重绘品牌标识」
- 要求模型把多件商品「拆成独立单品」但不给完整轮廓（会切边）
- 要求模型把产品放进场景（会扭曲标签）
- 只写形容词不写槽位（「高级感」「有氛围」出不来差异化，见 §5）

---

## 5. 主图版式原型（解决「10 张一个模板」）

### 为什么要有这一节

同一款商品 10 张主图如果共用一套版式（白底 + 顶部标题 + 底部规格条），视觉上等于 1 张图重复 10 次，点击率上不去。版式差异必须落在**背景世界观、光位与色温、色彩关系、构图与留白、道具与材质**五处，只换文案不算换版式。

### 起步版式族（已登记 6 个，**不是上限**）

| 族 | 视觉特征 | 常放第几张 | 文字承载 |
|---|---|---|---|
| A 野餐草地 | 满幅草地 / 格纹布、暖阳逆光、柠檬薄荷冰块、多件并排 | MD-04 / MD-07 | 左上大字 + 左侧图标胶囊 |
| B 生活方式 | 桌面近景、键盘茶杯、暖光浅景深、单件居中 | MD-06 | 几乎不加字，靠构图说话 |
| C 甜品极简 | 浅色台面 + 甜品绿植柔焦、单件居中、大面积留白 | MD-03 | 顶部一行小字 |
| D 促销信息 | 纯色渐变底、产品 + 纸箱组合、信息密度高 | MD-01 / MD-09 | 顶大字 + 副标 + 角标 + 底条 |
| E 冰爽批发 | 冰蓝 / 冰晶背景、矩阵多件、冷光 | MD-02 | 左侧口号 + 底部规格条 |
| F 撞色棚拍 | 红黄或橙蓝撞色、冰块道具、单件大图 + 阵列 | MD-01 / MD-10 | 左侧大字 + 底部服务条 |

### 分配规则

- 10 张主图至少覆盖 **4 族**，同一族不超过 **3 张**
- 第 1 张（首图）信息必须完整（产品 + 规格），但版式可以打破常规用来抢视觉
- 场景族不设下限：放几张由商品需要决定，可以先一张都没有
- 同一商品内部，背景主色不超过 3 个色系，避免看起来像不同商品

### 五槽位写法（提示词结构，不是形容词堆砌）

每条背景提示词按顺序写满五个槽位：

1. **背景世界观**——这是哪、什么材质、什么时间（如 light wooden picnic table on grass, bright summer afternoon）
2. **光位与色温**——主光方向 + 色温值（如 warm backlight from upper left, 5000K）
3. **构图与产品占位**——产品占哪块、留白在哪（如 single product centred, wide empty space on the right）
4. **道具与材质**——3~5 件道具，写到材质（如 clear ice cubes, lemon slices, mint leaves, red-checkered cloth）
5. **文字安全区**——明确哪块不能有杂物（如 keep the upper-left third clean for text overlay）

反面写法：「一张高级感的饮料海报」「非常有氛围感」——模型只能给均值，出不来差异化。

### 起步六族的英文提示词片段

配合 §2 的通用后缀使用。

**A 野餐草地**
```
Commercial beverage photography. Light wooden picnic table on green grass, red-checkered
cloth, bright summer backlight from upper left at 5000K, dappled sunlight through leaves,
blurred foliage and a wicker basket far behind, clear ice cubes, lemon slices and mint leaves
scattered on the table, shallow depth of field. Keep the upper-left third clean for text.
{通用后缀}
```

**B 生活方式**
```
Photorealistic lifestyle background. A light-wood desk beside a window, warm afternoon sunlight
raking from the right at 4000K, a mechanical keyboard at the left edge, a frosted glass cup of
tea at the right edge, a wooden reed diffuser softly blurred behind, natural soft shadows,
very shallow depth of field. Keep the centre clear for a single product.
{通用后缀}
```

**C 甜品极简**
```
Photorealistic background. A pale marble counter with a light green cake and lime slices softly
blurred on both sides, large tropical leaves out of focus behind, soft even daylight at 5500K,
generous empty space around the centre, minimal and clean. Keep the centre third empty.
{通用后缀}
```

**D 促销信息（纯色棚拍）**
```
Studio product photography background. Seamless gradient backdrop, deep red fading to bright
yellow at the bottom, hard key light from upper left with soft fill from the right, crisp
ice-block props at the bottom corners, clean graphic look, no texture noise. Keep the upper
half clean for a large headline.
{通用后缀}
```

**E 冰爽批发**
```
Commercial background. A wall of crushed ice and frosted ice crystals, cool blue-white lighting
from behind at 7000K, faint mist, glossy reflective floor, high-key and crisp. Keep the bottom
band clear for a spec strip.
{通用后缀}
```

**F 撞色棚拍**
```
Studio background. Split colour backdrop, vivid orange upper half and deep blue lower half,
crisp studio strobes from both sides, scattered clear ice cubes on a glossy black surface,
strong contrast, commercial poster look. Keep the left third clean for vertical text.
{通用后缀}
```

### 扩展版式族（G ~ N，同样只是起点）

| 族 | 视觉特征 | 常放第几张 | 文字承载 |
|---|---|---|---|
| G 俯拍平铺 | 正上方俯拍、木桌或大理石、多件平铺 + 道具环绕 | MD-02 / MD-09 | 顶部留白横排 |
| H 整箱堆叠 | 原箱与纸箱堆叠、托盘、仓库工业冷光 | MD-02 / MD-05 | 左侧竖排或角标 |
| I 夜市霓虹 | 夜间摊档、暖黄串灯、霓虹反光、暗调 | MD-08 | 左下大字 + 发光描边 |
| J 运动补水 | 健身房或跑道、冷调侧光、毛巾水壶 | MD-06 / MD-07 | 顶部标语 |
| K 节日限定 | 春节红金 / 圣诞红绿、礼盒元素、雪花或灯笼 | MD-10 | 居中大字 + 副标 |
| L 极简几何 | 纯色几何色块、硬光、单件 + 大面积留白 | MD-01 / MD-03 | 极简一行字 |
| M 液体飞溅 | 深色底、水花四溅、高速摄影、产品悬空 | MD-04 / MD-07 | 大字压在上三分之一 |
| N 冷柜陈列 | 玻璃门冷柜、白冷光、层板铺货 | MD-05 | 底部规格条 |

**G 俯拍平铺**
```
Top-down flat lay photography. Light oak table surface, evenly diffused overhead daylight at
5500K, products arranged in a loose grid with props (ice cubes, citrus halves, folded linen,
a kraft carton corner) framing the edges, crisp shadows, everything in focus. Keep the top
third empty for a horizontal headline.
{通用后缀}
```

**H 整箱堆叠**
```
Commercial warehouse photography. Stacked corrugated cartons on a wooden pallet, cool industrial
lighting from high above at 6500K, concrete floor with soft reflections, shrink-wrap texture
detail, slight depth falloff into a blurred storage rack. Keep the left third clean for vertical text.
{通用后缀}
```

**I 夜市霓虹**
```
Night market photography. A street food stall at night, warm string lights and faint neon
reflections on a wet counter, light smoke drifting, dark moody exposure at 3000K, bokeh
signage far behind. Keep the lower-left area clean and slightly darker for text.
{通用后缀}
```

**J 运动补水**
```
Sports lifestyle background. Edge of an indoor running track, cool side light at 6000K,
a rolled towel and a steel water bottle softly blurred at the sides, polished floor with
long reflections, crisp and clean. Keep the upper band clean for a slogan.
{通用后缀}
```

**K 节日限定**
```
Festive commercial background. Deep red and gold palette, subtle snow or paper-lantern bokeh
depending on the season, warm key light at 2800K, glossy surface with soft reflections,
elegant and restrained. Keep the centre clear for a single product and the top for a headline.
{通用后缀}
```

**L 极简几何**
```
Minimal graphic background. Two large flat colour blocks meeting on a hard diagonal, crisp
studio lighting with a defined shadow edge, matte seamless surface, no texture, high contrast.
Keep one large empty block for minimal copy.
{通用后缀}
```

**M 液体飞溅**
```
High-speed splash photography. Deep charcoal background, clear water or beverage droplets frozen
mid-air around an empty centre, hard rim light from behind at 7000K, glossy black surface.
Keep the centre hollow and the top third clean for a headline.
{通用后缀}
```

**N 冷柜陈列**
```
Retail chiller background. Inside a glass-door convenience store cooler, empty clean shelves,
cool white LED strips at 7000K, light condensation on the glass, shallow depth of field.
Keep the middle shelf clear for the product.
{通用后缀}
```

---

### 变异矩阵：自己造新族的方法

不必等这份清单变长。任选下面七个维度各取一个值组合，就是一个新族；组合出来后按五槽位写成提示词即可。

| 维度 | 取值示例 |
|---|---|
| 环境 | 室内桌面 / 户外草地 / 海边沙滩 / 街头夜市 / 仓储 / 便利店 / 影棚 / 虚拟几何 |
| 时间与光 | 清晨侧光 / 正午硬光 / 黄昏逆光 / 夜晚暖光 / 冷柜白光 / 双灯棚拍 |
| 承托材质 | 浅木 / 大理石 / 金属拉丝 / 水泥 / 织物 / 冰面 / 水面 / 无（悬空） |
| 道具族 | 冰块与水珠 / 水果与香草 / 甜品烘焙 / 餐食烧烤 / 电子数码 / 运动器材 / 礼盒灯笼 / 无道具 |
| 构图 | 单件居中 / 矩阵阵列 / 俯拍平铺 / 对角排布 / 前后景分层 / 局部特写 / 悬空飞溅 |
| 色彩 | 品牌撞色 / 冷暖对冲 / 低饱和莫兰迪 / 单色高级灰 / 季节限定色 |
| 情绪 | 清爽 / 温暖 / 热闹 / 高级 / 动感 / 节庆 |

举例：`海边沙滩 + 黄昏逆光 + 浅木 + 水果香草 + 单件居中 + 冷暖对冲 + 清爽` = 「黄昏海滩」族；`影棚 + 双灯 + 金属拉丝 + 无道具 + 局部特写 + 单色高级灰 + 高级` = 「金属特写」族。这两个族都可以直接登记入库。

### 新增族的登记规则

新族不要私下用，登记完再用，否则团队里各写各的、批量时对不上。

1. **用途定位**：说清「这张为什么用它」，不能只是「好看」
2. **五槽位提示词**：按 §5 的五槽位写全，附可直接复制的英文片段
3. **禁忌**：该族最容易犯的错（如夜市族容易把人像拍糊、冷柜族容易反光压产品）
4. **去重**：与已登记族的差异度要 >30%，只换背景色不算新族
5. **登记**：加进上面的表，并在 SKILL 变更记录里写一条日期

---

## 6. 借鉴参考图：借什么、不借什么

**借**：版式骨架（产品占位、留白位置）、光位与色温、色彩关系、道具材质、文字层级（几层字、谁大谁小）

**不借**：
- 别人的产品与包装（罐身、瓶型、品牌标识）
- 别人的产地与进口声明——参考图里出现「香港进口饮料」这类表述时，只有实际产地相符才能写，不能照抄
- 别人的服务承诺——「漏液包赔」「加固包装」没有实际履约能力就不能写
- 违规词——参考图里出现过「官方正品」「正品保证」，这两条明令禁止，样式再好看也不能抄

**判断方法**：把参考图上的文字全部抹掉，只看构图、光、色、道具。去掉文字后版式依然成立的，可以借；全靠文案撑起来的，借过来会空。

**多口味陷阱**：参考图是「三味聚享」这类多口味组合时，单品 SKU 只能借版式，不能借多口味阵列，否则图货不符。
