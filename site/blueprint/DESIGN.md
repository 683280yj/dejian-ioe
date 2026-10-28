---
name: 酿见 × 筹策 · 网页设计规格
version: 1.0
date: 2026-10-28
applies_to:
  - 酿见 · 白酒经营智能决策蓝图（甲方页面）
  - 筹策官网（chouce-site）
format: 参考 Google Labs design.md（YAML tokens + Markdown 规范正文）
license_note: 字体/图标/色阶思路均取自免费可商用来源（思源系列 OFL、霞鹜文楷 OFL、Lucide ISC、Radix Colors MIT 思路）

colors:
  wine:   # 暗红系：1–2 页面底 / 3–6 表面 / 7–8 边框与深实色 / 9–10 品牌实色 / 11–12 浅红文字
    1: "#1d0908"
    2: "#200c0a"
    3: "#2a0f0b"
    4: "#33120d"
    5: "#3d1712"
    6: "#451c14"
    7: "#571f24"
    8: "#6f2a30"
    9: "#87353b"
    10: "#9c3f46"
    11: "#c47a72"
    12: "#f3ddd3"
  gold:   # 金系：1–4 深金底与边框 / 5–8 次级金字 / 9 主金 / 10–12 标题与数字金
    1: "#2e2008"
    2: "#4a3418"
    3: "#6b4c22"
    4: "#8a6a35"
    5: "#a98f66"
    6: "#b39a72"
    7: "#c9a86a"
    8: "#d2a45d"
    9: "#e0a55a"
    10: "#e3b96a"
    11: "#e8c87e"
    12: "#f0c9a0"
  paper:  # 米/纸系：1–7 浅表面（由浅到深） / 8 沙色 / 9–12 暖中性文字（用于浅底）
    1: "#fffdf7"
    2: "#fbf7ea"
    3: "#f5f1e4"
    4: "#f5eedf"
    5: "#eae7d6"
    6: "#e2ddc8"
    7: "#ddd0af"
    8: "#c9b59a"
    9: "#897d6f"
    10: "#6b5a50"
    11: "#5c4a42"
    12: "#2a1512"
  neutral: # 中性系：仅用于系统截图内 UI、表单控件、数据表格
    1: "#ffffff"
    2: "#faf9f7"
    3: "#f3f0ea"
    4: "#eeeeee"
    5: "#e6e6e6"
    6: "#dddddd"
    7: "#c8c4bc"
    8: "#a8a29a"
    9: "#777777"
    10: "#555555"
    11: "#2a2a2a"
    12: "#171310"
  status:
    danger: "#c0392b"        # 警示红（浅底/圆点）
    danger_on_dark: "#e0685f" # 深底异常文字与图表线（修正，见 §2.3）
    positive: "#64735f"       # 墨绿（万卷口径，正向状态，仅浅底）

typography:
  font_family:
    display: '"Noto Serif SC", "Source Han Serif SC", "Songti SC", "SimSun", serif'
    accent: '"LXGW WenKai", "霞鹜文楷", "Kaiti SC", "STKaiti", serif'
    body: '"Noto Sans SC", "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif'
    mono: '"Geist Mono", "SFMono-Regular", Menlo, Consolas, monospace'
  font_size:
    display: clamp(40px, 6.1vw, 92px)
    h1: clamp(40px, 6.1vw, 92px)
    h2: clamp(32px, 4.2vw, 58px)
    h2_compact: clamp(28px, 3.2vw, 44px)
    h3_serif: 24px
    h3_sans: 18px
    lead: clamp(16px, 1.3vw, 18px)
    body: 16px
    small: 14.5px
    caption: 12.5px
    kpi_number: clamp(34px, 3.3vw, 48px)
    alert_number: clamp(44px, 5.4vw, 80px)
  line_height:
    display: 1.16
    heading: 1.22
    body: 1.75
    dense: 1.6
  letter_spacing:
    display: 0.02em
    plaque: 0.2em
    eyebrow: 0.12em   # 英文眉题，全大写
    caption_loose: 0.3em

spacing:
  page_pad: clamp(20px, 4.4vw, 64px)
  content_max: 1312px
  section_y: clamp(80px, 10vw, 136px)
  scale: [4, 8, 12, 16, 18, 24, 32, 40, 64]

rounded:
  none: 0        # 默认：牌匾/卡片/按钮均为直角
  seal: 4px      # 印章、印章式图标
  chip: 6px      # 徽标、标签、提示条
  frame: 10px    # 截图框、截图带图片
  pill: 999px    # 仅状态点/进度点等极小元素
  circle: 50%    # 序号环、热点点位

shadows:
  card_on_dark: "0 24px 60px rgba(0,0,0,.35)"
  card_on_light: "0 18px 40px rgba(68,30,27,.12)"
  shot_on_light: "0 30px 70px rgba(68,30,27,.18), 0 0 0 1px rgba(68,30,27,.08)"
  shot_on_dark: "0 30px 70px rgba(0,0,0,.30)"
  bar: "0 8px 30px rgba(0,0,0,.18)"
  toast: "0 18px 40px rgba(0,0,0,.30)"

