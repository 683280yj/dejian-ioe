# 资产来源与许可

| 类别 | 来源 | 许可 |
|---|---|---|
| 图标（标注 Lucide 的 16 个） | [Lucide](https://lucide.dev) `lucide-static@1.62.0`，只把 stroke-width 从 2 改成 1.5 | ISC，全文见 `icons/LICENSE-lucide.txt`；每个文件头部保留来源注释 |
| 图标（原创 10 个）、品牌标、插图、图表 | 本项目原创 | 随 dejian-ioe 仓库（MIT，保留 IOE 原作者版权声明） |
| 字体（已转成路径，SVG 里不含字体文件） | Noto Serif/Sans CJK SC、IBM Plex Mono、Instrument Serif | 均为 SIL OFL 1.1；`diagrams/editable/` 里是活字，需要本机装这些字体 |

另外查过 Tabler Icons（MIT，v3.49）和 Phosphor（MIT，v2.1）：这两套都能用，但 Lucide 已经覆盖全部通用图标，混用会让线条风格不统一，所以没有收录。
品牌标是原创的印章字标，没有参照任何真实酒企的标识（茅台、五粮液等）。

## 图标逐个来源
| 文件 | 含义 | 语义色 | 来源 |
|---|---|---|---|
| `icons/product-liquor.svg` | 商品 / 白酒瓶 | ink | 原创（本项目，MIT） |
| `icons/liquor-jar.svg` | 酒坛（品牌/窖藏） | ink | 原创（本项目，MIT） |
| `icons/inventory-warehouse.svg` | 库存 / 仓库 | ink | Lucide `warehouse` (ISC) · stroke 2→1.5 |
| `icons/purchase.svg` | 采购 | ink | Lucide `package-plus` (ISC) · stroke 2→1.5 |
| `icons/wholesale.svg` | 销售 / 批发 | ink | Lucide `truck` (ISC) · stroke 2→1.5 |
| `icons/customer-b2b.svg` | 经销商 / 企业客户 | ink | Lucide `building-2` (ISC) · stroke 2→1.5 |
| `icons/reconcile.svg` | 对账 | ink | 原创（本项目，MIT） |
| `icons/stocktake.svg` | 盘点 | ink | Lucide `clipboard-check` (ISC) · stroke 2→1.5 |
| `icons/report.svg` | 报表 | ink | Lucide `chart-column` (ISC) · stroke 2→1.5 |
| `icons/brand-switch.svg` | 品牌切换 / 多品牌 | ink | Lucide `layers` (ISC) · stroke 2→1.5 |
| `icons/roles.svg` | 角色权限 | ink | Lucide `shield-user` (ISC) · stroke 2→1.5 |
| `icons/ai-workbench.svg` | AI 工作台 | ai | 原创（本项目，MIT） |
| `icons/ai-replenish.svg` | 补货测算 | ai | 原创（本项目，MIT） |
| `icons/ai-inbound-match.svg` | 入库对单 | ai | 原创（本项目，MIT） |
| `icons/ai-anomaly.svg` | 异常筛查 | ai | Lucide `scan-search` (ISC) · stroke 2→1.5 |
| `icons/ai-stock-alert.svg` | 库存预警 | ai | 原创（本项目，MIT） |
| `icons/ai-daily-report.svg` | 日报起草 | ai | Lucide `file-pen-line` (ISC) · stroke 2→1.5 |
| `icons/data-catalog.svg` | 数据清单 | ink | Lucide `database` (ISC) · stroke 2→1.5 |
| `icons/backtest.svg` | 回测 / 仿真 | ai | 原创（本项目，MIT） |
| `icons/params-recalc.svg` | 参数调整 / 重算 | ink | Lucide `sliders-horizontal` (ISC) · stroke 2→1.5 |
| `icons/auto-exec.svg` | 自动执行（低风险） | ai | Lucide `zap` (ISC) · stroke 2→1.5 |
| `icons/human-approve.svg` | 人工复核 / 拍板 | wine | 原创（本项目，MIT） |
| `icons/ai-to-human.svg` | AI → 人 交接 | wine | 原创（本项目，MIT） |
| `icons/explain-basis.svg` | 依据 / 可解释 | ai | Lucide `book-open-text` (ISC) · stroke 2→1.5 |
| `icons/update-cycle.svg` | 更新周期 | ink | Lucide `calendar-sync` (ISC) · stroke 2→1.5 |
| `icons/risk-boundary.svg` | 风险 / 适用边界 | ink | Lucide `shield-alert` (ISC) · stroke 2→1.5 |

## 主视觉位图（hero/）

| 文件 | 来源 |
|---|---|
| `hero/_src/desk-bottle.jpg`、`cellar-jars.jpg`、`ledger-flatlay.jpg` | 本项目用 Grok Bot 图像生成工具原创生成（2026-10-27），未用任何真实品牌图片做参考 |
| `hero/*-1920.*` / `*-1280.*` / `*-crop-1280x960.webp` | 由上述原图缩放/裁切；1920 为 1.5× Lanczos 放大（原图 1280×720） |
| `hero/desk-bottle-dejian-*` | 在空白瓶标上叠加原创「德鉴」字样 + 小印（Noto Serif CJK SC，OFL），不含任何真实品牌标识 |

瓶标、礼盒均为空白或「德鉴」，不仿习酒/茅台等任何真实品牌。
