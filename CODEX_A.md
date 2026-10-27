# CODEX_A — 后端 / 数据 / AI 服务层

工作目录：`~/Downloads/dejian-ioe/_wt/codex-a`　分支：`codex-a`（从 `main` 拉出）　本地端口：8001
先读：`AGENTS.md`、`PLAN.md`。

## 范围
多租户底座（Tenant→Brand→Warehouse/Channel、Membership 角色）、数据隔离、权限、To B 交易模型（采购单/企业客户/批发订单/应收应付）、AI 服务层与 API、支付宝 Python 移植。

## 你拥有的文件（只改这些）
- 新 app：`tenancy/`、`trade/`、`ai_flows/`（**除了** `ai_flows/templates/`）、`payments/`
- `inventory/models/**`、`inventory/migrations/**`、`inventory/services/**`、`inventory/permissions/**`、`inventory/exceptions/**`
- `inventory/views/**`、`inventory/views*.py`、`inventory/urls.py`、`inventory/forms/**`、`inventory/forms*.py`（视图负责租户过滤和给模板传 context）
- `inventory/settings.py`、`project/settings.py`、`inventory/test_settings.py`、`requirements.txt`、`Dockerfile`、`docker-compose*.yml`、`docker/**`、`.env.template`
- 测试：`inventory/tests/test_tenancy_*.py`、`tenancy/tests/`、`trade/tests/`、`ai_flows/tests/`、`payments/tests/`，以及因你改模型而必须修的既有测试
- `NOTICE.md`、根目录误提交的 `product_form.html / product_list.html / product_response.html`（可删）

## 禁止
- `inventory/templates/**`、`inventory/static/**`、`ai_flows/templates/**`、`pilots/**`、`docs/**`（B 的地盘）
- `~/Downloads/dejian-liquor-sales` 只读参考：`src/lib/ai-decision.ts`、`src/lib/ai-service.ts`、`src/lib/order-state.ts`、`src/lib/alipay/*`。读来移植成 Python，不改原文件
- 支付宝：只移植已有能力（网站支付下单、查询、退款、异步通知验签、金额换算、状态映射），按支付宝官方 SDK/文档实现，不自造接口，不碰签约

## 关键设计
- `tenancy.models`：`Tenant`、`Brand(tenant)`、`Warehouse(tenant)`、`Channel(tenant)`、`Membership(user, tenant, role, brands M2M 可空=全部, warehouses M2M 可空=全部)`；角色 `owner/purchaser/sales/warehouse/finance/auditor`
- `TenantScopedModel` 抽象基类 + `TenantManager.for_request(request)`；中间件把 `request.tenant`、`request.membership` 挂上（来自 session 里选中的租户且用户必须是成员）
- 业务表全部加 `tenant`（非空）；`Product` 加 `brand`；`Inventory` 改成 `(product, warehouse)` 唯一；迁移把存量数据放进"默认租户/默认品牌/默认仓库"
- `ai_flows`：`AISuggestion` 模型（见 PLAN §2），`services/` 每条流程一个模块（`replenishment.py`、`receiving_match.py`、`order_screening.py`、`stock_alert.py`、`reconciliation.py`、`report_draft.py`），纯函数计算 + 落库；`adopt()` 只生成草稿/任务；LLM provider 接口可空实现
- JSON API（给 B 的页面用）：`/api/ai/suggestions/`（列表，按 flow/brand 过滤）、`/api/ai/suggestions/<id>/adopt|dismiss`（需对应角色）；接口格式写到 COORDINATION.md

## 第一件事（M1-a，今天）
1. `python3 -m venv .venv` 装依赖，跑现有测试，把结果（通过数/失败数）写进 COORDINATION.md。
2. 加 `NOTICE.md`；删根目录三个误提交 HTML。提交 `[A] chore: NOTICE + 清理误提交文件`。
3. 建 `tenancy` app：Tenant/Brand/Warehouse/Channel/Membership + 中间件 + `TenantScopedModel`；先给 `Product`、`Category`、`Supplier`、`Inventory` 接上 tenant/brand/warehouse，写迁移和"租户 A 看不到租户 B"测试。
4. 在 COORDINATION.md 公布：模板里可用的 context 变量（`request.tenant`、`current_brand`、`brands`）和品牌切换的 URL，让 B 做切换器。

## 完成定义（每个里程碑）
测试全绿；新增隔离测试和"AI 不越权"测试；迁移可在空库和旧库上跑通；无密钥；COORDINATION.md 记录了做完的事、接口变化和给 B 的待办。
