# 交接文档：dejian-ioe 项目开发与部署指南

> 写给接手开发的 AI 助手 / 新开发者。读完这一篇，你应该能独立完成：改代码 → 提交 → CI 测试 → 发布 → 部署生产 → 回滚。

## 1. 项目与仓库

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/683280yj/dejian-ioe.git |
| 技术栈 | Django 6.1.2 + PostgreSQL 16 + Nginx + Docker |
| 主分支 | `main`（所有改动都从这里走） |
| 生产环境 | 华为云 ECS，SSH 别名 `huawei-cloud`（159.138.136.40，root） |
| 生产域名 | `ioe.idky.tech`（应用）、`cc.idky.tech`（静态官网，走 Cloudflare） |

关键 App：
- `inventory/` — 商品、库存、销售、采购主业务
- `ai_assist/` — 筹策助手（AI 对话 + 补货建议 + 工具调用）← 近期开发重点
- `b2b/` — 采购单（AI 只能生成 DRAFT 草稿，不提交审批）
- `tenancy/` — 多租户（企业/角色/成员），所有业务查询必须按租户过滤

## 2. 本地开发与测试

```bash
# 本地虚拟环境（.venv 是失效符号链接，别用；用 .venv-local）
cd ~/Projects/dejian-ioe-deploy
SECRET_KEY=test-secret-key .venv-local/bin/python manage.py test ai_assist --settings=inventory.test_settings
```

- 测试必须用 `--settings=inventory.test_settings`（SQLite 内存库，不需要真数据库）
- `SECRET_KEY` 环境变量是必须的（test_settings 里有兜底，但显式给更稳）
- **改完必须跑测试**；CI 里会再跑一遍全量测试，不过关发不出镜像

## 3. 部署流程（核心！）

```
git push origin main
      ↓
GitHub Actions 自动触发（.github/workflows/publish-image.yml）
  1. 构建测试镜像
  2. 在镜像里跑 Django 全量测试（inventory.test_settings）
  3. 验证全新部署脚本
  4. 发布多架构镜像到 ghcr.io/683280yj/dejian-ioe:latest + sha tag
      ↓
生产服务器拉新镜像重启
```

生产服务器上的操作：

```bash
ssh huawei-cloud
cd /opt/dejian-ioe
docker compose -f docker-compose.huawei.yml pull   # 拉新镜像（已登录 GHCR）
docker compose -f docker-compose.huawei.yml up -d  # 重启（entrypoint 自动跑 migrate）
docker ps --filter name=dejian-ioe                  # 确认 healthy
```

注意事项：
- 生产用 `docker-compose.huawei.yml`（服务器专属，**不在仓库里**，改它要手工）；备份在同目录 `.bak`
- 生产 `.env` 在 `/opt/dejian-ioe/.env`（含 SECRET_KEY、数据库、AI_API_* 等），不要提交进仓库
- `docker-compose.prod.yml` 是通用版，镜像由 `IOE_IMAGE` 变量控制
- GHCR 登录已配好（`docker login ghcr.io -u 683280yj`，用的是 gh CLI 的令牌，**含 read:packages 权限**；如果 403，在本机 `gh auth refresh -s read:packages` 重新授权后重登）

## 4. 回滚

CI 每次发布都打两个 tag：`latest` + 完整 sha（`sha-<commit>`）。回滚：

```bash
# 方法一：把 compose 里的 image 换成旧 sha tag
sed -i 's|ghcr.io/683280yj/dejian-ioe:latest|ghcr.io/683280yj/dejian-ioe:sha-<旧commit>|' docker-compose.huawei.yml
docker compose -f docker-compose.huawei.yml up -d

# 方法二（代码回滚）：本地 revert 后推送，CI 会重新发布
git revert <bad-commit> && git push origin main
# 然后生产 pull + up -d
```

- 业务数据在 `./data/db`（Postgres 卷）和 `./data/media`，回滚应用镜像**不影响数据**
- 如果新版本带了数据迁移，回滚前想清楚要不要反向迁移（`ai_assist/migrations/` 里查）

## 5. 筹策助手（ai_assist）架构速览

```
用户对话 (base.html 悬浮窗，POST /ai/assistant/chat/)
   ↓
views.assistant_chat
   ├─ GET/DELETE：读历史 / 清空（ChatTurn 表，按企业+用户持久化，保留最近30条）
   ├─ 模型已配置（AI_API_BASE/KEY/MODEL 环境变量）→ chat_api.answer()
   │     └─ OpenAI 兼容 function calling 循环（最多3轮）
   │          工具在 ai_assist/tools.py：TOOLBOX + TOOL_SPECS
   │          ├─ 只读：query_restock_suggestions / query_stock / query_sales_summary / query_pending_drafts
   │          └─ 写（直接落库，需老板权限）：adopt_suggestions（生成采购草稿）/ create_product（录入商品）
   └─ 模型未配置/失败 → assistant.py 规则层兜底（关键词路由）
```

改助手时的铁律：
- **所有数据库查询必须按租户过滤**（`tenant=...`），工具函数签名统一 `(tenant, args, actor=None)`
- **写操作必须过权限**：`_is_boss(actor)`（企业老板或超管）；新写工具照抄 `_tool_create_product` 的模式
- `tools.execute()` 只给写工具传 `actor`（只读函数不收这个参数，传了会 TypeError——踩过坑）
- 工具执行失败返回 `{'error': ...}` 回喂模型，不要抛异常打断对话
- 改了 models 记得 `makemigrations ai_assist`

## 6. 服务器上的其他东西（别动坏）

`/opt/dejian-ioe` 同一台机器还跑着：`chouce-site`（静态官网，nginx 容器）、`edge-proxy`（Caddy 统一入口，配置在 `/opt/proxy/Caddyfile`，域名路由都在这）、postgres 容器、uptime-kuma 监控等约 17 个容器。改 Caddyfile 前先备份；磁盘曾到 85%，清理用 `docker builder prune` + 容器内 `/tmp`，别删 `dejian-ioe:local` 等在用镜像。

## 7. 常见坑（都是踩过的）

1. `.venv` 是坏的符号链接 → 用 `.venv-local`
2. 测试缺 SECRET_KEY 起不来 → 环境变量给上，或依赖 test_settings 兜底
3. GHCR 拉镜像 403 → 令牌缺 `read:packages`，重新 `gh auth refresh`
4. `serviceusage.googleapis.com` 在国内网络常连不上 → gcloud 配置走代理（`gcloud config set proxy/address 127.0.0.1` 等）
5. 生产改 compose/配置先备份（`cp xxx xxx.bak`）
6. 提交信息用 Conventional Commits（feat/fix/chore...），仓库历史全是中文描述

## 8. 待办（下一轮）

- [ ] 助手语音输入（浏览器 SpeechRecognition → 文本框）
- [ ] 小屏全屏按钮（cc-panel 增加 fullscreen 切换）
- [ ] CI 部署阶段自动化（目前 push 后要手工 SSH 拉镜像，可加 watchtower 或 workflow ssh step）