components:
  button_primary:
    background: "{colors.wine.9} 或 linear-gradient(180deg, #963a41, {colors.wine.8})"
    text: "#ffffff"
    padding: "16px 32px"
    rounded: "{rounded.none}"
  button_secondary_on_dark:
    background: "{colors.paper.4}"
    text: "#441e1b"
    padding: "16px 32px"
  card_plaque:
    background: "linear-gradient(160deg, {colors.wine.6}, {colors.wine.4})"
    border: "1px solid rgba(224,165,90,.42)"
    rounded: "{rounded.none}"
  chip_anomaly_high:
    background: "{colors.status.danger}"
    text: "#ffffff"
  input_on_dark:
    background: "{colors.wine.2}"
    border: "1px solid rgba(224,165,90,.4)"
    text: "{colors.paper.4}"
    min_height: 44px
---

# 网页设计规格 · 酿见 × 筹策

> 适用范围：酿见蓝图页与筹策官网共享同一套视觉语言——**暗红底、烫金字、米色文字**，对齐甲方品牌 PPT（茅台系深红 + 金）。
> 取值标记：`现行` = 已在筹策官网 `site.css` 上线并验证；`补` = 为补齐 12 级色阶推导的值；`修正` = 针对已知问题改定的值，正文给出理由与对比度实测。
> 对比度为 WCAG 相对亮度公式实测值（2026-10-28 计算），正文门槛 ≥ 4.5:1，大字（≥24px 或 ≥18.66px 加粗）≥ 3:1。

## 1. 设计原则

1. **图多字少，深色块压场。** 首屏与关键板块以真实产品图、场景图、系统界面截图为主角；文字只保留标题、一句说明、关键数字。深色整幅板块（wine-2→wine-3 渐变）与浅色米纸板块交替，但深色为主导（占比 ≥ 60%）。
2. **红金米三色打天下。** 全站只用暗红、金、米/纸三系 + 中性灰（仅截图内 UI 与表格）。金色只做描边、数字、眉题与强调，绝不大面积铺金；传统元素（回纹、牌匾、印章、撕纸边）先几何化/线条化再用，不直接贴纹样照片。
3. **大标题双色分层。** 标题层级靠颜色不靠堆字重：主行米白（paper-4），关键词行换烫金（gold-10/11）；标题用思源宋体 900，副题与眉题用大写英文 + 大字距。
4. **AI 只解释，不改业务——视觉上同样如此。** AI 输出（解释条、异常 chips）在视觉上是从属层：置于数据/依据之下，左金线 + 小一号字 + 「AI 解释 / 一句话解释」徽标明示来源；chips 是只读徽标（无按钮形态、无 hover 抬升），采纳/忽略等业务动作保持原有按钮规格与位置，AI 层不新增任何可执行控件、不遮挡原始数字与公式依据。
5. **动效只服务氛围与状态。** 只用 transform/opacity；粒子、光晕、跑马灯一律不挡内容、不抢焦点；`prefers-reduced-motion` 时全部关闭（见 §7）。

## 2. 颜色 Tokens

分级思路参考 Radix Colors：每色 12 级，1–2 背景、3–5 表面、6–8 边框/中间调、9–10 实色、11–12 文字。

### 2.1 暗红系 wine（品牌主色）

| 级 | Hex | 用途 |
|---|---|---|
| 1 | `#1d0908` 补 | 最深底：整幅遮罩深端、页脚渐变终点 |
| 2 | `#200c0a` 现行 | 页面底（body 背景） |
| 3 | `#2a0f0b` 现行 | 板块底（渐变起点/终点） |
| 4 | `#33120d` 现行 | 表面 1：深板块卡面、代码/表格区底 |
| 5 | `#3d1712` 现行 | 表面 2：抬升卡、测算面板渐变起点 |
| 6 | `#451c14` 现行 | 卡片渐变亮端、hover 表面 |
| 7 | `#571f24` 现行 | 强边框、页脚渐变深端、分隔带 |
| 8 | `#6f2a30` 现行 | 深酒红实色：主按钮渐变终点、下拉/选中深态 |
| 9 | `#87353b` 现行 | **品牌酒红**：主按钮、印章、页脚底、浅底标题强调 |
| 10 | `#9c3f46` 现行 | 实色 hover（按钮、链接强调） |
| 11 | `#c47a72` 补 | 低对比浅红字：仅大字/装饰，禁止正文 |
| 12 | `#f3ddd3` 补 | 高对比浅红字：酒红面上的大标题（罕用） |

渐变规范：板块底 `linear-gradient(180deg, wine-4, wine-3)` 或 `(wine-3, #38150f)`；牌匾卡 `linear-gradient(160deg, wine-6, wine-4)`；主按钮 `linear-gradient(180deg, #963a41, wine-8)`；页脚 `linear-gradient(180deg, wine-9, wine-7)`。

### 2.2 金系 gold（描边与强调，禁止大面积铺色）

| 级 | Hex | 用途 |
|---|---|---|
| 1 | `#2e2008` 补 | 金调最深底：金徽标底、选中行底 |
| 2 | `#4a3418` 补 | 深金表面 |
| 3 | `#6b4c22` 补 | 深金边框（深底弱分隔） |
| 4 | `#8a6a35` 补 | 中金边框、未激活图标 |
| 5 | `#a98f66` 现行 | 注脚金：注脚/口径说明（限深底，见 §2.5 修正 F） |
| 6 | `#b39a72` 现行 | 次级金字：对比表旧值列、次级说明 |
| 7 | `#c9a86a` 现行 | 带注金：截图带图注、流程说明 |
| 8 | `#d2a45d` 现行 | 中间金：图表第二线、进度填充终点 |
| 9 | `#e0a55a` 现行 | **主金**：描边、焦点环、眉题点、激活态 |
| 10 | `#e3b96a` 现行 | 标题金：双色标题第二行 |
| 11 | `#e8c87e` 现行 | 数字金：KPI 数字、表头（深底） |
| 12 | `#f0c9a0` 现行 | 最浅金：酒红面上的金字、大标题点缀 |

