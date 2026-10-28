# 筹策系统代码对比报告：渚包 vs 鸣人包

日期：2026-10-28　范围：`extracted/zhu-code/dejian-ioe/`（下称「渚包」）vs 鸣人 `dejian-ioe-code.tgz` 解压至 `/tmp/mingren-code/dejian-ioe/`（下称「鸣人包」）。只读分析，未改任何代码。

## 结论先行

**本地部署应以鸣人包为基础，再并入渚包独有的 `dejian-showcase/` 目录。** 理由：两包的 dejian-ioe 主代码逐字节完全相同（鸣人包就是同一工作区的 git 仓库原样打包），但只有鸣人包带完整 `.git`，能看到历史、分支和那批「中途停止」的未提交修复 diff；渚包根目录无 `.git`，无法做任何 git 核对。渚包不可丢的是同级的 `dejian-showcase/`（5 个文件，含访客只读修复和体验实例配置），鸣人 tgz 里没有。另一个不可丢的是鸣人工作区里的未跟踪文件（见 §2），`git clean` 或重新 checkout 会把修复冲掉——部署前应先把未提交改动提交存档。

## 1. 目录差异清点

`diff -rq`（排除 `.venv`、`__pycache__`、`*.sqlite3`、`.git`、`_wt`）结果只有 5 行，全部是鸣人包独有：

| 独有项 | 说明 |
|---|---|
| `.env.example`、`.env.template` | 内容 identical，是同一份模板的两个名字；含 SECRET_KEY/DEBUG/ALLOWED_HOSTS 占位写法 |
| `db/`、`temp/` | 空目录 |
| `logs/inventory.log` | 1.3 MB 运行日志（无部署价值，但可佐证修复曾在本机 runserver 热重载生效过） |

- 共有文件全部字节一致：渚包 596 个文件 vs 鸣人包 599 个文件（差的就是上表 3 个文件）。关键文件 md5 抽查一致（如 `inventory/settings.py`、`inventory/views/core.py`）。
- **渚包独有 1：`_wt/`（49 MB）** —— deploy / lane-a / lane-b / lane-c 四个 worktree 快照，与主代码有 10–22 处差异是分支状态不同所致。这四个分支在鸣人包 `.git` 里都存在（deploy-vercel `9b8d298`、lane-a `6a6e61f`、lane-b `e707b5d`、lane-c `1ae98ea`），所以 `_wt` 不是独有内容，只是冗余副本。
- **渚包独有 2：同级目录 `dejian-showcase/`** —— `build_showcase_db.py`、`create_guest.py`、`reset_showcase.sh`、`showcase_settings.py`、`showcase_urls.py`。这是体验实例的部署脚本，鸣人 tgz 里完全没有，**部署时必须从渚包并入**。
- 两包都按交接说明去掉了 *.sqlite3、.env、media，数据库内容本身无法从任何一包核对。

## 2. Git 状态

### 渚包
- `dejian-ioe/` 根目录**没有 `.git`**（打包时被去掉）。
- `_wt/*/.git` 只是指针文件，指向原机器的 `/workspace/dejian-ioe/.git/worktrees/<name>`，该路径不在包内，实测 `git status` 报 `fatal: not a git repository`。即渚包无法做 log/status/diff，只能当普通文件快照用。

### 鸣人包（`.git` 完整可用）
- HEAD：`1ec2c9a`（main）。最近 5 个提交：
  - `1ec2c9a` test(i18n): 登录页英文断言兼容免密进入按钮
  - `7c3983c` feat(auth): 演示免密一键进入系统
  - `d38ce5d` feat(tenancy): 德鉴导入示例与批发/采购订单导入
  - `903503c` 去掉种子数据与界面中的来源/演示标注
  - `2548f9a` 德鉴演示案例改为通用多企业平台的展示数据
