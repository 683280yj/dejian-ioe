# 筹策代码规范检查报告（只读审计）

- 时间：2026-10-28
- 对象：`~/workspace/chouce-20261028/work/dejian-ioe`（Django）、`~/workspace/chouce-20261028/work/chouce-site`（官网静态站）
- 标准：仓库 `AGENTS.md` 硬规则 + 交接遗留项 + 通用规范
- 方法：源码审读、grep 扫描、与交接基线包（downloads/naruto.zip 内 dejian-ioe-code.tgz）逐文件 diff、`makemigrations --check --dry-run`。未改任何代码、未提交、未重启服务。

## 0. 基线与改动范围（先说清现状）

**生产工作树没有.git**：`work/dejian-ioe/` 下无 `.git`，`_wt/{deploy,lane-a,lane-b,lane-c}/.git` 均为指向 `/workspace/dejian-ioe/.git/worktrees/*` 的文本指针，目标不存在（悬空）。因此无法用 git status/diff 对照基线 HEAD 1ec2c9a；本次以交接包 tgz 解包到 /tmp 做只读 diff 代替。与基线相比的全部改动可枚举：

| 范围 | 文件 |
|---|---|
| 解释层（本次重点） | 新增 `ai_assist/explain.py`、`ai_assist/migrations/0002_*.py`；改 `ai_assist/models.py`（+4 字段）、`ai_assist/services.py`（+3 行钩子）、`ai_assist/hints.py`（行结构扩展）、`ai_assist/tests/test_demo_flow.py`（契约断言同步）、`inventory/templates/inventory/inventory_list.html`（依据单元格追加渲染） |
| 此前部署期改动 | `inventory/static/inventory/styles/dejian.css`、`inventory/templates/inventory/base.html`、`inventory/templates/registration/login.html`（品牌化 + CSRF 防复发） |
| 无变化 | `requirements.txt` 与基线一致 |

## 1. 发现清单

### F1生产工作树无版本控制，AGENTS.md 工作流无从执行
- 证据：`work/dejian-ioe/` 无 `.git`；`_wt/deploy/.git` 内容为 `gitdir: /workspace/dejian-ioe/.git/worktrees/deploy`，该路径不存在，`git status` 报 `fatal: not a git repository`。
- 影响：AGENTS.md 第 2/4/8 条（分支工作、只在本地分支提交、提交前跑测试并小步提交）全部无法执行；所有改动无回滚点、无审计轨迹，本次审计只能靠交接包人工 diff。
- 整改：从交接包/团队仓库恢复 `.git` 到工作树根，确认 HEAD 后把现有改动按条归档提交。

### F2SECRET_KEY 硬编码默认值仍在代码里
- 证据：`inventory/settings.py:18` — `SECRET_KEY = os.environ.get('SECRET_KEY', 'p5k!d@$v_...')`（默认值是一串完整字面量密钥，已随交接包在团队内扩散）。
- 现状：生产靠 `dejian-showcase/*.env`（权限 600，含 SECRET_KEY）覆盖，当前未被触发；但 env 一旦缺失/改名，应用会静默启用这把已知密钥启动，无任何告警。
- 整改：默认值改为空/随机生成并在缺失时启动失败；该字面量按已泄露处理。

### F3解释层 LLM 调用位于数据库事务与同步请求之内（潜伏，配 key 后激活）
- 证据：`ai_assist/services.py:49` `run_workflow` 带 `@transaction.atomic`；其内部（diff +3 行处，objs 保存后）调用 `explain.fill_run_explanations(objs)`；`ai_assist/views.py:70-73` 的 `refresh`（POST）同步调用 `run_workflow`。`ai_assist/explain.py:186-193` 的 `fill_run_explanations` 串行逐条调 `ensure_explanation(allow_llm=True)`，上限 20 条；`explain.py:151` 单次 HTTP 超时 20s。
- 影响：配齐 `AI_API_*` 后，一次刷新最坏 20×20s 在打开的事务里同步等待外部网络；体验库是 SQLite，长写事务会锁库，请求大概率先被 gunicorn 超时杀掉并回滚整轮测算。当前两套 env 均未配 `AI_API_KEY/AI_API_BASE/AI_API_MODEL`（仅 showcase.env 有 `AI_EXPLAIN_ENABLED=1`），LLM 分支处于未激活状态，所以尚未发生。
- 整改：解释生成移出事务（`transaction.on_commit` 后执行）或改异步/管理命令补生成；同时下调单条超时与 cap。

### F4requirements 未锁定 Django 版本
- 证据：`requirements.txt:1` — `Django>=4.2.0`（无上限、无 lock 文件），且文件与交接基线一致，即遗留项一直未处理。
- 影响：本机 venv 实际装的是 Django 6.1.2（超出基线预期 5.2 LTS），交接期已出现 2 个 i18n 测试失败与版本相关；任何重装都可能再跳大版本。
- 整改：锁定 `Django==5.2.x`（或团队确认的目标版本）并在该版本下复测全量测试。