透明度用法（现行）：金边框多用 `rgba(224,165,90,.28–.55)`（即 gold-9 的 alpha 档：.28 弱分隔 / .42 卡描边 / .55 强调边）；金底纹 `rgba(224,165,90,.05–.07)`。

### 2.3 米/纸系 paper（浅表面 + 浅底文字）

| 级 | Hex | 用途 |
|---|---|---|
| 1 | `#fffdf7` 现行 | 最亮面：测算面板、截图内卡 |
| 2 | `#fbf7ea` 补 | 浅卡面 |
| 3 | `#f5f1e4` 现行 | 纸底：浅板块背景 `--paper` |
| 4 | `#f5eedf` 现行 | 米白：深底主文字、浅面交替 |
| 5 | `#eae7d6` 现行 | 奶油底 `--cream`：浅板块交替底 |
| 6 | `#e2ddc8` 现行 | 浅板块深一档：账目区/价值区底 |
| 7 | `#ddd0af` 补 | 浅卡渐变深端 |
| 8 | `#c9b59a` 现行 | 沙色：双色标题浅底变体、深底次级标题 |
| 9 | `#897d6f` 现行 | `--muted`：**仅大字/装饰**（对比度不足，见修正 C） |
| 10 | `#6b5a50` 现行 | 浅底次级文字（修正主力，5.80:1） |
| 11 | `#5c4a42` 现行 | 浅底正文（7.39:1） |
| 12 | `#2a1512` 现行 | 墨 `--ink`：浅底标题、深底反色块文字 |

深底正文梯队（跨系取色，硬性规定）：标题 `paper-4`/`#f7ecd9` → 说明 `#d8c3a5`（介于 paper-8 与 gold-7 之间的现行值）→ 次级 `gold-6` → 注脚 `gold-5`。

### 2.4 中性系 neutral（仅截图内 UI / 表单 / 表格）

`#ffffff, #faf9f7, #f3f0ea, #eeeeee, #e6e6e6, #dddddd, #c8c4bc, #a8a29a, #777777, #555555, #2a2a2a, #171310`（1–12 级；现行值取自系统表格 .rt：行线 `#eeeeee`、表头线 `#e6e6e6`、次级字 `#777777`、表头字 `#555555`、正文 `#2a2a2a`）。中性系不得用于品牌区版式，只出现在被展示的系统界面与数据表内部。

状态色：`danger #c0392b`（浅底警示/圆点）、`danger_on_dark #e0685f`（深底异常文字/图表线）、`positive #64735f` 墨绿（万卷口径，正向状态，仅浅底；深底正向用 gold-11 代替，不另造绿）。

### 2.5 对比度达标组合（实测，唯一许用清单）

| 前景 | 背景 | 比值 | 许用 |
|---|---|---|---|
| `#f7ecd9` | wine-2 `#200c0a` | 16.05 | 标题、正文 |
| `#f5eedf` paper-4 | wine-2 | 16.25 | 标题、正文 |
| `#d8c3a5` | wine-2 / wine-3 / wine-4 | 10.97 / 10.47 / 9.95 | **深底说明文字下限**，正文 |
| `#d8c3a5` | wine-7 `#571f24` | 7.54 | 页脚正文 |
| `#f5eedf` | wine-9 `#87353b` | 6.98 | 按钮字、页脚字 |
| `#ffffff` | wine-9 / `#963a41`（按钮渐变亮端） | 8.07 / 7.05 | 主按钮字 |
| `#f5eedf` | `#441e1b`（棕） | 12.56 | 整幅深棕板块字 |
| `#e8c87e` gold-11 | wine-2 / wine-3 | 11.62 / 11.09 | KPI 数字、表头 |
| `#e0a55a` gold-9 | wine-2 | 8.67 | 眉题、图标、强调字 |
| `#f0c9a0` gold-12 | wine-9 | 5.21 | 酒红面上的金字（唯一许用金） |
| `#ecd9c6` | wine-9 | 5.88 | 酒红面正文（预警区） |
| `#ead3c2` | wine-9 | 5.61 | 页脚次级字 |
| `#c9ae85` | wine-6 `#451c14` | 6.91 | 卡面说明 |
| `#a98f66` gold-5 | wine-3 / wine-6 | 5.81 / 4.76 | 注脚（限 ≥12.5px 非关键信息） |
| `#5c4a42` paper-11 | paper-3 | 7.39 | 浅底正文 |
| `#6b5a50` paper-10 | paper-3 | 5.80 | 浅底次级文字 |
| `#87353b` wine-9 | paper-3 | 7.14 | 浅底眉题/强调字 |
| `#2a1512` paper-12 | gold-9（标签底） | 7.99 | 金标签上的墨字 |
| `#e0685f` | wine-2 | 5.65 | 深底异常文字、图表主线（深底） |
| `#c0392b` | `#f5eedf` | 4.71 | 浅底警示字/点（限 ≥12.5px） |

**修正清单（覆盖现行实现中的不达标用法）：**