- 本地分支：main、deploy-vercel、lane-a、lane-b、lane-c（即渚包 `_wt` 对应的分支）；另有 upstream 远程分支记录。
- **未提交改动共 28 条：23 个已跟踪文件被改 + 5 个未跟踪新增**，`git diff --stat` 为 23 files changed, 74 insertions(+), 56 deletions(-)。这批就是交接文档说的「修复中途停止」的那一批（另含 b2b、replenish、i18n 等他人改动）：
  - 已改：`ai_assist/hints.py`、`ai_assist/workflows/replenish.py`、`b2b/templates/b2b/_action_label.html`、`b2b/templates/b2b/dashboard.html`、`b2b/templates/b2b/po_detail.html`、`b2b/templates/b2b/so_detail.html`、`b2b/views.py`、`inventory/services/report_service.py`、`inventory/settings.py`、`inventory/templates/inventory/barcode/template_settings.html`、`inventory/templates/inventory/base.html`、`inventory/templates/inventory/inventory_list.html`、`inventory/templates/registration/login.html`、`inventory/tests/test_i18n.py`、`inventory/views.py`、`inventory/views/barcode.py`、`inventory/views/core.py`、`inventory/views/open_access.py`、`inventory/views/product.py`、`inventory/views/sales.py`、`inventory/views_report.py`、`tenancy/templates/tenancy/import.html`、`tenancy/tests/test_import_samples.py`
  - 未跟踪新增：`ai_assist/management/commands/reset_showcase.py`、`design-assets/`、`inventory/locale/zh_Hans/`、`inventory/middleware_locale.py`（settings.py 的 MIDDLEWARE 引用了它）、`tenancy/readonly.py`（showcase 只读中间件，`showcase_settings.py` 引用了它）。这些文件两包都有（渚包是纯文件形式存在），但在 git 视角下属于「未提交」，丢了版本库或 clean 就会连带丢功能。

## 3. 上线前 9 项必修 —— 在渚包里的现状

（渚包与鸣人包工作区文件一致，以下行号在两包通用；git diff 证据取自鸣人包。）

### ① 访客 chouce_guest 权限只留 view_* —— ✅ 已修
- 证据：`dejian-showcase/create_guest.py:21-26` 只把 `codename__startswith='view_'` 的权限（inventory/b2b/ai_assist/tenancy 四个 app）授予访客，另加一个自建的 `view_reports` 查看报表权限；`:5` 角色固定 `auditor`，`tenancy/roles.py` 中 `Role.AUDITOR` 的权限映射为空列表（只读）；`:10` `is_staff=False, is_superuser=False`。
- 兜底：`dejian-showcase/showcase_settings.py` 挂了 `tenancy.readonly.ReadOnlyGuestMiddleware`，写操作会被中间件拦下。
- 注意：这个修复只存在于渚包的 `dejian-showcase/` 里，这也是渚包不能丢的核心原因。

### ② 热销商品串企业（inventory/views/core.py:64）—— ✅ 已修
- 证据：`inventory/views/core.py:64-68` 已改为先建查询、再 `top_products.filter(sale__tenant=request.tenant)`。
- 小 caveat：过滤带条件——`request.tenant` 为 None 时不加过滤。正常请求有租户中间件赋值，风险低，但与鸣人建议的无条件 `sale__tenant=request.tenant` 略有差别。

### ③ 储值汇总企业隔离（report_service.py / views.py:650）—— ⚠️ 部分修
- 已修一半：`inventory/services/report_service.py:365` `get_recharge_report(..., tenant=None)` 新增 tenant 参数，`:381-384` 按 `member__tenant=tenant` 过滤后再做全部汇总/日统计/支付方式/会员排行（排行在 `:431` 同步加了 tenant 过滤）；调用方 `inventory/views_report.py:286,306` 两处都传了 `tenant=getattr(request, 'tenant', None)`。充值报表页这条链是通的。
- 没修的一半：`inventory/views.py:650`（reports_index 的充值总金额）现在的写法是 `RechargeRecord.objects.filter(member__in=Member.objects.all())` —— 过滤条件是「全部会员」，等于没过滤，仍是跨企业汇总。git diff 显示这里只做了形式上的改动，没有真正按 `request.tenant` 隔离。**这是 9 项里最明确的未完成点。**