### F5sales.py 的 print 残留未清（35 处）
- 证据：`inventory/views/sales.py` 共 35 行含 `print(`，如 `:140` `print(f"原始价格字符串: '{raw_price}'...")`、`:151/:159/:168` 打印商品价格、数量、小计、库存不足信息。
- 影响：交接遗留项未完成；销售业务数据持续写 stdout/服务日志，属信息暴露面 + 无效开销。
- 整改：整文件替换为 logging 或直接删除调试输出。

### F6GET 读路径里写库（解释层）
- 证据：`ai_assist/hints.py:51-56`（`inventory_context`）在库存列表 GET 上下文构建时，对无解释的建议调用 `ensure_explanation(s, allow_llm=False)`，后者 `ai_assist/explain.py:180-184` 执行 `s.save(update_fields=[...])`。
- 影响：读请求产生写事务，违反 GET 幂等预期；并发打开页面会重复生成、互相覆盖（结果确定性相同，实际危害低）；另外 `rule_explain`（`explain.py:83`）里访问 `s.product` 会逐条再查一次库，与 hints 已做的 `Product.objects.in_bulk` 优化相抵，列表页每条建议多一次查询 + 一次写。
- 整改：页面侧只读展示已有解释；缺失时返回空，生成统一放测算完成/定时任务路径。

### F7解释层两处静默吞错、无日志
- 证据：`ai_assist/explain.py:158-159` `except Exception: return None`；`:192-193` `except Exception: continue`。ai_assist 全包无 logging 使用。
- 影响：LLM 端点长期故障、返回格式漂移等只会表现为「一直是规则解释」，无人可见。
- 整改：至少 `logging.getLogger(__name__).exception(...)` 记录降级原因与次数。

### F8LLM 提示词与代码自相矛盾：anomalies 字段被丢弃
- 证据：`ai_assist/explain.py:124-128` 的系统提示词要求返回 `{"explanation":..., "anomalies": [...]}`，但 `:148-153` 只取 `parsed['explanation']`，anomalies 从不读取；实际落库的异常来自规则检出（与模块 docstring 口径一致）。
- 整改：提示词删掉 anomalies 要求，省 token 且避免误导维护者。

### F9第三方 LLM 数据面：经营数据随请求外发
- 证据：`ai_assist/workflows/replenish.py:131-134` 组装的 inputs 含 `采购价`、`售价`、`供应商`（名称）、在库/在途；`explain.py:135-142` 将 inputs/values/rationale 原样放入请求体发往 `AI_API_BASE`。
- 现状：功能未配 key、未激活；且由运维自选端点，属设计内行为。
- 整改：正式接 LLM 前确认服务商数据政策；或对供应商名做代号化、价格做区间化后再发送。

### F10解释层新功能无单元测试
- 证据：`ai_assist/tests/` 仅 `test_algorithms.py`、`test_demo_flow.py` 两文件；与 explain 相关的只有 `test_demo_flow.py:61` 更新后的行键契约断言。`detect_anomalies / rule_explain / llm_explain 回退 / ensure_explanation 幂等与只写 ai_* 字段` 均无覆盖。
- 背景：AGENTS.md 规则 5 要求「写代码时要有测试守住」产品铁律；解释层目前的合规靠代码审读成立（见第 3 节），没有回归锁。
- 整改：补 explain 单测：异常检出分支、LLM 失败回退、enabled=0 时零写入、save 的 update_fields 不含业务字段。

### F11解释徽标硬编码中文，与页面双语口径不一致
- 证据：`inventory/templates/inventory/inventory_list.html:41` 新增片段中 `AI 解释`/`一句话解释` 为硬编码中文；同页其余文案均走 `{% if request.LANGUAGE_CODE == 'en' %}` 双语分支。
- 影响：英文界面下该处仍显示中文；原有采纳/忽略按钮与行为经 diff 核对未变。
- 整改：按同页模式补英文分支。

### F12官网登录入口为明文 HTTP + 裸 IP
- 证据：`chouce-site/site-config.js` — `loginUrl: 'http://159.138.136.40:8318/accounts/login/'`。
- 影响：官网所有「登录系统」按钮跳到未加密的登录页，凭据链路明文（与已知待办「域名+HTTPS 未做、`COOKIE_SECURE=0`」为同一问题）。
- 整改：上域名 + HTTPS 后改此项为 https 地址，并同步打开 COOKIE_SECURE。

### F13官网配置 7 项仍为空，页脚主体/备案缺失
- 证据：`site-config.js` 中 `companyName / bookingUrl / email / phone / icp / police / policeCode` 均为空字符串（仅 loginUrl 已填）。
- 影响：按文件头注释逻辑，空项不显示——页脚无公司全称与 ICP/公安备案信息，「预约产品讲解」按钮降级为页内提示。属待甲方信息，非代码缺陷，但公网运营前应闭环。
- 整改：拿到甲方信息后一次填齐。