- **修正 A（深底说明文字下限）**：深红底上的说明/正文一律不得低于 `#d8c3a5` 一档。禁止把浅底正文色 `#5c4a42`、次级色 `#897d6f` 迁到深底（曾在 V4 压暗时出现 `.lead`、`#chouce-calc .more summary` 深底近乎不可读）。
- **修正 B（酒红不上深红）**：`wine-9 #87353b` 文字禁止直接放在 wine-1～7 深底上（同色系无对比）。深底强调一律走金系；酒红文字只许出现在 paper-1～6 浅底（7.14:1）。
- **修正 C（浅底次级）**：`--muted #897d6f` 在 paper-3/cream 上仅 3.56 / 3.23:1，降级为大字/装饰专用；正文级次级文字改用 paper-10 `#6b5a50`（5.80:1）。
- **修正 D（金字上酒红面）**：gold-9 `#e0a55a` 在 wine-9 上仅 3.73:1，禁止小字；酒红面上的金字统一 gold-12 `#f0c9a0`（5.21:1）。
- **修正 E（图表线分底色）**：亮红 `#e0685f` 在浅底仅 2.94:1，禁止；浅底图表主线用 wine-9 `#87353b`，`#e0685f` 仅限深底。
- **修正 F（注脚金使用面）**：gold-5 `#a98f66` 在 wine-6 卡面上仅 4.76:1，只许 ≥12.5px 的非关键注脚；关键注脚升 gold-7 `#c9ae85`（6.91:1）。


## 3. 字体 Tokens

### 3.1 字族栈

| 角色 | 栈 | 说明 |
|---|---|---|
| 展示/标题 display | `"Noto Serif SC", "Source Han Serif SC", "Songti SC", "SimSun", serif` | 思源宋体；本地子集字体名 `CSerif`（900）优先，CDN/系统同名回退 |
| 点缀 accent | `"LXGW WenKai", "霞鹜文楷", "Kaiti SC", "STKaiti", serif` | 霞鹜文楷：牌匾题字、引言、图注题、印章旁小注；不用于正文与数据 |
| 正文 body | `"Noto Sans SC", "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif` | 本地子集 `CSans`（400/700）；表格、表单、说明文字 |
| 数字/等宽 mono | `"Geist Mono", "SFMono-Regular", Menlo, Consolas, monospace` | 本地子集 `CMono`；眉题英文、公式、代码式依据 |

字重：标题 900（Heavy）为主，600（SemiBold）用于蓝图页 H3 与长标题；正文 400，强调 700。禁止 100–300 细字重出现在深底（笔画在深色上易断）。

### 3.2 字号阶梯（现行值）

| Token | 值 | 行高 | 字距 | 用途 |
|---|---|---|---|---|
| display | `clamp(40px, 6.1vw, 92px)` | 1.16 | .02em | 首屏 H1（双行双色） |
| h2 | `clamp(32px, 4.2vw, 58px)` | 1.22 | .01em | 板块标题 |
| h2-compact | `clamp(28px, 3.2vw, 44px)` | 1.22 | .01em | 整幅深色板块标题（同行案例） |
| h3-serif | 24–30px | 1.3 | 0 | 卡组小标题、依据区标题 |
| h3-sans | 17–18px / 700 | 1.5 | 0 | 功能卡标题（无衬线粗体） |
| lead | `clamp(16px, 1.3vw, 18px)` | 1.75 | 0 | 板块导语（一句为限） |
| body | 16px（≤600px 时 15px） | 1.75 | 0 | 正文 |
| small | 14.5–15px | 1.65 | 0 | 卡内说明、表格旁注 |
| caption | 12–13px | 1.6 | 0 | 图注、口径、脚注 |
| eyebrow | 12–12.5px mono | 1.5 | .12em 全大写 | 板块眉题 `01 · 运筹` 式 |
| kpi-number | `clamp(34px, 3.3vw, 48px)` 宋体 | 1.1 | 0 | 数据条数字 |
| alert-number | `clamp(44px, 5.4vw, 80px)` 宋体 | 1.1 | 0 | 预警区大数字 |
| plaque | 20–26px 宋体 | 1.2 | .2–.24em | 牌匾字、Logo 字标 |

### 3.3 数字规范

- 所有数据数字（KPI、表格、测算结果）必须 `font-variant-numeric: tabular-nums`（或 `font-feature-settings: "tnum" 1`），保证列内对齐不跳动。
- 展示型大数字用宋体（display 栈），数据表内数字用无衬线 + tnum；公式/依据串用 mono。
- 数字与单位：数字宋体/等宽，单位小一号（`small` 18px 对 48px 数字，现行 `.num small` 口径），不换行（`white-space: nowrap` 于数字组）。

## 4. 间距 / 圆角 / 阴影

### 4.1 间距

- 页面边距 `--pad: clamp(20px, 4.4vw, 64px)`；内容最大宽 `--max: 1312px`（含边距总宽 = max + 2×pad）。
- 板块纵向 `padding: clamp(80px, 10vw, 136px)`；板块头与内容间距 `clamp(40px, 5vw, 64px)`。
- 间距阶梯（px）：4 / 8 / 12 / 16 / 18 / 24 / 32 / 40 / 64。网格间隙：卡组 18px，密集格 1px 发丝线分隔（账目格），截图带 22px。
- 触控目标：可点击元素最小 44px 高（导航链接、选项卡、表单控件）；正文行高 1.75 不压缩。

### 4.2 圆角（直角为默认，这是本品牌识别之一）

