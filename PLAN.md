# 德鉴 × IOE 二开总方案（v0.1，2026-10-27）

> 仓库：`~/Downloads/dejian-ioe`（基于 [zhtyyx/ioe](https://github.com/zhtyyx/ioe) MIT，`upstream` 指向原仓库）。
> 德鉴是**首批体验企业（pilot tenant）**，产品本身面向**多品牌、多企业的 To B 客户**，不是德鉴专用系统。
> 产品铁律：**AI 做重复活（算数、对表、筛异常、起草建议），人做决定和执行（审批、稽核、发货、签字）。AI 不自动审批、不自动下单、不自动发货。**

## 0. 基线：IOE 现状（2026-10-27 读码结论）

| 项 | 现状 |
|---|---|
| 技术栈 | Python 3.10+ / Django ≥4.2 单体；服务端模板（Bootstrap 5 + 自带 HeroUI 风格 CSS/JS、crispy-forms）；默认 SQLite（已带 psycopg2，可切 PostgreSQL）；gunicorn + Docker/GHCR |
| 认证/权限 | Django 自带 User/Group/Permission + 自写装饰器 `inventory/permissions/decorators.py` |
| 模块 | 商品/分类/规格/图片/批次/供应商、库存+流水+预警、盘点（含审批）、收银销售单（POS）、会员/等级/充值/积分、报表（销售趋势/周转/会员）、操作日志、备份恢复、中英文、深浅主题、条码（阿里云条码 API） |
| 多租户 | **无**。README 明说"按单店使用，库存和订单尚未按门店隔离"；`Store` 模型存在但没被任何表引用；`Inventory` 对 `Product` 是一对一 |
| 缺口（To B 必需） | 无采购单、无企业客户/经销商、无批发销售订单、无应收应付/对账、无多仓 |
| 代码热点 | `inventory/views.py`(751 行) 与 `inventory/views/` 包并存；`views_*.py` 旧文件与 `views/*.py` 重复；`inventory/models.py` 过渡 shim；`inventory/settings.py` 与 `project/settings.py` 两份；仓库根目录有 3 个误提交的大 HTML（`product_*.html`）；部分测试/服务里有 `print` 调试输出 |
| 许可证 | MIT：允许商用、修改、闭源分发；**必须保留原版权声明和 LICENSE 全文**（放在 `LICENSE` 与 `NOTICE.md`） |

## 1. 目标架构

```
Tenant（企业客户，如 德鉴）
 ├── Brand（品牌，一个企业可多个；德鉴=自有/代理白酒品牌）
 │     └── Product（SKU 归属品牌）
 ├── Warehouse（仓库/门店，多仓）
 │     └── Inventory（product × warehouse 唯一）
 ├── Channel（渠道：直营/经销/电商/门店）
 ├── Customer（企业客户/经销商，To B 下游）
 ├── Supplier（上游，按租户隔离）
 └── Membership（User ↔ Tenant + Role，可限定到品牌/仓库）
```

- **数据隔离**：共享库 + 行级隔离。所有业务表加 `tenant` 外键（非空）；品牌相关表加 `brand`。统一 `TenantScopedModel` 基类 + `TenantManager`，中间件从登录用户的 `Membership` 解析当前租户到 request（不信任前端传 tenant_id）。所有查询走 scoped manager；越权访问返回 404。每个模块要有"租户 A 看不到租户 B"的测试。
- **角色**（每个租户内）：`owner` 老板/管理员、`purchaser` 采购、`sales` 销售、`warehouse` 仓库、`finance` 财务、`auditor` 稽核（只读+签核）。AI 是"系统角色"，只能写 `AISuggestion`/草稿，不持有任何审批权限。
- **数据库**：开发 SQLite，试点与生产 PostgreSQL。
- **新 Django app**（与 `inventory` 平级）：`tenancy/`（租户、品牌、仓库、渠道、成员角色）、`trade/`（采购单、企业客户、批发订单、应收应付/对账）、`ai_flows/`（AI 服务层+建议记录+API）、`payments/`（支付宝，从旧 TS 项目移植）、`pilots/dejian/`（德鉴试点配置与种子数据）。
- **保留 IOE**：商品/分类/规格/批次、库存流水、盘点审批、报表、操作日志、备份、i18n、主题、条码。POS 收银和会员保留为"门店渠道"能力，不是 To B 主线。

## 2. AI 嵌入日常流程（每条：AI 做什么 / 人做什么 / 落点）

| # | 流程 | AI 做 | 人做 | 产出物 |
|---|---|---|---|---|
| 1 | 采购补货测算 | 按近 N 周销量、在途、安全库存、价格走势算建议量和决策档（`BUY_REPLENISH / HEDGE_LOCK / OBSERVE / DEFER_HOLD`），写明依据 | 采购改量、拍板；老板审批 | 采纳 → **草稿采购单**（DRAFT），不自动提交供应商 |
| 2 | 入库对单 | 三单对比：采购单 × 到货单 × 发票/送货单，标出数量/单价/批次差异 | 仓库确认实收、签收；差异由采购处理 | 差异清单 + 待办任务；库存只在人点"确认入库"后变动 |
| 3 | 销售订单异常筛查 | 筛价格低于底价、超信用额度、窜货（渠道/区域不符）、重复下单、异常大单 | 销售/稽核逐条放行或驳回 | 风险标签 + 稽核待办；订单状态不由 AI 改 |
| 4 | 库存预警 | 按仓按品牌算可售天数、临期/滞销、跨仓调拨建议 | 仓库/采购决定调拨或补货 | 预警卡 + 草稿调拨单 |
| 5 | 对账 | 支付宝流水 × 订单 × 应收，自动匹配，列未匹配/金额不符 | 财务核对、确认、签字 | 对账差异表；核销需财务确认 |
| 6 | 日报/周报起草 | 汇总销售、库存、异常、待办，起草文字（无 LLM 时用模板） | 负责人改稿、发布 | 报告草稿（DRAFT → PUBLISHED 由人点） |

统一数据结构：`AISuggestion(tenant, brand, flow, subject, band, score, inputs_json, rationale, status[NEW/ADOPTED/DISMISSED/EXPIRED], decided_by, decided_at, result_ref)`。`adopt()` 只生成草稿或任务，并写 `OperationLog`。规则计算为主（确定性、可测试，从旧项目 `ai-decision.ts` 移植）；LLM 只用于起草文字，走可替换 provider，没配 key 也能跑。

## 3. 德鉴试点（pilot tenant）

- `pilots/dejian/`：租户"德鉴"、品牌、仓库、渠道、角色账号（admin/采购/销售/仓库/财务/稽核）、白酒 SKU 种子（香型、度数、容量、年份、箱规，例：`DJ-53-500-2021` ¥1,288）、白酒专用字段（批次号、生产日期、箱/瓶换算）。
- 一条命令装好：`python manage.py seed_pilot dejian`；可重复执行（幂等）。
- 对外演示统一用"演示酒业"脱敏数据；真实德鉴数据不进仓库。

## 4. 支付宝模块移植

- 来源：旧项目 `dejian-liquor-sales/src/lib/alipay/*`（TS，`alipay-sdk`）。移植为 `payments/alipay/`（Python）。
- 只移植已有能力：电脑网站支付下单、交易查询、退款、异步通知验签、金额分/元换算、状态映射。用支付宝官方 Python SDK 或官方文档写明的签名方式，**不自造接口、不改签约流程**。
- 密钥只从环境变量/仓库外文件读取，`.env*`、`*.pem` 一律不进 git。

## 5. 里程碑

| 里程碑 | 内容 | 验收 |
|---|---|---|
| **M0 清理**（0.5 天） | 补 `NOTICE.md`；删根目录误提交 HTML；合并重复 views/settings 的计划（只做无行为变化的清理） | 原有测试全绿 |
| **M1 多租户底座** | `tenancy` app、全业务表加 tenant/brand、多仓库存、角色权限、中间件、迁移脚本（旧数据迁入"默认租户"）；UI：编辑风设计 tokens + 租户/品牌切换器 | 两租户隔离测试全过；老功能回归通过；切换品牌后列表只显示该品牌 |
| **M2 To B 交易 + AI 流程** | `trade`（采购单/企业客户/批发订单/应收）；`ai_flows` 六条流程的服务、API、工作台页 | 每条流程有单测；"采纳"只生成草稿；AI 不能改订单/库存状态的测试 |
| **M3 德鉴试点 + 支付** | `seed_pilot dejian`、支付宝下单/查询/通知/退款、对账页、Docker + PostgreSQL 部署 | 德鉴账号端到端：补货建议→草稿采购单→人审批→入库对单→批发订单→支付宝付款→对账确认 |

## 6. 全局验收清单

- [ ] `python manage.py test` 全绿；新增测试覆盖租户隔离和"AI 不越权"
- [ ] 任何人用租户 A 的账号访问租户 B 的对象 ID → 404
- [ ] 所有 AI 产出带 `rationale` 且在 UI 上用靛蓝标识；所有人类决定按钮用酒红（见 `docs/DESIGN_SPEC.md`）
- [ ] 仓库内无密钥（`git grep -nE "PRIVATE KEY|APPCODE=|SECRET_KEY="` 只命中模板/示例）
- [ ] `LICENSE` 原样保留，`NOTICE.md` 写明基于 IOE（MIT, © 2025 zhtyyx）