### ④ /api/barcode/lookup/ 500（barcode.py UnboundLocalError）—— ✅ 已修
- 原因：`barcode_lookup` 里局部变量 `inventory` 会遮蔽模块 `inventory`，使函数前面的 `inventory.models.Product` 在赋值前被引用而报 UnboundLocalError。
- 证据：`inventory/views/barcode.py:132-133` 局部变量已改名为 `inv`（`inv = inventory.models.Inventory.objects.get(...)`、`stock = inv.quantity`），`:129` 的 `inventory.models.Product.objects.get(...)` 恢复正常；模块导入在 `:9` `import inventory.models` 本来就有。
- 说明：鸣人交接里写的修法是「顶部 import Product」，实际采用的是改名方案，两者等效，500 的根因已消除。

### ⑤ open_access.py 的 next 开放跳转 —— ✅ 已修
- 证据：`inventory/views/open_access.py:7` 引入 `url_has_allowed_host_and_scheme`，`:45-48` 用它校验 POST 的 next（allowed_hosts 限定本站 host、按请求是否 HTTPS 决定 require_https），不过校验就回落到 `LOGIN_REDIRECT_URL`。原来只判 `startswith('/')` 的写法已删。

### ⑥ 商品列表 DEBUG print —— ✅ 已修（限交接指定范围）
- 证据：git diff 显示 `inventory/views/product.py` 的 product_list 里 4 处 `print(f"DEBUG: ...")`（筛选参数、初始数量、活跃筛选后数量、总/活跃/当前页数量）已全部删除；`inventory/views/sales.py` 顶部提交时整段打印 POST 数据的块也一并删了。
- 残留提醒（不在本项原始范围内）：`inventory/views/sales.py:133-242` 的 sale_create 解析路径里仍有约 20 处普通 `print()`（解析价格、库存不足、金额计算等），上线后仍会往日志输出，如需日志干净要另行清理。

### ⑦ SECRET_KEY / ALLOWED_HOSTS 去 ioe.xianist.com、HTTPS 改读环境变量 —— ⚠️ 部分修
- ✅ ALLOWED_HOSTS：`inventory/settings.py:25` 已删掉硬编码追加的 `"ioe.xianist.com"`，只剩环境变量 `ALLOWED_HOSTS` 解析（`:23`，默认 localhost,127.0.0.1）。
- ✅ HTTPS 相关：`inventory/settings.py:28-37` 新增 `_env_flag` 读取 `SECURE_SSL_REDIRECT`、`SECURE_HSTS_SECONDS/INCLUDE_SUBDOMAINS/PRELOAD`、`SESSION_COOKIE_SECURE`、`CSRF_COOKIE_SECURE`，默认全关、部署时用环境变量开。
- ❌ SECRET_KEY：`inventory/settings.py:18` 仍是 `os.environ.get('SECRET_KEY', '<一串写死的默认值>')`——虽然能读环境变量，但代码里带着一个已公开在源码中的默认密钥，部署时若忘设环境变量就会静默用这个已知密钥。交接要求是「改读环境变量」，严格说只做了一半：**上线配置必须显式设置 SECRET_KEY 环境变量，或把默认值改成空/报错**。

### ⑧ settings 安全默认值（DEBUG、DEJIAN_OPEN_ACCESS 默认关，零的改动）—— ✅ 已修
- 证据：`inventory/settings.py:21` `DEBUG = os.environ.get('DEBUG', 'False') == 'True'`（默认关，原为默认 True）；`:223` `DEJIAN_OPEN_ACCESS = os.environ.get('DEJIAN_OPEN_ACCESS', '0')...`（默认关，原为默认 '1'）。配套的两个测试更新也在未提交改动里（`inventory/tests/test_i18n.py`、`tenancy/tests/test_import_samples.py`）。
- 注意：体验实例是在 `dejian-showcase/showcase_settings.py` 里显式把 `DEJIAN_OPEN_ACCESS` 按环境变量（默认 '1'）打开、且用户换成 chouce_guest——这是体验库的预期行为，但意味着 showcase 部署时不要误把这套 settings 用到真实库。