| Token | 值 | 用途 |
|---|---|---|
| none | 0 | 按钮、卡片、板块、表格容器——默认全部直角 |
| seal | 4px | 印章、印章式图标底 |
| chip | 6px | 徽标、标签、待公布提示条 |
| frame | 10px | 截图框、截图带图片 |
| pill/circle | 999px / 50% | 仅状态圆点、序号环、热点点位 |

禁止：卡片/按钮使用 ≥8px 圆角（与牌匾直角语言冲突）。

### 4.3 阴影（统一带黑或酒红色调，禁止灰色泛光）

| Token | 值 | 用途 |
|---|---|---|
| card-on-dark | `0 24px 60px rgba(0,0,0,.35)` | 深底上的抬升卡（首屏演示卡） |
| card-on-light | `0 18px 40px rgba(68,30,27,.12)` | 浅底卡 hover 抬升 |
| shot-on-light | `0 30px 70px rgba(68,30,27,.18), 0 0 0 1px rgba(68,30,27,.08)` | 浅底截图框 |
| shot-on-dark | `0 30px 70px rgba(0,0,0,.30)` | 深底截图框 |
| bar | `0 8px 30px rgba(0,0,0,.18)` | 顶栏滚动态 |
| toast | `0 18px 40px rgba(0,0,0,.30)` | 浮层提示 |

规则：浅底阴影色固定 `rgba(68,30,27, α)`（wine-12 的 RGB 68,30,27），深底阴影固定纯黑 alpha；同一元素最多两层阴影；内高光可用 `inset 0 1px 0 rgba(245,238,223,.14)`（深卡顶光，现行）。

## 5. 组件规格

### 5.1 导航（顶栏）

- 高 76px，滚动后 64px；滚动态底 `rgba(52,22,19,.92)` + `backdrop-filter: blur(10px)` + 底边 `1px rgba(224,165,90,.35)` + shadow bar。
- 左：印章（32×32，wine-9 底，paper-4 字，radius seal，内描边 `inset 0 0 0 2px rgba(245,238,223,.35)`）+ 字标宋体 24px 字距 .24em。
- 链接 15px，opacity .86 → hover 1；登录按钮描边 `1px rgba(245,238,223,.45)` padding 9px 18px；主按钮见 5.2。
- ≤960px：汉堡按钮 44×44（三线 24×2，展开转 ×，动效 .3s），菜单整幅深底 `rgba(52,22,19,.98)` 下拉，链接行高 ≥48px，行间发丝线 `rgba(245,238,223,.12)`。

### 5.2 按钮

| 状态 | 主按钮（深底/浅底通用） | 次按钮（深底） | 幽灵按钮（浅底） |
|---|---|---|---|
| 默认 | 渐变 `#963a41 → wine-8`，白字，内描边 `inset 0 0 0 1px rgba(224,165,90,.35)` | paper-4 底，`#441e1b` 字，内描边 `rgba(224,165,90,.55)` | 透明底，边 `1px rgba(68,30,27,.45)`，棕字 |
| padding/字号 | 16px 32px / 16px | 同左 | 16px 30px / 16px |
| hover | 渐变转 `#a9474e → #7c3238`，`translateY(-2px)`（.2s） | 同主按钮的位移 | 底转 paper-3，`translateY(-2px)` |
| active | 回落无位移 | 同 | 同 |
| disabled | opacity .45，禁位移、禁指针 | 同 | 同 |
| 焦点 | `:focus-visible` 外环 `2px solid gold-9`，offset 3px（全站统一） | 同 | 同 |

主按钮可加流光（`::after` 白色渐变扫过，3.2s 间隔，现行）；流光只许出现在首屏主 CTA，reduced-motion 关闭。

### 5.3 牌匾式卡片

- 深底版（首屏演示卡/板块卡）：底 `linear-gradient(160deg, rgba(56,22,18,.93), rgba(34,11,9,.90))`，边 `1px solid rgba(224,165,90,.45)`，顶内高光，shadow card-on-dark，可叠 `blur(8px)` 背景模糊（压在照片上时）。内题头小字 gold-9 11px，卡标题 paper-4 18px/700，说明 `#dcc9ab` 13–15px。
- 浅底版：paper-3 底 + 边 `1px solid rgba(169,132,62,.42)` + 顶边 `3px solid wine-9`（能力卡口径），hover `translateY(-4px)` + shadow card-on-light（.3s）。
- 牌匾变体（文旅/蓝图页眉）：双线描边（外 1px gold-9、内 1px `rgba(224,165,90,.4)`，间距 4px）+ 四角回纹角花（SVG 线描，stroke gold-9），中央文楷题字。仅用于页眉题/章节题，不用于数据卡。

### 5.4 数据 KPI 卡 / 数据条

- 整幅数据条（首屏底）：4 列，底 `linear-gradient(180deg, rgba(28,9,7,.88), rgba(28,9,7,.95))`，顶边 `1px rgba(224,165,90,.5)`，列间 `1px rgba(224,165,90,.18)`；数字 gold-11 宋体 kpi-number，单位 18px，说明 `#d8c8b4` 13.5px。
- KPI 卡（浅底/蓝图页）：paper-1 底，边 `1px rgba(169,132,62,.42)`，内距 26px 24px；标签 caption 灰，数字宋体 28–34px wine-9（浅底）或 gold-11（深底），注脚 small。
- 数字滚动/计数动画只许 transform/opacity 外的方式？计数本身改文本不在禁列，但同一数字只许在入场时跑一次，时长 ≤1.2s，reduced-motion 直接显终值。

