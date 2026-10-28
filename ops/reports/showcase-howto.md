# 筹策体验库（showcase）本机从零跑起来：确切步骤分析

> 只读分析，2026-10-28。对象：`extracted/zhu-code/dejian-showcase/`（5 个文件）+ `extracted/zhu-code/dejian-ioe/`。
> 路径下文简称：IOE=`extracted/zhu-code/dejian-ioe`，SC=`extracted/zhu-code/dejian-showcase`。

## 0. 结论先行（最重要）

1. **`build_showcase_db.py` 不是从零生成器，是「正式库 → 体验库」的转换器**：它把一个已存在的德鉴正式库
   `/workspace/dejian-ioe/db/db.sqlite3` 整库复制后改名去商标。包里所有 `*.sqlite3` 已被剥掉，
   **直接跑它必然失败**（见 §1.2 失败点）。
2. **从零的正确链条是**：`migrate` 建空库 → `manage.py seed_dejian` 生成德鉴案例企业（数据源
   `ai_assist/demo_assets/dejian_case.xlsx` 在包里，完整可用）→ `build_showcase_db.py` 转成体验库 →
   `create_guest.py` 建只读访客 → `reset_showcase --save-snapshot` 存干净快照 → 用 `showcase_settings` 起服务。
3. 有 **3 个包外硬编码路径**必须先处理：`/workspace/dejian-ioe`、`/workspace/dejian-showcase`、
   `/workspace/dejian-design-proposal`（脚本写死，见 §1）。最省事的做法是把 IOE/SC 按原名放到
   `/workspace/` 下（拷贝或软链），而不是留在 `extracted/zhu-code/` 里硬改路径。
4. **两个包内缺失件**：① `requirements.txt` 没有 `whitenoise`，但 `showcase_settings.py` 要插入
   WhiteNoise 中间件，不补装体验实例 import 即失败；② `showcase.env` 已被剥掉，必须按 §4.2 重建
   （它须设置 `DJANGO_SETTINGS_MODULE=showcase_settings` + `PYTHONPATH`，否则 showcase 的
   settings/urls 根本不在 Python 路径上）。

---

## 1. dejian-showcase 五个文件逐个说明

### 1.1 `showcase_settings.py` — 体验实例的 Django settings（覆盖方式）

- 第一行 `from inventory.settings import *`：**整表继承主 settings**（`IOE/inventory/settings.py`），
  然后逐项覆盖。所以主 settings 的环境变量语义全部保留：`SECRET_KEY`（env，缺省是代码里的开发值，
  上线必须 env 换新）、`DEBUG`（env `DEBUG`，默认 `False`）、`ALLOWED_HOSTS`（env，默认
  `localhost,127.0.0.1`）、INSTALLED_APPS、MIDDLEWARE、TEMPLATES 等都不变。
