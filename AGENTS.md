# AGENTS.md — 德鉴 × IOE 二开（所有 Codex/AI 代理必读）

项目根：`~/Downloads/dejian-ioe`（基于 zhtyyx/ioe，MIT）。总方案见 `PLAN.md`，设计规范见 `docs/DESIGN_SPEC.md`。
德鉴是首批体验企业（pilot tenant）；产品面向多品牌、多企业的 To B 客户。公司名一律写「德鉴」。

## 你在哪里干活
- Codex A 只在 `~/Downloads/dejian-ioe/_wt/codex-a`（分支 `codex-a`）里改代码，任务书 `CODEX_A.md`。
- Codex B 只在 `~/Downloads/dejian-ioe/_wt/codex-b`（分支 `codex-b`）里改代码，任务书 `CODEX_B.md`。
- 根目录 `~/Downloads/dejian-ioe`（`main`）只读；唯一可写的是共享文件 `~/Downloads/dejian-ioe/COORDINATION.md`（只追加，不改别人的条目）。
- **停止修改 `~/Downloads/dejian-ioe` 以外的任何目录**，尤其是 `~/Downloads/dejian-liquor-sales`（旧项目，只读参考）。

## 硬规则
1. 只改自己任务书里"拥有"的文件；要动对方的文件 → 在 COORDINATION.md 提请求，等对方做。
2. `rm -rf` 只能用于自己拥有的目录内；禁止对仓库根、`~`、`~/Downloads`、`.git` 执行删除。不 `git push --force`，不改写 `main`，不 `git reset --hard` 别人的提交。
3. 不提交密钥：`.env*`、`*.pem`、`*.key`、支付宝/阿里云/LLM 的 key、真实客户数据。示例只放 `.env.template`。
4. 不推送到 `upstream`（zhtyyx/ioe），不开远程 PR；只在本地分支提交。合并到 `main` 由 Riep 决定。
5. 产品铁律：AI 只出建议/草稿/差异清单，**不能**审批、提交、改订单或库存状态、发货、付款。写代码时要有测试守住这一点。
6. 保留 `LICENSE` 原文，不删 IOE 版权声明。
7. 依赖只装在仓库内的虚拟环境：`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`；不全局安装。
8. 每次提交前跑 `.venv/bin/python manage.py test`，必须全绿。提交信息格式：`[A] tenancy: 加 Tenant/Brand 模型` / `[B] ui: 编辑风 tokens`，小步提交。

## 运行
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.template .env   # 填本地 SECRET_KEY，DEBUG=True；.env 不提交
.venv/bin/python manage.py migrate && .venv/bin/python manage.py runserver 8000   # A 用 8001，B 用 8002，避免端口冲突
.venv/bin/python manage.py test
```