### 5.5 表格

- 展示型表格（补货建议 .rt 口径）：容器白底（neutral-1）或深底 wine-4 二选一，整表最小宽 760px，窄屏横向滚动（见 §8）。
- 字号 13px / 行高 1.65；表头 600 字重，浅底版表头字 neutral-10、底线 `1px neutral-5`；深底版表头 gold-11、底线 `rgba(224,165,90,.35)`。
- 单元格 padding：表头 8px 10px，正文 10px；行线浅底 `1px neutral-4`，深底 `rgba(224,165,90,.14)`。
- 数字列右对齐 + tnum；关键数字 16px/700 wine-9（浅底）或 gold-11（深底）；标签 `.rt-tag`：浅底版底 `#f3e3e1`、字 wine-9、radius chip、padding 2px 8px、12.5px；深底版底 `rgba(224,165,90,.12)`、字 gold-11。
- 行 hover：浅底 `#fffdf7`，深底 `rgba(224,165,90,.06)`（.2s）。

### 5.6 徽标 / 异常标记 chips

- 语义分级（与补货解释层一致）：`high` 高异常 = danger 底白字；`warn` 中 = gold-9 底、墨字（paper-12，7.99:1）；`info` 提示 = 中性描边（深底：边 `rgba(224,165,90,.4)`、字 `#d8c3a5`；浅底：边 neutral-6、字 paper-11）。
- 规格：12–12.5px，padding 2px 8px（行内）或 4px 10px（独立行），radius chip，字重 400–600，`white-space: normal` 允许换行（异常文案可长），chips 间距 4–6px。
- **只读铁律**：chips 无 hover、无 active、无指针光标，不做成按钮样；可操作的行内动作（采纳/忽略）只用 5.2 的按钮规格，二者在视觉上必须可区分。
- AI 解释条：位于依据段之下，`border-left: 2px solid gold-9` + 底 `rgba(224,165,90,.06)`（深底）/ `rgba(135,53,59,.05)`（浅底），14px，行首徽标「AI 解释」（gold-9 底墨字）或「一句话解释」（描边款）标明来源，现行实现为 Bootstrap `text-bg-warning` 徽标 + 正文，二者等价取一。

### 5.7 滑杆与表单

- 输入框（深底）：底 wine-2，边 `1px rgba(224,165,90,.4)`，字 paper-4，最小高 44px，字号 16px（防 iOS 缩放）；浅底版：白底，边 `rgba(68,30,27,.25)`，字 paper-12。
- 焦点：边转 gold-9（深底）/ wine-9（浅底）+ 外环 `0 0 0 3px rgba(224,165,90,.25)`（深底）/ `rgba(135,53,59,.15)`（浅底，现行）。
- 标签：14px，深底 `#d8c3a5`、浅底 paper-11；必填/口径注脚 caption 注脚金（深底）/ paper-10（浅底）。
- 滑杆（range）：轨道 4px，深底 `rgba(224,165,90,.25)`、浅底 `rgba(68,30,27,.18)`；已选段 gold-9→gold-8 渐变；拇指 20px 圆，gold-9 底 + 2px paper-4 描边（深底）/ wine-9 底（浅底），`accent-color: gold-9` 作降级口径；拇指触控区 ≥44px（用 padding 扩）。
- 下拉（select）：同输入框规格，右侧箭头用 Lucide `chevron-down` 16px 线描（见 §6），不用系统默认箭头时以背景 SVG 实现。
- 禁用态：opacity .45，边转虚线（口径未定的「待公布」提示条：虚线边 `1px dashed rgba(245,238,223,.45)` + 底 `rgba(42,21,18,.35)`，现行）。

### 5.8 选项卡（Tabs）

- 默认：透明底，边 `1px rgba(68,30,27,.3)`（浅底）/ `rgba(224,165,90,.4)`（深底），字棕/米，最小高 44px，padding 0 20px，15px，直角。
- hover：边转 wine-9/gold-9，字同色。
- 选中：wine-9 底白字（浅底）/ gold-9 底墨字（深底），`aria-selected="true"` 驱动，不用纯类名猜状态。
- 切换动效：面板 `pin` 入场（opacity + translateY(14px→0)，.5s `cubic-bezier(.2,.8,.2,1)`）；≤960px 时整排横向滚动、隐藏滚动条、按钮不压缩。

### 5.9 跑马灯 / 截图带

- 文字跑马灯：棕 `#441e1b`（现行 `--brown`，介于 wine-6/7）整幅，上下 padding 18px；宋体 32px（≤600px 时 22px），词间 60px，分隔符 gold-9 20px；动画 `translateX(-50%)` 36s linear infinite，内容必须双份拼接保证无缝；hover 不暂停（文字带）；reduced-motion 静止。
- 截图带（showband）：底 `linear-gradient(180deg, #241110, #3d1a16)`，顶边 `1px rgba(224,165,90,.35)`，上下 padding 40/44px；带题宋体 20px paper-4 + 英文小注 11px 字距 .3em gold-7；图卡宽 440px（≤760px 时 300px）、图高 248px（移动 180px）、`object-fit: cover; object-position: top`，radius frame，金描边 `rgba(224,165,90,.45)`，shadow `0 22px 44px rgba(0,0,0,.45)`；图注 gold-11 13px 字距 .14em 居中；动画 42s linear infinite，**hover 暂停**（与文字带相反，因为要看图）；reduced-motion 静止且可横向滚动。
- 截图本体必须套 `.shot` 框：顶栏（三点 + 地址小字，浅底版底 `#efe9da`）+ 图 + 图注（caption，paper-10/深底 gold-5），禁止裸图直贴。

