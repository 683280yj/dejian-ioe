# 德鉴 · 设计与开发规范（Editorial Archive 版）

> 注：本规范最初为 Next.js + Tailwind 版写成。在 dejian-ioe（Django 模板）中，把 §1 tokens 实现为 CSS 变量，组件名作为版式参考，不照搬 TS 代码。

> 版式参考：StyleKit · [Editorial Profile Archive](https://www.stylekit.top/templates/editorial-profile-archive)。
> 一句话：**AI 结果用靛蓝，人的决定用酒红，其余部分保持纸面和衬线。**

## 0. 产品叙事（所有页面都要遵守）

- AI 负责重复活：算数、对表、筛异常、起草建议。**人负责拍板和执行**：审核、稽核、发货、签约。
- AI 不自动审核、不自动发货、不自动下单。"采纳"只会生成**草稿订单**或**跟进任务**。
- 文案用第二人称、动词开头："请你拍板""你的下一步"。

## 1. Design Tokens（`tailwind.config.ts`）

| Token | 值 | 语义 |
|---|---|---|
| `canvas` | `#f5f2ec` | 页面底色（暖纸） |
| `stone` | `#ebe7dc` | 分区底色、激活态 |
| `sheet` | `#fbfaf7` | 卡片、表格、表单 |
| `ink` | `#24231f` | 正文与深色分区。**禁止纯黑 #000** |
| `ai` | `#5149cf` | **只用于 AI 产出**：信号、得分、"AI 已对完的表" |
| `brand-600` | `#8b1e3f` | **只用于人的决定和执行**：采纳按钮、拍板提示、当前导航 |
| `coral` | `#ef6b7a` | 状态点、编号、plate 投影 `6px 6px 0` |
| `line` | ink/10–15 | 1px hairline 分隔 |

- 四个决策档对应的 plate 渐变：`buy` 酒红/靛蓝，`hedge` 杏/粉，`observe` 青/米，`defer` 灰/墨。代码里一律小写，展示时用 `BUY_REPLENISH / HEDGE_LOCK / OBSERVE / DEFER_HOLD`。

## 2. 字体（`src/app/layout.tsx`，通过 next/font 加载）

- `font-display`：Instrument Serif，用于拉丁字母和数字（KPI、金额、日期、斜体强调词如 *only* / *decisions*）。
- 中文衬线用 Noto Serif SC，`h1–h4` 字重 600。
- `mono-label`：IBM Plex Mono，10px，大写，`tracking-[0.14em–0.2em]`。用于编号、面包屑和标签。
- 字号阶梯：Hero `clamp(44px,6vw,84px)`，页标题 30px，分区标题 32–40px，正文 14–15px，行高 `leading-7` 及以上。

## 3. 栅格与编号

- Hero：`lg:grid-cols-[minmax(0,0.82fr)_minmax(420px,1.18fr)]`。
- 分区：`lg:grid-cols-[0.32fr_0.68fr]`，左侧放 `SectionLabel no="01"` 和标题。
- 列表/文章：`md:grid-cols-[4rem_minmax(0,1fr)_13rem]`，依次是编号、正文、plate。
- 动态行：`grid-cols-[4.5rem_minmax(0,1fr)_auto]`。
- 分区编号统一写成 `01 / 标题`。侧栏分组、AI 导航标签、卡片序号都沿用同一套编号。

## 4. 组件

| 组件 | 位置 | 要点 |
|---|---|---|
| `AuraFrame` | `components/editorial.tsx` | 四角各一个 L 形角标，右下加一个 coral 点；用于资料卡和登录框 |
| `SectionLabel` | 同上 | `no` 加标题，coral mono |
| `ArrowLink` | 同上 | mono 按钮 + ArrowUpRight 图标；有 `primary / secondary / light` 三种 |
| `RecCard` | `components/ai/rec-card.tsx` | 编号、档位码、标题、"请你拍板"引用、4 格 KPI、AI 信号条（靛蓝），右侧"你的下一步"（酒红 CTA）+ PLATE 得分 |
| `PageHeader` | `components/ui.tsx` | 30px 衬线标题，副标题写清"人做什么"，`border-b` |
| `StatCard` | 同上 | 用 display 数字，mono 标签 |
| `AiNav` | `components/ai-nav.tsx` | 带编号的下划线 tabs（`role=tablist`，当前项 `aria-current`） |
| `Empty` | 同上 | 衬线 "Nil." 加一句引导 |

## 5. Do / Don't

- ✅ 方角，用 1px hairline，留白要大，标题用衬线，数字用 display 字体。
- ✅ 颜色要承担语义：靛蓝表示 AI，酒红表示人。新功能先想清楚它属于哪一方。
- ❌ 不用 `rounded-xl` 和 `shadow-md`。唯一允许的投影是 plate/logo 的 coral 硬投影。
- ❌ 不用纯黑、不用渐变按钮、不用 emoji 图标。浅色 plate 上不要直接放白字，要放在 `bg-ink/80` 的 chip 里。
- ❌ 不写"AI 已自动下单/发货"之类的文案。
- ❌ 不用非法的 Tailwind 透明度阶（如 `ink/48`），只用 5 的倍数。

## 6. 开发约定

- **只用 Tailwind token，不写裸 hex**。新增颜色先加到 `tailwind.config.ts`。
- 字体只通过 `next/font` 加载，不引外链 CSS。
- 可访问性：可交互元素都要有 `focus-visible:outline`；tabs 用 `role=tablist/tab`，当前导航用 `aria-current="page"`；正文对比度 ≥ 4.5:1。
- 动效：只用 opacity/transform 过渡，时长 ≤ 200ms，并遵守 `motion-reduce:transition-none`。
- 数据：落地页 `src/app/page.tsx` 是 `force-dynamic`，直接读 Prisma 计数。**不新增或伪造 API**，AI 接口仍然是 `/api/ai/suggestions*`。
- 不改动 Alipay 签名和配置相关代码。
- **合并前的三道关卡**：
  1. `npm run build` 成功
  2. `npx vitest run` 全绿
  3. `BASE_URL=http://localhost:3100 node scripts/editorial-shots.mjs` 截图后人工过一遍首页、登录、工作台、订单、看板和移动端
