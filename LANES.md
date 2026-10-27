# 德鉴 × IOE 二开分工（box 共享目录 /workspace/dejian-ioe）

总原则：基于开源进销存 IOE（Django，MIT，保留原版权）二开；面向多品牌 To B；德鉴作为首批体验企业做 demo 数据（对外演示可用「演示酒业」）。
AI 只做重复活（算数/对表/筛异常/起草），人做决定和执行（审批/入库/发货/付款）。AI 绝不自动审批、下单、改库存、发货。
**不接支付宝**（已取消）。忽略 PLAN.md 里所有支付宝内容。不提交密钥，不 push，不改 upstream。

各自只在自己的 worktree 干活，只改自己拥有的目录；需要别人改的东西写到 /workspace/dejian-ioe/COORDINATION.md（只追加，写明 From/To/内容）。
完成一块就在自己分支 commit（git -c user.name=SandyCmm -c user.email=yggcmm@outlook.com commit）。合并到 main 由 渚 统一做。

## lane-a（渚）：/workspace/dejian-ioe/_wt/lane-a
- 多租户底座：企业(Tenant)→品牌(Brand)→仓库/渠道；所有业务表加 tenant；按登录用户过滤；角色（老板/采购/销售/仓库/财务/稽核）。
- AI 服务层：新 Django app `ai_assist`（补货测算、入库对单、订单异常筛查、库存预警、对账、日报起草），规则/统计算法为主，可选 LLM 起草（环境变量配置，无 key 时降级为模板）。
- 德鉴 demo 种子命令：`python manage.py seed_dejian`。
- 拥有：project/、inventory/models*、inventory/migrations、inventory/views*、inventory/urls*、新 app ai_assist/、seed 命令。

## lane-b（鸣人）：/workspace/dejian-ioe/_wt/lane-b
- 界面按 docs/DESIGN_SPEC.md 重做（暖纸底、衬线标题、直角细线；AI 产出=靛蓝 #5149cf，人的决定=酒红 #8b1e3f）。
- 拥有：所有 templates/、static/（css/js/图片）。不改 Python 模型/视图；需要新上下文变量就写 COORDINATION.md 找 lane-a。
- 先做：base 布局 + 侧栏/顶栏 + 登录页 + 首页仪表盘 + 商品列表/库存列表的样式；再预留「AI 工作台」页面模板（ai_assist/templates/ 可由你写，视图归 lane-a）。

## lane-c（零）：/workspace/dejian-ioe/_wt/lane-c
- To B 交易：新 Django app `b2b`（采购单、供应商对账、企业客户/经销商、批发订单、应收应付），含 models/views/urls/templates/tests。
- 拥有：b2b/ 整个目录。需要 tenant 外键时先用 `tenant = models.ForeignKey('tenancy.Tenant', null=True, ...)` 约定名称（lane-a 会建 app `tenancy`），在 COORDINATION.md 对齐。
- 注册到 settings/urls 的改动写 COORDINATION.md 让 lane-a 合，不要自己改 project/。

## 验收
- `python manage.py test` 全过；`runserver` 能打开主要页面；德鉴种子数据能一键导入；AI 页面能对德鉴数据给出建议，采纳只生成草稿/待办。

## 唯一硬性要求：2026 iCAN「精创杯」AI 智能决策挑战赛命题（docs/REQUIREMENT.docx）
系统必须能现场演示以下每一条（这是评分口径）：
1. **真实企业**：德鉴酒业作为研究对象，写清 谁在做/什么场景/当前人工怎么做/痛点（耗时、成本、差错）。人工基线要有数字（标注「演示假设」或来源，不编造成事实）。
2. **数据清单**：系统内「数据清单」页：每类数据→来源→清洗/对齐/脱敏处理→完备性→缺失字段补齐方案→对应业务环节与效能指标。
3. **量化决策**：每个 AI 环节设可量化目标 + 约束（预算、资源、业务规则），输出**带具体取值**的处置动作（如「向 X 供应商补 120 箱，预算占用 ¥4.3 万」），并标明更新周期（实时/日/周/月）。
4. **可解释、可质疑、可调整**：每条建议显示依据/公式/输入数据；用户可改参数（约束、目标）**重新测算**；区分「自动执行」（仅限低风险：如生成预警、起草报表）与「人工复核确认」（审批、下单、入库、发货）；AI 只给备选方案，人拍板。
5. **回测/仿真对比**：用德鉴演示历史数据做回测或仿真，与人工基线对比（缺货率、库存周转、对单耗时、差错率等），给出推导过程。
6. **适用边界与风险**：页面或文档写明失效场景、运维成本、风险与应对。
7. 成果展示：系统 + 方案文档要通俗易懂，适合 PPT/情景模拟路演。