### 5.10 页脚

- 底 `linear-gradient(180deg, wine-9, wine-7)`，paper-4 字；顶部可加撕纸边（SVG 波浪/撕纸 path，填充 wine-9，高 40px，现行 `.torn`）——撕纸只许出现在页脚顶与浅→深交界，整站最多 2 处。
- 结构：左品牌区（印章反色：paper-4 底 wine-9 字 + 字标 26px 字距 .2em + 文楷引言 18px），右导航两列 15px、行高 ≥44px、opacity .88 → hover 1 + 下划线。
- 底部条：顶线 `1px rgba(245,238,223,.25)`，13px `#ead3c2`（5.61:1），备案/链接 hover 转白。


## 6. 图标与图像规范

### 6.1 图标（Lucide 描边风格，ISC 许可可商用）

- 画布 24×24，描边宽 **2px**（默认）；大图标（32px 以上展示用）可降至 1.8px 保持视觉轻重一致；小图标（16px）保持 2px 不得加粗。
- 端点/拐点：`stroke-linecap: round; stroke-linejoin: round`；无填充（fill: none），颜色一律 `currentColor` 跟随文字色。
- 尺寸档：16px（行内/箭头/下拉）、20px（按钮内、选项卡）、24px（导航/功能入口）、32px（空状态/板块锚点）、60px 序号环内的宋体字（非图标，见下）。
- 语义色：默认跟随正文；强调态 gold-9；警示 danger；禁止给线描图标上多色/渐变。
- 传统图形的线描化：回纹角花、瓦当、印章走 SVG 单线描（stroke gold-9，宽 1.5–1.6px，透明度 .05 作底纹 / 1.0 作描边）——底纹用法：回纹 SVG 96×96 平铺、`stroke-opacity .05`，只许出现在浅底板块与登录/空状态等外壳，**数据区（表格、测算、图表）禁止底纹**。
- 序号语言：用宋体字 + 描边环代替图标表达步骤（环：60px 圆、1.5px wine-9 描边、内阴影双环，现行 `.ring`；或 32px 编号圆 mono 字），与 Lucide 图标二选一，同一组件内不混用。

### 6.2 产品图 / 场景图

- 首屏背景图：全幅 cover，贵州山水/酒镇场景实拍优先；必须压深色遮罩——横屏遮罩 `linear-gradient(90deg, rgba(36,12,10,.93) 0%, rgba(60,24,21,.78) 42%, rgba(60,24,21,.25) 100%)` + 底部 `linear-gradient(0deg, rgba(36,12,10,.7), transparent 35%)`；文字所在半幅的遮罩不透明度不得低于 .78（保证 §2.5 的对比度成立）。
- 双图轮播：两张场景图交叉淡入淡出 16s 周期（opacity + scale 1.1→1.02 缓降），两图共用同一遮罩。
- 产品图（酒瓶/礼盒）：深底衬托，主体破框压色块（图压 wine-7 圆/拱形色块，现行敦煌式手法的本品牌版），色块只许 wine/gold 系；图注用文楷 13–15px。
- 颗粒层：照片上可叠 SVG 噪点（`feTurbulence`，opacity .16，`mix-blend-mode: overlay`），只许首屏与整幅图板块，禁止叠在截图与表格上。
- 系统界面截图：真实截图、1x/2x 双档 + WebP 优先；套 §5.9 的 `.shot` 框；截图内 UI 颜色属 neutral 系，不受品牌色阶约束，但截图框外的一切元素必须回到品牌色。

## 7. 动效规范

### 7.1 通用

- **只动 transform 与 opacity**（外加 `filter: blur` 仅用于标题逐字入场）。禁止用 width/height/top/left 做动画（跑马灯用 translateX，进度条用 scaleX）。
- 时长档：微交互 .2s（hover/按钮）、状态切换 .3–.35s（顶栏、卡片抬升）、面板入场 .5s、板块 reveal .8s、氛围循环 16s（轮播/极光）/ 36–42s（跑马灯）。
- 缓动：入场统一 `cubic-bezier(.2,.8,.2,1)`；线性只用于跑马灯与进度；状态脉冲（预警点）1.4s `pulse`、热点 2s `ping`——脉冲只许表达真实状态（预警未处理），不作装饰。

### 7.2 入场 Reveal

- 板块级 `.rv`：`opacity 0 + translateY(28px)` → 入视口加 `.rv-in`，.8s 上述缓动；同板块子元素可级联延迟（现行首屏：kicker .2s → sub 1.3s → cta 1.6s → endorse 1.9s；数据条四列 .2s 间隔）。
- 标题逐字：每字 `.7s` 入场（translateY(.45em) + blur(6px)→0），仅首屏 H1；H1 双文案轮换时整行 .45s 淡出/入。
- 无 JS / 打印 / 加载超时必须有兜底直接显示（现行 `.rv.shown` + print 规则），动效永不绑架内容可见性。

### 7.3 氛围效果边界（粒子 / 光晕 / 倾斜）