- 覆盖项：
  | 项 | 值 | 说明 |
  |---|---|---|
  | `DATABASES['default']['NAME']` | env `SHOWCASE_DB`，默认 `/workspace/dejian-showcase/showcase.sqlite3` | 只换库文件名，引擎仍是 sqlite3（继承自主 settings 的 `BASE_DIR/db/db.sqlite3` 配置） |
  | `SESSION_COOKIE_NAME` / `CSRF_COOKIE_NAME` | `chouce_sid` / `chouce_csrf` | 与正式实例 cookie 隔离 |
  | `MIDDLEWARE` | 在 SecurityMiddleware 后插入 `whitenoise.middleware.WhiteNoiseMiddleware`；在 MessageMiddleware 后插入 `tenancy.readonly.ReadOnlyGuestMiddleware` | ⚠️ whitenoise 不在 requirements 里（见 §0.4）；只读中间件逻辑在 `IOE/tenancy/readonly.py`：对 `READONLY_USERNAMES` 名单内的用户拦所有非安全方法 POST（仅放行登录/退出/`/enter/`/切语言）并拦部分 GET |
  | `READONLY_USERNAMES` | env，默认 `chouce_guest` | 只读名单 |
  | `DEJIAN_OPEN_ACCESS` | env，**默认 `'1'`（开）** | 与主 settings 默认关相反：体验实例显式开免密；用户为 env `DEJIAN_OPEN_ACCESS_USER`，默认 `chouce_guest` — 即免密只进体验访客，不是 dj_boss |
  | ` STATIC_ROOT` / `STATIC_URL` | `/workspace/dejian-showcase/staticfiles`（写死）/ `/static/` | collectstatic 目标是写死路径，不随 SHOWCASE_DB 变 |
  | `MEDIA_URL` | `/media/` | `MEDIA_ROOT` 未覆盖，仍是主 settings 的 `IOE/media/`（包里已被剥掉，需自建目录） |
  | `ROOT_URLCONF` | `'showcase_urls'` | 见 §1.5；要求 SC 目录在 `PYTHONPATH` 上 |
  | `SECURE_PROXY_SSL_HEADER` | `('HTTP_X_FORWARDED_PROTO','https')` | 在 Caddy/nginx 反代后用 |
  | `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | env `COOKIE_SECURE`，**默认 `'1'`（开）** | ⚠️ 本机纯 HTTP 调试时 cookie 不回送、登录/CSRF 会失败，必须设 `COOKIE_SECURE=0` |
  | `SHOWCASE_SNAPSHOT` | env，默认 `/workspace/dejian-showcase/showcase.clean.sqlite3` | `reset_showcase` 快照路径 |
  | `BACKUP_ROOT` | `/workspace/dejian-showcase/backups`（写死），import 时即 `os.makedirs(..., exist_ok=True)` | 该目录的父级 `/workspace/dejian-showcase` 不存在时，**光 import 这个 settings 就会抛 FileNotFoundError** |
- 它没有覆盖 `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS`：全靠 env，这正是交接说的「DEBUG=False、新 SECRET_KEY」
  必须在 env 里落实的原因。

### 1.2 `build_showcase_db.py` — 正式库→体验库转换器（纯 sqlite3 脚本，非 Django）

- 用法（文件头）：`python build_showcase_db.py`，只用标准库 `sqlite3/shutil/sys`，不依赖 Django。
- 数据来源：**写死的源库 `SRC='/workspace/dejian-ioe/db/db.sqlite3'`**，用 sqlite 在线 backup
  复制到 `DST='/workspace/dejian-showcase/showcase.sqlite3'`。不是 fixture、不是代码生成。
- 复制后做的事：① 全表 TEXT 列按 `REPL` 替换表去商标/脱敏（公司名、习酒品牌名、真实经销商名、
  人名等 → 虚构名）；② `tenancy_tenant` 中 `code='dejian'` 的企业改成 `code='chouce'`、
  「筹策体验酒业有限公司」；③ **只留体验企业**：按 `tenant_id` 删除其它企业所有行，再循环清
  外键悬空行并 `foreign_key_check` 断言；④ 原账号全部停用（`is_active=0`、密码置 `'!disabled'`、
  去掉 staff/superuser、用户名改 `staffNN`），清权限与 session；⑤ 条码 `XJ-%` 商品图片置 NULL。
- **源数据不在包里时失败在哪**：
  - `/workspace/dejian-ioe/` 目录不存在 → `sqlite3.connect(SRC)` 抛
    `OperationalError: unable to open database file`，第一步即死。
  - 目录存在但 `db.sqlite3` 不存在 → sqlite 会**新建一个空文件**当源库，backup 出一个空库，
    替换全是 0 行，最后 `select id from tenancy_tenant where code='chouce'` 返回 None，
    `...fetchone()[0]` 抛 `TypeError: 'NoneType' object is not subscriptable`。
  - 同理，若源库里没有 `code='dejian'` 的企业（比如只跑过 migrate 的空库、或只有别的企业），
    死在同一行。所以它的隐含前置条件是：**源库必须是已经 seed/运营过、且含 dejian 企业的完整库**。

### 1.3 `create_guest.py` — 建只读体验访客（Django ORM 脚本，不是 management command）

- 做的事：取 `Tenant(code='chouce')` → get_or_create 用户 `chouce_guest`，密码取 env `GUEST_PW`，
  没有就 `secrets.token_urlsafe(9)` 随机生成；设为 active、非 staff/superuser；建 Membership
  （角色固定 `auditor`「稽核」，`tenancy.roles.sync_user_groups` 同步组）；再把该用户权限收敛为
  inventory/b2b/ai_assist/tenancy 四个 app 下全部 `view_*` 权限 + 一个自定义 `inventory.view_reports`。
  这正是交接「上线前必须修 #1（116 项权限收到只剩 view_*）」的落地文件。
- **运行方式**：文件里直接用 ORM 且无 `django.setup()`，不能 `python create_guest.py` 裸跑；
  必须在 Django 上下文里执行，例如 `manage.py shell < create_guest.py`，且 settings 须是
  showcase_settings（否则连的是主库，没有 chouce 企业，`Tenant.objects.get` 抛 DoesNotExist）。
  必须在 §1.2 之后跑（文件头亦如此写）。
- **写死副作用**：把账号密码明文写入 `/workspace/dejian-design-proposal/system-login.txt`
  （chmod 600）。该目录不存在时 `open(p,'w')` 抛 FileNotFoundError — 且发生在用户已建完之后，
  是半成品状态；跑之前先建好这个目录。

### 1.4 `reset_showcase.sh` — 每晚重置的 cron 包装（非首建工具）

- 内容仅 7 行：`cd /workspace/dejian-ioe` → `set -a; . /workspace/dejian-showcase/showcase.env; set +a`
  → `.venv/bin/python manage.py reset_showcase`。
- 它依赖：① `showcase.env`（包里已剥掉，须重建，且必须在里面把 `DJANGO_SETTINGS_MODULE`
  设成 `showcase_settings`，因为 `manage.py` 只是 `setdefault('inventory.settings')`，env 设了才覆盖）；
  ② IOE 下有 `.venv`；③ 实际干活的是 management command
  `IOE/ai_assist/management/commands/reset_showcase.py`：把体验库整体还原为 `SHOWCASE_SNAPSHOT`
  快照并跑 `ai_refresh` 重算补货建议；带 `--save-snapshot` 时是反向存快照。
  该 command 自带护栏：DB 不是 sqlite、或路径等于主库 `db/db.sqlite3`、或没配置快照路径时
  直接 CommandError 拒绝执行。
- 所以首建顺序里它只在最后一步以 `--save-snapshot` 形式（经 manage.py 直接调用）出现一次；
  shell 脚本本身是给 cron 每晚用的。

### 1.5 `showcase_urls.py` — 体验实例的 ROOT_URLCONF

- 仅 4 行：`urlpatterns = [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})] + list(inventory.urls.urlpatterns)`。
  即：**复用主项目全部路由**，只额外用 Django 自带 static serve 视图直出 `/media/`（生产由
  gunicorn 跑时 Django 不自动 serve media，这里补上；注意它不做权限校验，体验库商品图可接受）。
- 要求 `showcase_urls` 可 import ⇒ SC 目录必须在 `PYTHONPATH`（或把文件放进 IOE 根目录）。

---

## 2. 从零生成一家体验企业的数据：包里有什么

### 2.1 没有 fixtures
主树（排除 `_wt/`）内**没有任何 `fixtures/` 目录、没有任何 fixture 格式的 json/yaml 数据文件**，
`loaddata` 路线不存在。

### 2.2 可用的 seed / 生成命令（这才是从零路线）

| 路径 | 作用 | 与体验库的关系 |
|---|---|---|
| `IOE/ai_assist/management/commands/seed_dejian.py` | **核心**。`manage.py seed_dejian [--reset] [--no-ai] [--days N]`。建 `code='dejian'` 企业（品牌/仓库/渠道/用户/会员等级/经销商/团购客户/门店会员），订单来源见 §2.3，另建一个小企业 `code='demo-other'` 演示数据隔离，末尾默认跑一遍 AI 工作流（`--no-ai` 可跳） | build_showcase 的上游：它生成的 dejian 企业正是被改名为 chouce 的那一家；demo-other 会在 build 时被删除（正好对应交接 #2「体验库删掉第二家企业」） |
| `IOE/ai_assist/management/commands/reset_showcase.py` | 体验库快照保存/还原 + `ai_refresh` | 见 §1.4 |
| `IOE/ai_assist/management/commands/ai_refresh.py`、`ai_backtest.py` | 重算补货建议/回测 | reset_showcase 内部调用 ai_refresh |
| `IOE/inventory/management/commands/generate_sample_data.py` | 上游 IOE 的通用示例数据（Faker 生成分类/商品/会员/销售，无租户概念） | ⚠️ 与多租户模型脱节，**不要用它建体验库**，仅列明存在 |
| `IOE/generate_mock_data.py` | 仓库根的旧 mock 脚本（顶层脚本，非 management command） | 同上，不走这条路 |
| `IOE/b2b/demo_seed.py` | `B2BSeedMixin`：被 seed_dejian 调用，经 b2b.services 流转函数生成采购/批发演示单 | 不是独立入口，随 seed_dejian 自动执行（前提 b2b 已在 INSTALLED_APPS，主 settings 会自动探测注册） |

### 2.3 seed_dejian 的数据源（全部在包里 ✅）

- `IOE/ai_assist/case_data.py` 读取 **`IOE/ai_assist/demo_assets/dejian_case.xlsx`**（企业工作簿副本，
  含仿真销售/采购/加工三张流水表）→ 德鉴三档成品的批发出库、基酒采购、加工入库原样导入。
- `IOE/ai_assist/demo_profile.py`：租户/品牌/仓库/渠道/SKU/供应商/经销商名单 + 固定随机种子
  （`SEED=20261027`，结果可复现）+ 生成参数（`HISTORY_DAYS=550`）；习酒代理三款的销售历史和
  「表内最后一笔之后到今天」的补充订单由代码按价格/同比/季节性生成。
- 商品走与生产同一条导入链路：`IOE/tenancy/importer.py` 的 `importer.sample_dicts('products')`，
  样本源在 `IOE/ai_assist/demo_assets/import_samples/`（商品.xlsx、批发订单.xlsx、客户.xlsx、
  采购订单.xlsx、期初库存.xlsx；importer 也能在同目录读同名 .csv）；商品图片在
  `IOE/ai_assist/demo_assets/products/*.jpg`（6 张），seed 时自动挂上。
- 注意 seed 出来的账号是演示账号体系（老板/销售/仓库及别名，口令在 demo_profile.py 中，
  本报告不引值）；这些账号会在 build_showcase 时被全体停用，最终只留 chouce_guest，符合方案。

### 2.4 企业自助导入模板（运行时备选，非建库必需）

`IOE/tenancy/importer.py` + `IOE/tenancy/templates/tenancy/import.html`（导入页，5 类：
products / stock / customers / wholesale_orders / purchase_orders），
`IOE/tenancy/tests/test_import.py`、`IOE/tenancy/tests/test_import_samples.py` 是其测试。
体验库建成后若要补数据可用它，但建库不依赖它（seed 已内嵌调用）。

---

## 3. 项目入口与运行要求

| 项 | 结论 |
|---|---|
| `manage.py` | 在 **IOE 根目录** `IOE/manage.py`（只有这一个，`_wt/*` 下的是各 worktree 副本，忽略） |
| `DJANGO_SETTINGS_MODULE` 默认 | `inventory.settings`（manage.py 第 9 行 `setdefault`；`inventory/wsgi.py`、`inventory/asgi.py` 同样）。体验实例靠 env 把它改成 `showcase_settings` |
| 真正的 settings | `IOE/inventory/settings.py`。⚠️ `IOE/project/settings.py` 只是一个 12 行的残片（只有 MEDIA/BACKUP 几行、无 import 头），**不是可用 settings，不要用 `project.settings`** |
| WSGI | `inventory.wsgi:application`（Dockerfile 的 gunicorn 命令即用它）；只要 env 里 `DJANGO_SETTINGS_MODULE=showcase_settings`，setdefault 不会覆盖，gunicorn 就会跑体验实例 |
| `requirements.txt` | `Django>=4.2`、`psycopg2-binary`、`gunicorn>=21.2`、`django-bootstrap5`、`Pillow`、`django-crispy-forms`+`crispy-bootstrap5`、`requests`、`django-widget-tweaks`、`urllib3`、`openpyxl`（读 xlsx 必需）、`Faker`、`psutil`、`qrcode`。⚠️ **缺 `whitenoise`**（showcase 专需，须额外装）；sqlite 是默认库，psycopg2 本机不用 |
| Python 版本 | `Dockerfile`：`python:3.12-slim`；`PLAN.md` 写 Python 3.10+ / Django ≥4.2。**本机 python3 为 3.12.3，与 Dockerfile 一致，用系统 python3 建 venv 即可** |
| Docker 路线 | `README.docker_zh.md` 是上游 IOE 的 GHCR 镜像说明（`IOE_PORT=8000`、entrypoint 自动 migrate+collectstatic、空库起步、手动 createsuperuser）——那是**原版单机 IOE** 的玩法，不含 tenancy/showcase，**不能用它部署体验库**，仅作版本/端口参考。体验库走裸机 venv + gunicorn（与交接方案、reset_showcase.sh 的 `.venv` 假设一致） |
| 项目内规矩 | `IOE/AGENTS.md`：依赖只装仓库内 `.venv`；常用命令 `migrate` / `runserver 8000`（协作时 A 用 8001、B 用 8002 避冲突）；提交前跑 `manage.py test` |
| 包里被剥掉的东西 | 全部 `*.sqlite3`、`.env`/`showcase.env`、密钥、`IOE/media` 上传、以及 `db/`、`static/` 目录本身都不存在（见 §4 失败点） |

---

## 4. 本机从零部署体验库：分步命令草案

> 布局选择（第 0 步是全案关键）：脚本写死了 `/workspace/dejian-ioe`、`/workspace/dejian-showcase`、
> `/workspace/dejian-design-proposal` 三个绝对路径。与其逐个改脚本（任务要求不改代码），
> **推荐把两个目录按原名落到 `/workspace/`**（拷贝；或软链到 extracted 位置——但 seed 会往
> IOE 内写 db/media/logs，软链等于写回 extracted 树，自行权衡）。以下按此布局写，
> `IOE=/workspace/dejian-ioe`，`SC=/workspace/dejian-showcase`。
> 本机端口现状（2026-10-28 探测）：8000/8001/8002/8080 均空闲。建议体验实例用 **8000**
> （与 Dockerfile/AGENTS 主实例口径一致），起前用 `ss -ltn` 再确认一次；被占则换 8010，
> 下文命令同步改。

### 4.0 摆放目录与建 venv
```bash
cp -r ~/workspace/chouce-20261028/extracted/zhu-code/dejian-ioe     /workspace/dejian-ioe
cp -r ~/workspace/chouce-20261028/extracted/zhu-code/dejian-showcase /workspace/dejian-showcase
mkdir -p /workspace/dejian-design-proposal          # create_guest 写 system-login.txt 要用
cd /workspace/dejian-ioe
python3 -m venv .venv                                # python 3.12.3，与 Dockerfile 3.12 对齐
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install whitenoise                     # ⚠️ requirements 缺它，不装 showcase_settings 起不来
mkdir -p db media static                             # ⚠️ 包里没有这三个目录
```
- 前置条件：磁盘够（seed 后 sqlite 库约百兆级以内）、能联网装 pip。
- 失败点：漏 whitenoise → 起服务时 `ModuleNotFoundError: whitenoise`；漏建 `db/` →
  migrate 时 sqlite `unable to open database file`（settings 只自动建 logs/backups/temp，不建 db）。

### 4.1 重建 showcase.env（被剥掉，必须自拟）
`/workspace/dejian-showcase/showcase.env`（reset_showcase.sh 会 `set -a; . 它`）：
```bash
DJANGO_SETTINGS_MODULE=showcase_settings
PYTHONPATH=/workspace/dejian-showcase:/workspace/dejian-ioe
SECRET_KEY=<本地新生成的随机长串，不要用代码里的缺省值>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
SHOWCASE_DB=/workspace/dejian-showcase/showcase.sqlite3
SHOWCASE_SNAPSHOT=/workspace/dejian-showcase/showcase.clean.sqlite3
DEJIAN_OPEN_ACCESS=1
DEJIAN_OPEN_ACCESS_USER=chouce_guest
READONLY_USERNAMES=chouce_guest
COOKIE_SECURE=0
```
- 要点：`PYTHONPATH` 是让 `showcase_settings`/`showcase_urls` 可 import 的唯一办法（两文件在 IOE 之外）。
- `COOKIE_SECURE=0` 只限本机 HTTP 调试；上 HTTPS（Caddy）时改回 1。
- 失败点：env 里没有 `DJANGO_SETTINGS_MODULE` → 所有命令默认跑 `inventory.settings`（主库），
  现象是「命令成功但连错库」；SECRET_KEY 不设 → 用代码内缺省开发值，本机自测可忍、上线不可。

### 4.2 建主库（空库）并 seed 德鉴案例企业 —— 这是体验库的数据源头
```bash
cd /workspace/dejian-ioe
set -a; . /workspace/dejian-showcase/showcase.env; set +a
export DJANGO_SETTINGS_MODULE=inventory.settings   # 这一段明确跑主 settings，不要用 showcase
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_dejian             # 数据源 dejian_case.xlsx 在包里；想跳过末尾 AI 测算加 --no-ai
```
- 前置条件：§4.0 的 venv 与 `db/` 目录；xlsx 与 demo_assets 完整（包里已确认存在）。
- 产出：主库 `/workspace/dejian-ioe/db/db.sqlite3`，含 `code='dejian'` 企业（+一个 demo-other）。
  **这个路径正是 build_showcase 写死的 SRC**，布局对了才接得上。
- 失败点：seed 中途报错重跑会提示已存在，需加 `--reset`；seed 耗时取决于 550 天历史生成，
  不要误判为卡死；seed 里演示账号口令是代码内演示值，上线口径不要外传，build 后会被停用。

### 4.3 转换成体验库
```bash
.venv/bin/python /workspace/dejian-showcase/build_showcase_db.py   # 纯 sqlite 脚本，输出 replaced cells 数
ls -lh /workspace/dejian-showcase/showcase.sqlite3
```
- 前置条件：§4.2 完成且主库里确有 `code='dejian'` 企业。
- 失败点：见 §1.2——SRC 不存在/为空时分别死在 connect 和 `fetchone()[0]`；
  另外 DST 所在目录 `/workspace/dejian-showcase` 必须先存在（§4.0 已保证）。

### 4.4 建只读访客 + 存干净快照
```bash
cd /workspace/dejian-ioe
set -a; . /workspace/dejian-showcase/showcase.env; set +a     # 此时 DJANGO_SETTINGS_MODULE=showcase_settings
# 可选：GUEST_PW=<自定> 不设则随机生成，去 system-login.txt 里看
.venv/bin/python manage.py shell < /workspace/dejian-showcase/create_guest.py
.venv/bin/python manage.py collectstatic --noinput           # 目标写死 /workspace/dejian-showcase/staticfiles
.venv/bin/python manage.py reset_showcase --save-snapshot    # 存 showcase.clean.sqlite3 供每晚还原
```
- 前置条件：§4.3 的体验库在位；`/workspace/dejian-design-proposal/` 已建（§4.0）。
- 失败点：settings 没切到 showcase → `Tenant(code='chouce')` DoesNotExist；
  collectstatic 前没装 whitenoise 不影响 collectstatic 本身，但起服务必挂（见 §4.0）；
  reset_showcase 若连到主库会被它自带的护栏拒绝（说明 settings 切错了，反而是好事）。

### 4.5 起服务（二选一）
```bash
# A. 本机调试（runserver 自带静态服务，WhiteNoise 也在）
.venv/bin/python manage.py runserver 127.0.0.1:8000
# B. 按交接方案（gunicorn；wsgi 的 setdefault 不会覆盖 env 里的 showcase_settings）
.venv/bin/gunicorn inventory.wsgi:application --bind 127.0.0.1:8000 --workers 2
```
- 前置条件：env 已 source（§4.4 同一 shell 或重新 source）；端口先 `ss -ltn | grep 8000` 确认空闲，
  本次探测 8000/8001/8002 均空闲，被占改 8010 并同步 `ALLOWED_HOSTS` 无需改（只认主机名不认端口）。
- 验证清单：打开 `/accounts/login/` 应见筹策登录页；`/enter/` 应以 chouce_guest 免密进入体验企业；
  随便提交一个写操作应被只读中间件拦下；页面企业名应为「筹策体验酒业有限公司」且只有这一家企业；
  商品图 `XJ-%` 应无图（build 时已置 NULL，属预期）。
- 失败点：浏览器登录后立刻掉线/表单 CSRF 报错 → 多半 `COOKIE_SECURE` 还是 1 而你在用 HTTP（改 0）；
  静态文件 404 → collectstatic 没跑或 WhiteNoise 没装；进成了 dj_boss/德鉴企业 → 连错库或 settings
  没切，立即停下查 env，不要继续操作。

### 4.6 （可选，上线形态）每晚重置
```cron
30 3 * * * /workspace/dejian-showcase/reset_showcase.sh >> /workspace/dejian-showcase/reset.log 2>&1
```
- 前置条件：§4.4 已存快照；reset_showcase.sh 里写死的 cd/env 路径与 §4.0 布局一致。
- 本机自测阶段可不装 cron，手动跑 §4.4 的 `reset_showcase`（不带 --save-snapshot）验证还原即可。

---

## 5. 风险/未定事项汇总

1. `showcase.env` 是重建拟稿，交接没有给原文；其中 `PYTHONPATH` 与 `DJANGO_SETTINGS_MODULE`
   两项是按代码反推的必需项，若渚那边有原 env，以原 env 为准。
2. 交接「上线前必须修」清单里与代码有关的几项（barcode 500、储值汇总隔离等）是否已在包里修好，
   本报告未逐项验（不在任务范围）；体验库能跑起来 ≠ 那几项已修，上线前仍需按交接清单核。
3. `seed_dejian` 生成数据的「今天」取运行日，晚于 2026-10-28 跑会多出补充订单，属设计行为、非 bug。
4. MEDIA_ROOT 在 IOE/media，seed 挂的商品图走 image 字段存入该目录（demo_assets/products 是源）；
   备份/迁移体验库时别只拷 sqlite，media 要一起。
