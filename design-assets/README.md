# 德鉴 × IOE 设计资产包

德鉴酒业（首批体验企业）多品牌 To-B 进销存 + AI 决策系统用的视觉资产，参赛项目为 2026 iCAN 精创杯 AI 智能决策挑战赛。
资产总览图在 `preview.png`（2400×6690，上半部分纸底、下半部分深色）。来源与许可见 `LICENSES.md`。

> 本目录**只放资产**，不改 templates/static。资产由 lane-b（UI）负责接入。

## 配色（docs/PALETTE_V2.md）

| 角色 | 浅色（内容区） | 深色（Hero / 登录 / 侧栏） |
|---|---|---|
| 背景 | paper `#fbf8f3` | `#211b18` |
| 卡片 | card `#fffdf9` | `#2d2523` |
| 正文 | ink `#241e1b` | 米白 `#fbf8f3` |
| 次要文字 | muted `#7c716c` | line `#e8dfd7` |
| 线 | line `#e8dfd7` | 米白 14%（`#4a4340`） |
| **AI 产出** | gold `#c99a57` | 暗金 `#e4b76f` |
| **人的决定** | wine `#6e1f2c`（主按钮实心） | wine-2 `#a43f45` |
| 强调 / 风险 | wine-2 `#a43f45` | wine-2 `#a43f45` |
| 达标 / 改善 | green `#43685e` | green `#43685e` |

语义规则：**金色 = AI 算出来的东西，酒红 = 人做的决定。** AI 只起草和提示，不自动审批、下单、改库存或发货。低风险的自动执行（库存预警、日报、入库差异提示）用 `auto-exec` 图标，并且始终可以关掉。

- 注意：在浅色底的淡金色块（`#f5ebdc`）上，金色小字对比度偏低。正文请用 ink，金色只用在 ≥13px 的标签或图形上。
- 深色区块用于首页 Hero、登录页和侧栏；内容区和表格仍用纸底。页面是深浅交替，不是全站暗色。

## 1. 图标 `icons/*.svg`（26 个）

- 规格：24px 网格，1.5 描边，`stroke="currentColor"`，round cap/join。改颜色用 CSS `color` 即可。
- 角色色（总览图里用的颜色）：ink 类用正文色；ai 类用 gold（深色底用 `#e4b76f`）；wine 类用 wine（深色底用 `#a43f45`）。
- 深色底不需要另外的文件：在深色容器上设 `color:#fbf8f3`、`#e4b76f` 或 `#a43f45`。

| 文件 | 含义 | 建议页面 | 来源 |
|---|---|---|---|
| product-liquor | 商品 / 白酒瓶 | 商品列表、SKU | 原创 |
| liquor-jar | 酒坛（品牌/窖藏） | 品牌/批次 | 原创 |
| inventory-warehouse | 库存 / 仓库 | 库存菜单 | Lucide |
| purchase | 采购 | 采购单 | Lucide |
| wholesale | 销售 / 批发 | 销售单 | Lucide |
| customer-b2b | 经销商 / 企业客户 | 客户管理 | Lucide |
| reconcile | 对账 | 财务对账 | 原创 |
| stocktake | 盘点 | 盘点单 | Lucide |
| report | 报表 | 报表中心 | Lucide |
| brand-switch | 品牌切换 / 多品牌 | 顶栏品牌切换 | Lucide |
| roles | 角色权限（老板/采购/销售/仓库/财务/稽核） | 设置 | Lucide |
| ai-workbench | AI 工作台 | 侧栏入口 | 原创 |
| ai-replenish | 补货测算（每周） | ai_assist replenish | 原创 |
| ai-inbound-match | 入库对单（实时） | receiving | 原创 |
| ai-anomaly | 异常筛查（实时） | order_anomaly | Lucide |
| ai-stock-alert | 库存预警（每日） | stock_alert | 原创 |
| ai-daily-report | 日报起草（每日） | report | Lucide |
| data-catalog | 数据清单 D01–D15 | 数据目录 | Lucide |
| backtest | 回测 / 仿真 | 沙盘 | 原创 |
| params-recalc | 参数调整 / 重算 | 沙盘参数 | Lucide |
| auto-exec | 自动执行（低风险，可关） | execution_mode=auto 标记 | Lucide |
| human-approve | 人工复核 / 拍板 | 审批按钮、待办 | 原创 |
| ai-to-human | AI → 人 交接 | 建议卡片“交给我” | 原创 |
| explain-basis | 依据 / 可解释 | 建议卡片“为什么” | Lucide |
| update-cycle | 更新周期 | 工作流卡片 | Lucide |
| risk-boundary | 风险 / 适用边界 | 建议卡片底部 | Lucide |

## 2. 品牌标 `brand/`（原创，不仿任何真实酒企）