### F14fx.js 粒子动画在首屏滚出后仍持续运行
- 证据：`chouce-site/assets/js/fx.js:75-79` 仅在 `visibilitychange`（标签页隐藏）时暂停 rAF；hero 滚出视口后粒子仍逐帧绘制（上限 70 粒、DPR≤1.5，开销不大但无必要）。其余实现规范：scroll 用 rAF 节流 + passive 监听、tilt 仅 `(pointer: fine)` 启用且 mouseleave 复位、reduced-motion 直接跳过动效部分。
- 整改：加 IntersectionObserver，hero 不可见时暂停。

## 2. 交接遗留项复核

| 遗留项 | 现状 | 依据 |
|---|---|---|
| SECRET_KEY 写死默认值 | **未净**：生产 env 已换随机值且文件 600，但代码默认值仍在 | F2 |
| sales.py print 残留 | **未清**：35 处 | F5 |
| 报表中心汇总未加企业过滤 | **主体已闭环**：充值报表已显式按企业过滤（`inventory/services/report_service.py:365-384,431`，视图 `views_report.py:286,306` 传 tenant）；其余报表方法（get_sales_by_period 等）无显式 tenant 参数，但 Sale 等模型默认管理器为 TenantManager（`inventory/models/sales.py:16`）且 `tenancy.middleware.TenantMiddleware` 在 MIDDLEWARE 中，Web 请求内自动按当前租户过滤。残余脆弱点：脱离请求上下文（脚本/定时任务）调用这些方法会跨企业全量汇总，`get_operation_logs`（report_service.py:448）同样无 tenant 参数 | 本节核对 |
| requirements 锁 Django | **未做** | F4 |

## 3. 本次解释层改动专项结论

**结论：符合产品铁律与租户隔离，可以保留试点；有 2 项风险需在接 LLM 前整改（F3、F6）。**

逐项核对：

1. **不越界写入**：`ensure_explanation`（explain.py:168-185）只写 Suggestion 自身的 `ai_explanation / ai_anomalies / ai_source / ai_generated_at` 四个字段，且用 `update_fields` 限定；不改 status、不调用 adopt/reject、不触碰订单、库存、发货、付款。异常标记与解释均为纯展示数据。
2. **原有写流程未被削弱**：采纳仍走 `services.adopt`（用户 POST + `user_can` 角色校验 + 只生成 DRAFT 采购单，`services.py:110-144`，供应商/商品查询均带 `tenant=sug.tenant`）；`services.py` 的改动仅在测算落库后追加一个解释生成钩子（diff +3 行）。
3. **租户隔离成立**：解释的输入对象全部来自已按租户过滤的查询链——`hints.latest_run` 显式 `tenant=tenant` 过滤（hints.py:7-10），`restock_suggestions` 按该 run 取建议（hints.py:13-20），模型默认管理器为 TenantManager（models.py:100）；explain.py 本身不发起任何查询，不存在跨租户读取或写入路径。
4. **读路径无外部网络调用**：页面路径调用 `ensure_explanation(allow_llm=False)`（hints.py:55），规则解释与异常检出均为本地纯计算；LLM 仅可能在测算（POST /ai/refresh/ 触发的 run_workflow）时调用，单次超时 20s（explain.py:151），返回经 JSON 结构与长度校验（:148-153），失败自动回退规则解释。唯一问题是调用位置在事务内（F3）与读路径写库（F6），属性能/规范问题，不属越界。
5. **模板渲染安全**：`{{ s.explain}}`、`{{ a.text}}` 走 Django 自动转义（inventory_list.html:41，无 `|safe`），LLM 自由文本无法注入 HTML；采纳/忽略按钮及原有行为经 diff 核对未变。
6. **试点隔离正确**：`AI_EXPLAIN_ENABLED=1` 只出现在 `dejian-showcase/showcase.env`（权限 600）；`main.env` 未配该开关，主系统上解释层处于关闭态（hints 仍返回新键但为空值）。两套 env 及仓库内均未检出真实 API 密钥（LLM 三项配置均未设置）。

## 4. 其他正向确认

- 迁移与模型一致：`makemigrations --check --dry-run`（showcase_settings）输出 `No changes detected`（另有一条与本次无关的 staticfiles.W004 目录不存在警告）。
- 官网引用完整性：index.html / 404.html / credits.html 的全部本地 src/href 均能落到现存文件，无失效引用；`assets/js/{main,fx}.js`、`assets/calc.js`、`site-config.js` 中未检出任何密钥/令牌字样。
- 仓库内未发现 `.env*` 文件；全仓 grep 未检出硬编码真实凭据（F2 的 SECRET_KEY 默认值除外）。