- 金尘粒子：Canvas 绘制，z-index 1（内容 z-index 2 之上、遮罩之上），`pointer-events: none`；颜色 gold-11 alpha .25–.75 闪烁，上浮速度 ≤ .5px/帧。
- 极光光晕：2–3 团 radial-gradient（gold-9 .20 / wine-10 .28 / gold-9 .10），16s alternate 缓动漂移（位移 ≤1.5%、缩放 ≤1.06）。
- 视差倾斜：仅首屏演示卡组与截图舞台，幅度 ≤ 3°，.35s 回正；仅 `(pointer: fine)` 设备启用。
- 滚动进度条：顶置 3px，gold-9→gold-11 渐变，`scaleX` 驱动，z-index 80。
- **移动端降级**：≤600px 关闭粒子 Canvas 与倾斜（现行首屏演示卡在 ≤600px 直接隐藏，同理）；极光保留静态一帧；跑马灯保留（降字号）。电量/性能优先于氛围。
- `prefers-reduced-motion: reduce`：全站 `animation/transition: none !important`，轮播定格首图，跑马灯静止，视频背景隐藏，只保留即时状态变化。

## 8. 响应式断点与移动端规则

### 8.1 断点（两档主断点 + 两档收拢）

| 区间 | 规则 |
|---|---|
| >1200px | 全量布局；KPI/能力/账目网格 4 列，六业 3 列 |
| 901–1200px | 收拢档：4 列网格降 2 列，依据区转单列，流程条 7→4 列（现行官网在 1200/1100 有同名收拢，合并实现时以本表为准） |
| **561–900px（主断点一）** | 导航转汉堡（顶栏 64px）；首屏转单列、演示卡限宽 520px；数据条 2×2；步骤 2 列；预警/六业转 1–2 列；选项卡横滚；表格横滚（min-width 760px 不压缩） |
| **≤560px（主断点二）** | 正文 15px；H1 `clamp(36px, 10.4vw, 46px)`；首屏演示卡隐藏；CTA 全宽平分、最小高 48px；网格全单列；流程条转竖排时间线；截图图内宽 760px 横滚且热点点位隐藏；跑马灯字号 22px；页脚导航 2 列 |

> 对齐说明：酿见蓝图页现行代码即以 900/560 为两档主断点；筹策官网现行代码为 1200/1100/960/600 四档，语义与本表一一对应（960≈900 导航档、600≈560 移动档），新页面一律按本表 900/560 落地，老页面下次改版时收敛。

### 8.2 移动端硬性规则

- 触控目标 ≥44px（导航行 ≥48px）；表单控件字号 ≥16px 防 iOS 自动缩放。
- 安全区：顶栏/页脚左右 padding 取 `max(--pad, env(safe-area-inset-*))`；浮层提示 bottom 叠加 `env(safe-area-inset-bottom)`。
- 首屏高度用 `100svh`（回退 `100vh`）；移动端遮罩改纵向渐变（顶 .72 → 中 .6 → 底 .9），标题第二行加 `text-shadow 0 2px 18px rgba(20,6,5,.55)` 保对比（现行修正）。
- 横向滚动只许出现在：选项卡排、截图带、宽表容器；页面本体 `overflow-x: clip` 兜底，禁止整页横滚。
- 动效与媒体降级按 §7.3；视频背景在移动端以海报图替代（现行 `.cbg` 在 reduced-motion 隐藏，同规则推广到 ≤560px）。

## 附录 A. CSS 变量映射（实现对照）

| 规格 Token | 现行变量/值 | 备注 |
|---|---|---|
| wine-9 | `--wine: #87353b` | 品牌主色 |
| wine-8 | `--wine-d: #6f2a30` | |
| wine-4～6 渐变 | `#33120d / #3d1712 / #451c14`（V4 层字面值） | 建议回填为 `--wine-4/5/6` 变量 |
| 棕（板块交界） | `--brown: #441e1b` | 介于 wine-6/7，整幅结果条/跑马灯底 |
| paper-3 | `--paper: #f5f1e4` | |
| paper-5 | `--cream: #eae7d6` | |
| paper-12 | `--ink: #2a1512` | |
| paper-8 | `--sand: #c9b59a` | |
| paper-9 | `--muted: #897d6f` | 限大字/装饰（修正 C） |
| gold-9/11/12 | `#e0a55a / #e8c87e / #f0c9a0`（字面值） | 建议回填为 `--gold-9/11/12` |
| 深底正文 | `#d8c3a5`（字面值） | §2.5 下限，建议回填 `--on-dark-body` |
| 页面边距/最大宽 | `--pad / --max` | 见 §4.1 |
| 字族 | `--serif / --sans / --mono` | 栈定义见 §3.1；accent 文楷栈为蓝图页新增 `--kai` |

## 附录 B. 落地检查清单

- [ ] 深底任意说明文字取色 ≥ `#d8c3a5` 档，且与所压背景在 §2.5 清单内
- [ ] 无 wine-9 文字压深底、无 gold-9 小字压 wine-9 面
- [ ] 数字全部 tnum；展示数字用宋体
- [ ] 按钮/卡片直角；圆角只出现在 seal/chip/frame/圆点
- [ ] 阴影只用 §4.3 的六个 token，无灰色泛光
- [ ] AI 解释条与 chips 从属呈现，chips 无可点击形态
- [ ] 动效只动 transform/opacity；reduced-motion 全关且有无 JS 兜底
- [ ] 900/560 两档逐项过 §8.1；触控 ≥44px；本体无横滚
