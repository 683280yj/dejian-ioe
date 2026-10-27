# CODEX_B — 前端 / UX / AI 工作台 / 德鉴试点配置

工作目录：`~/Downloads/dejian-ioe/_wt/codex-b`　分支：`codex-b`（从 `main` 拉出）　本地端口：8002
先读：`AGENTS.md`、`PLAN.md`、`docs/DESIGN_SPEC.md`。

## 范围
按编辑风设计规范重做 IOE 界面（Django 模板 + 静态资源，不引入 React/Next）、租户/品牌切换器、AI 工作台各页面、德鉴试点种子数据与配置、文档。

## 你拥有的文件（只改这些）
- `inventory/templates/**`、`inventory/static/**`（含 `app.css`、`app.js`、`vendor/`）、`inventory/templatetags/**`
- `ai_flows/templates/**`（A 建 app，你写页面模板）
- `pilots/**`（新建：`pilots/dejian/` 种子数据 JSON/YAML、品牌图、配置；`pilots/management/commands/seed_pilot.py`）
- `docs/**`（`docs/DESIGN_SPEC.md` 已放好，可按 Django 实现补充）、`README_DEJIAN.md`
- `scripts/**` 里的前端冒烟脚本、`inventory/tests/test_frontend*.py`、`pilots/tests/`

## 禁止
- 模型、迁移、视图、URL、settings、requirements（A 的地盘）。页面缺数据 → 在 COORDINATION.md 写"需要 A 在 X 视图传 Y"
- 不复制旧项目的 Next.js/Tailwind 代码；把 `docs/DESIGN_SPEC.md` 的 tokens 翻成 CSS 变量（`--canvas #f5f2ec`、`--ink #24231f`、`--ai #5149cf`、`--human #8b1e3f`、`--coral #ef6b7a`），方角、1px hairline、衬线标题
- 不用真实德鉴客户/价格数据；对外截图用"演示酒业"
- `~/Downloads/dejian-liquor-sales` 只读参考（`src/components/editorial.tsx`、`src/components/ai/rec-card.tsx`、`src/app/(app)/ai/workbench/page.tsx` 看版式），不改它

## 视觉语义（必须遵守）
- 靛蓝 `#5149cf` 只给 AI 产出（建议、得分、差异、"AI 已对完"）；酒红 `#8b1e3f` 只给人的决定（采纳、审批、确认入库、发货、签字按钮）
- AI 卡片上必须显示"依据"（rationale）和"请你拍板"；采纳按钮文案写清结果："生成草稿采购单"，不写"自动下单"

## 第一件事（M1-b，今天）
1. `python3 -m venv .venv` 装依赖，`runserver 8002`，截图现有首页/商品/库存/收银四页存到 `docs/screens/before/`。
2. 在 `inventory/static/inventory/styles/` 加 `editorial-tokens.css`，在 `base.html` 引入，替换主色/字体/圆角/阴影，保证深浅主题和中英文不坏；截图到 `docs/screens/after/`。提交 `[B] ui: 编辑风 tokens`。
3. 在 `base.html` 顶栏预留"租户 · 品牌"切换器（先静态占位，等 A 在 COORDINATION.md 公布 context 后接上）。
4. 写 `pilots/dejian/seed.yaml`：德鉴租户、2–3 个品牌、2 个仓、3 个渠道、6 个角色账号（密码从环境变量读，不写死）、10–20 个白酒 SKU（香型/度数/容量/年份/箱规/价格）。`seed_pilot` 命令等 A 的 M1 模型合进 main 后再写。

## 完成定义
测试全绿；页面在 1440 和 390 宽度下不破版；AI/人颜色语义正确；截图更新到 `docs/screens/`；COORDINATION.md 记录了完成项和对 A 的数据需求。