| 文件 | 用途 |
|---|---|
| `dejian-seal.svg` / `-flat.svg` | 德鉴印章标（酒红，带/不带错位投影）；登录页、关于页 |
| `dejian-lockup.svg` | 浅色顶栏 / 侧栏组合标 |
| `dejian-lockup-dark.svg` | 深色侧栏 / Hero 组合标（印 `#a43f45`，字米白，副标暗金） |
| `dejian-favicon.svg` / `-dark.svg` | favicon（「鉴」） |
| `demo-seal.svg` / `demo-lockup.svg` / `demo-lockup-dark.svg` / `demo-favicon.svg` | 中性「演示酒业」，用于路演或公开演示数据 |

所有品牌标都有 `png/*@2x.png`。

## 3. 插画 `illustrations/`（6 张，浅色 + 深色）

| 文件 | 用途 |
|---|---|
| `empty-no-todo.svg` | 待办空状态（Nil. 无待拍板事项） |
| `empty-no-anomaly.svg` | 异常筛查空状态（AI 已筛完，暂无异常订单） |
| `login-hero.svg` | 登录页右侧（矢量版；位图主视觉见 hero/） |
| `ai-human-flow.svg` | AI 起草 → 你拍板 → 草稿单（首页说明、引导） |
| `backtest-compare.svg` | 沙盘回测：可售天数目标带，AI 线 vs 人工基线（演示假设） |
| `multi-brand.svg` | 租户 → 品牌 → 仓库/渠道（多品牌说明） |

- 深色版本在 `illustrations/dark/*-dark.svg`。它们由 `_build/dark.py` 按色值映射生成：底色 `#211b18`，卡片 `#2d2523`，墨色转米白，金色转 `#e4b76f`，酒红转 `#a43f45`。
- PNG @2x 在各自的 `png/` 目录下。

## 4. 图表 `diagrams/`（1600×900，路演 PPT 用）

| 文件 | 内容 |
|---|---|
| `01-business-flow` | 业务流程：人工现状 vs AI 赋能（同一条链路，AI 算数/对表/筛异常/起草，人拍板） |
| `02-data-flow` | 数据流与数据清单（D01–D15 → 处理 → AI 建议 → 人审批） |
| `03-human-ai-split` | 人机分工：AI 可做 / 人必须做 / 红线 |
| `04-architecture` | 系统架构（Django IOE 二开 + tenancy + ai_assist） |

- `diagrams/*.svg` 的文字已转成路径，任何环境下显示一致。
- `diagrams/editable/*.svg` 保留可编辑的 `<text>`，需要 Noto Serif/Sans SC 和 IBM Plex Mono 字体。
- `png/*@2x.png` 是 3200×1800。
- 图中没有真实来源的数字，一律标注「演示假设」。

## 5. 主视觉位图 `hero/`（原创生成，酱香·厚重感）

| 场景 | 建议位置 | 文件 |
|---|---|---|
| 老木桌 + 木格窗 + 竹影 + 酒瓶礼盒 + 印章 | 首页 Hero（左侧 55% 留暗，放标题） | `desk-bottle-1920.webp/png`，**`desk-bottle-dejian-*`（瓶标「德鉴」）** |
| 陶坛酒窖 + 窗光 | 登录页（左侧暗区放表单） | `cellar-jars-*` |
| 账本 + 算盘 + 印泥 + 酒杯 | 数据目录 / 关于 / 沙盘封面 | `ledger-flatlay-*` |

- 每个场景有三种尺寸：`-1920.{webp,png}`（1920×1080）、`-1280.{webp,png}`（1280×720）、`-crop-1280x960.webp`（4:3 主体裁切，适合登录页侧栏）。
- 建议用 webp（120–320 KB）。
- 1920 版是从 1280 原图放大 1.5 倍得到的，全屏铺满时略软，可以叠一层暗色渐变来遮。
- 版式参考见 `preview.png` 第 05 节：
  - 标签用等宽大写暗金 `#e4b76f`（例如 `BAIJIU OPERATING SYSTEM`）
  - 标题米白，重点词 `#a43f45`
  - 主按钮 `#6e1f2c` 实心胶囊
  - 次按钮米白描边
  - 左侧加从 `#211b18` 70% 到 0 的渐变
- 瓶标和礼盒是空白的，或只有「德鉴」二字，没有任何真实品牌字样。

## 重新生成

```bash
cd design-assets/_build
/workspace/.venv-svg/bin/python build_all.py   # 依赖 cairosvg, fonttools, pillow
```

- 会重建图标、品牌标（含深色版）、插画（含深色版）、图表（转路径版 + 可编辑版）、所有 PNG @2x，以及 `preview.png`，并逐个检查 SVG 能否渲染。
- hero/ 只在缺文件时重建（`python hero.py`）。
- 配色常量在 `_build/art_common.py`，深色映射在 `_build/dark.py`。