### ⑨ 登录页等文案 —— ✅ 已修
- 登录页 `inventory/templates/registration/login.html`：`:2` 标题「登录 · 筹策」；`:5` 「快捷收银」→「补货建议」，且同行介绍文案已带筹策口径；`:14` 说明「登录筹策，管理各品牌的库存、订单、补货与供应商对账。」与薇尔方案一致；`:8` 免密说明「点击下方按钮，进入筹策体验企业。」与方案一致。
- 全站标题：`inventory/templates/inventory/base.html:9` 标题后缀 `ioe`→`筹策`，`:65` 面包屑 `ioe`→`筹策`（零的改动）。
- b2b：`b2b/templates/b2b/dashboard.html:12` 「待对账单」→「待供应商对账」，`:14`「对账确认均需人工…」→「供应商对账确认均需人工…」。
- 条码模板：`inventory/templates/inventory/barcode/template_settings.html:87,89` 「示例商品名称」→「商品名称」、「示例公司名称」→「公司名称」。
- 渚本人改的两处：`inventory/templates/registration/login.html:8`（即上面免密说明）和 `tenancy/templates/tenancy/import.html` 「示例模板（已填写）」→「参考模板（已填写）」，均在包内确认。

### 附：渚交接文档另两项（不在 9 项编号内，一并核了）
- **体验库删第二家企业 + 批发客户真名虚构化**：脚本层面已实现——`dejian-showcase/build_showcase_db.py:13-21` 有整表替换映射（含真公司名→「贵阳某酒类供应链」这类虚构名），`:30-37` 把 dejian 企业改名为 chouce 体验企业并删除其它全部企业的数据和租户行。但两包都不含数据库，**实际执行结果无法核验**；且种子源码仍是原样：`ai_assist/demo_profile.py:109` 仍有真实风格的客户全称、`ai_assist/management/commands/seed_dejian.py:362` 仍会建第二家企业——重跑 seed 就会把问题带回来，靠的是 build_showcase_db 这一步后处理兜住。
- **每晚重置体验库 + ai_refresh 定时**：命令已备——`ai_assist/management/commands/reset_showcase.py`（未跟踪新文件，两包都有）+ `dejian-showcase/reset_showcase.sh`，`ai_refresh.py` 命令早已在库中。但**每晚执行的 cron/systemd 定时配置不在任何一个包里**，部署到服务器时需要另行配置，这一项只能算「代码已备、调度未配」。

## 4. 部署取舍清单（不能丢的东西）

| 来源 | 必须保留 | 原因 |
|---|---|---|
| 鸣人包 | 整个 `dejian-ioe/`（含 `.git`） | 唯一带历史/分支/未提交 diff 的版本；主代码与渚包相同 |
| 鸣人包 | 未跟踪 5 项：`reset_showcase.py`、`tenancy/readonly.py`、`inventory/middleware_locale.py`、`inventory/locale/zh_Hans/`、`design-assets/` | 前三项被 settings/showcase 配置实际引用，clean 掉会直接报错 |
| 鸣人包 | `.env.template` / `.env.example` | 部署时生成 .env 的模板 |
| 渚包 | `dejian-showcase/` 全部 5 个文件 | 体验实例的建库、访客只读、重置脚本，鸣人包没有 |
| 渚包 | `_wt/` | 可丢：四个分支在鸣人 `.git` 里都有，指针已断的快照没有额外价值 |
| 两包都缺 | 数据库、.env、SECRET_KEY 真值、服务器定时配置 | 需按交接文档在部署环节另行准备；SECRET_KEY 必须新生成并以环境变量注入（见 ⑦） |

**部署前还剩的动作**：修 `inventory/views.py:650` 的储值汇总隔离（③）；处理 SECRET_KEY 硬编码默认值（⑦）；先把鸣人包未提交的 28 条改动提交存档，再开始部署。
