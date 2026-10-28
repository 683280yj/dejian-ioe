# 筹策本机生产化部署记录（2026-10-28 02:05–02:12）

用户 02:04 指令：部署在助手本机（本 VM），不再等香港服务器。

## 形态
- 三个 systemd 服务（Restart=always，已 enable 开机自启）：
  - chouce-showcase：体验库，gunicorn 2 workers，127.0.0.1:18001，showcase_settings
  - chouce-main：主系统（德鉴租户），gunicorn 2 workers，127.0.0.1:18000，prod_main_settings（inventory.settings + WhiteNoise + 独立 STATIC_ROOT main-staticfiles，collectstatic 164 文件）
  - chouce-site：官网静态，python http.server，127.0.0.1:18002
- chouce-reset.timer：每天 03:30 跑 reset_showcase.sh 还原体验库快照后重启 showcase 服务（交接缺失的「每晚 reset 定时」在本机已补上）
- 配置文件：/workspace/dejian-showcase/showcase.env、main.env（均 600 权限，含新生成的随机 SECRET_KEY，不落聊天/报告）；unit 副本存 prod-units/（VM 替换会清 /etc，凭副本可一键重装：cp 到 /etc/systemd/system 后 daemon-reload + enable --now）
- COOKIE_SECURE=0（本机 HTTP；将来走 HTTPS 隧道/域名时改 1）

## 验证（02:12 实测）
- 体验库：登录页 200；/enter/ GET 200 → POST 302 → 首页 200（经营概览、chouce_guest）；访客 POST /products/create/ 403；静态 app.css 200
- 主系统：登录页 200、静态 base.css 200（此前 runserver+DEBUG=False 下静态 404 的问题已消除）
- 官网：index 200；三服务 systemctl is-active 均为 active，日志无 error

## 未决
- 对外公网访问未开：服务只绑 127.0.0.1。本机对外通道依赖经 VPS 的反向隧道，VPS 的 SSH 仍未通（等渚/用户装公钥），通道恢复后可把体验库挂到公网域名；香港服务器正式部署同理顺延。

## 公网转发（2026-10-28 02:07–02:14）
- 突破：VPS 的专用账号 tunnel + 本机 ~/.ssh/tunnel-key 可登录（此前子代理只试了 root/ubuntu/ecs-user，未试 tunnel）。该账号无 sudo。
- VPS sshd 已设 GatewayPorts yes；华为云安全组实测只放行 22/80/443（80/443 已被既有服务占用），18011/18012 等高位端口外网不通（浏览器实测连接被拒；muse2api 的 7861 同样外网不直达、历来靠 ssh -L）。
- 已建 systemd chouce-tunnel.service（Restart=always、已 enable）：反向转发 VPS 18011→本机 18001（体验库）、18012→本机 18002（官网）；VPS 侧监听 0.0.0.0 已确认，经隧道回环实测体验库登录页 200、官网 200。主系统 18000 未转发（不公开）。
- showcase.env 的 ALLOWED_HOSTS 已加 159.138.136.40。
- 待用户二选一：①在华为云安全组放行 18011/18012（隧道已就绪，放行即通）；②改走 Cloudflare Tunnel 给域名+HTTPS（需其 Cloudflare 账号配合）。
- 更正与进展（02:17）：此前「安全组只放行 22/80/443」是误判——本机 curl 失败源于平台出口代理，8318 有历史公网先例（2026-10-08 CPA 转发实测 200）。已把隧道改绑 8318（体验库）/8319（官网）：8318 经出口代理实测 http://159.138.136.40:8318/accounts/login/ 返回 200，公网已通；8319 仍不通（无现成放行规则）。隧道 unit 已同步更新（prod-units/chouce-tunnel.service）。
- 02:31 用户已在华为云安全组放行 8319：实测官网 http://159.138.136.40:8319/ 公网 200；site-config.js 的 loginUrl 已填 http://159.138.136.40:8318/accounts/login/（公网拉取核验已生效），其余 7 字段仍空（公司名/预约/联系方式/备案待甲方信息）。体验库登录页与 /enter/ 访客入口公网均 200。
- 02:40 按用户要求通用化+配色对齐（已改代码，偏离交接包基线）：PLATFORM_WORDMARK「酒企 To B 平台」→「筹策工作台」（tenancy/context_processors.py）；login.html 眉题 MULTI-BRAND · B2B→ALL-IN-ONE WORKSPACE，介绍文案去「多品牌/经销商/供应商/门店」改为库存、销售与会员/企业工作空间（中英同步）；dejian.css 浅色底由冰蓝 #dceaf6 改米纸 #f4ecdd、墨色 #233d53 改暖墨 #33231b、网格线/阴影/描边统一为酒红系 rgba(110,31,44,…)，与官网及「米纸+深酒红」口径对齐（深色主题未动）；静态版本 dj7→dj8，collectstatic 已同步体验库与主系统并重启；test_branding 断言已同步，4 项测试通过；公网登录页实测新文案与新 CSS 已生效。截图 screenshots/login-generic-warm-mobile.png。
- 02:45 按第二批参考图（《万卷》古籍 App 规范板）做了 SaaS 版视觉重设计提案 V1（未上线）：~/workspace/chouce-20261028/design-proposal-v2/board.html + 5 张分段截图。口径：米纸+回纹水印只进外壳，宋体只做标题/数字，色板取参考图原值（通区金 #EBC387、古籍金 #BEA06E、朱砂 #B46E5A、墨绿 #64735F）+ 酒红主色，含登录/概览/商品列表三屏。待用户确认方向后再落地到 dejian.css 与模板。
- 03:00 官网质感适配已上线（用户反馈 V1 提案「太淡太素没质感」+要求按同赛道整理适配网站）：site.css 末尾追加覆盖层——首屏两张卡改深酒红牌匾+金边金字、主标题第二行改烫金色、数据带改实色深带+金色数字、主按钮酒红渐变+金描边、浅色章节加回纹底纹与标题金色下划线、卡片加金边与暖影、页脚酒红渐变。文案/结构/JS 未动，测算器实测正常，本地与公网均 200。旧版备份在 ~/workspace/chouce-20261028/site-backup-20261028-0252，回滚删覆盖段或还原备份即可。index.html 的 CSS 链接已加 ?v=20261028c 破缓存。
- 03:15 官网 V3 炫酷版上线（用户要求：主页更炫酷抓眼球、高级特效、图多字少）：新增 assets/js/fx.js（顶部金色滚动进度条、首屏金尘粒子 Canvas+极光光晕、首屏卡片组与界面大图鼠标视差倾斜，均带 reduced-motion/触屏降级）；首屏下方新增「系统长这样」真实截图无缝滚动带（5 张界面图×2 循环，悬停暂停）；CSS V3 层加标题金色光晕等。文字精简 18 处：对比表 5 行→3 行、账目 8 卡标题改四字短题+一句话、六业段落改一句话、运筹步骤收紧。实测零 JS 错误、测算器正常、公网 200。
- 03:24 VM 被替换：/workspace 链接、systemd units 丢失，四服务全停。已恢复：重建 /workspace→work 链接、从 prod-units/ 重装 units 并 enable --now，8318/8319 公网复测 200。注意：代码库 .git 目录已不在（交接时 HEAD 1ec2c9a），版本管理中断，待用户决定重新 init 或从鸣人包恢复。
- 03:40 补货解释层上线（体验库试点）：新增 ai_assist/explain.py（异常检测 7 类规则 + 规则版一句话解释 + OpenAI 兼容 LLM 客户端，JSON 强约束、失败自动回退）；Suggestion 加 4 字段（迁移 0002，两库均已应用）；services.run_workflow 测算后生成、hints 页面侧规则补齐；库存页建议行新增「一句话解释/AI 解释」徽标 + 异常 chips（红/黄/灰分级）。开关 AI_EXPLAIN_ENABLED 只写进 showcase.env，主系统未开。ai_assist 24 测试全过；全量 211 测试有 9 个未过，已定位的 2 个为交接时已知的环境问题（Django 6.1.2 下 i18n 英文空状态断言、删除接口 CSRF 测试读 cookie 的 KeyError），与本次改动无关，其余清单复核中。公网体验库实测：3 条建议均已生成解释与异常标记，数字与测算一致。
- 03:32 代码规范审计回件（reports/code-standards-audit.md）：解释层专项结论合规可保留试点（只写 ai_* 4 字段、租户隔离、读路径不调 LLM、模板转义）。已当场整改审计指出的三处解释层问题：①fill_run_explanations 改为 transaction.on_commit 后执行，避免配 LLM 后长开事务锁 SQLite；②LLM 契约简化为只返回 explanation（异常一律规则生成，删除原 anomalies 要求）；③两处裸 except 补 logging。ai_assist 24 测试复跑全过，showcase 已重启。遗留待用户拍板：.git 丢失后重新 init、settings.py SECRET_KEY 硬编码默认值处理、Django 版本锁定（现跑 6.1.2，requirements 仍 >=4.2.0）、sales.py 35 处 print 清理、GET 库存页惰性写库（规则解释补填，可接受但审计已记录）。
- 03:35 按用户指示为生产工作树重新 git init（分支 main，本地身份 683280yj，未推任何远程）：.gitignore 补 _wt/ 一行（原文件已覆盖 *.env、db.sqlite3、.venv、media、staticfiles）；暂存 599 文件，敏感文件名扫描无命中，最大文件为设计图约 4MB。基线提交 0e7cdc8「重新初始化仓库：筹策（德鉴 IOE）本地基线快照」，工作树干净。
- 03:36 更正上一条的测试数字：以完整日志复核，全量实为 207 个测试、失败 1 + 错误 1 + 跳过 2，与交接基线（207 个）一致。两个未过项均为既有环境问题：test_english_empty_state_and_inactive_status（Django 6.1.2 下 i18n 英文断言）、test_delete_item_requires_post_and_csrf（测试代码读 csrftoken cookie 的 KeyError）。先前「211 个、9 个未过」系一次中途状态的跑次读数，不成立，以本条为准。解释层无回归。
- 03:47 酿见蓝图页改版完成（预览 http://159.138.136.40:8319/blueprint/ ，源文件 ~/workspace/chouce-20261028/niangjian/，甲方原件未动）：整页换暗红设计系统（theme.css，tokens 按 DESIGN.md 的 Radix 式色阶，思源宋体 900 标题+思源黑体+霞鹜文楷走 jsdelivr）；图表配色同步压暗（销量线改亮红 #e0685f、金线 #e0a55a、网格金色半透明）；决策卡 6 个字符字形图标换成 Lucide 并内联 SVG（零 CDN 依赖）；h1 em 改标题金（原深酒红压暗底约 1.5:1，UX P0 已修）。按用户口径加两处「筹策已实现」文字链（沙盘下方、决策卡下方）链到体验库实况，不做按钮；沙盘实测可运行（1,792/1,508 箱与 PPT 文案样例一致），零 JS 错误。
- 03:44 补货建议面板按用户反馈改「客服口吻」：去掉「AI 辅助」徽标，行文案改为先说情况再给建议（如「含在途仅够卖 9 天，短于交期 12 天，断货风险高，建议补 408 瓶（约 68 箱）。」），细节仍收在「为什么」里。ai_assist 24 测试通过，showcase 已重启。
- 04:06 筹策助手上线体验库（仿 JadeAI 的 AI Chat Assistant 形态）：库存页右下角「问筹策助手」打开对话抽屉，助手先播报今日建议概况；可问「哪条最急/为什么补这么多」，可说「生成草稿」——助手先复述确认，用户回「好」后才由前端走既有采纳入口（POST+CSRF+权限）执行，助手本身不写库。对话走 GET 以兼容体验库只读访客中间件；访客确认生成时会被只读规则拦下，助手如实说明。规则脑实现（ai_assist/assistant.py），配 AI_API_* 后可换 LLM 脑、界面不变。ai_assist 测试 30 项全过；实测对话全流程通过。
- 04:24 审计整改与去英文完成并提交（本地 3 个提交：7b016a4 助手与客服口吻、22bfb04 去英文+SECRET_KEY 必填、3744679 sales 日志与依赖锁版本）：LANGUAGES 只留中文、删顶栏语言切换与英文测试（LocaleMiddleware 保留，模板依赖 request.LANGUAGE_CODE，语言锁定中文）；SECRET_KEY 删硬编码默认值、未设环境变量启动即报错；sales.py 35 处 print 改 logger.debug；requirements 按实跑版本精确锁定（Django==6.1.2 等）；页面侧解释改 persist=False 不再 GET 写库。全量 208 测试仅剩 1 个既有 error（test_delete_item_requires_post_and_csrf，交接基线问题），英文 error 已消除。两服务已重启，实测：语言切换器已消失、补货面板与筹策助手正常、主系统登录页 200。
- 04:37 已推远程：私有仓 https://github.com/683280yj/dejian-ioe （本机无 git 凭据、SSH 不通，走 GitHub Git Data API + custom.github surrogate 镜像本地 4 个提交；空仓先放种子提交再强制对齐 main，HEAD 树 600 文件已核验）。推送脚本 ~/workspace/chouce-20261028/push_via_api.py（断点状态 .push-state.json，后续增量推送可复用；注意远程提交 SHA 与本地不同，内容与说明一致）。
- 04:47 官网对比度 P0 已修（不等主页替换拍板，属现网缺陷）：calc.js 生成的 <details> 补 class="more"（「更多参数」入口此前 CSS 命不中、约等于看不见，现为数字金 #e8c87e）；site.css 追加 V4.2 补正块——暗色板块 .lead→#d8c3a5、.k 编号→#e0a55a、h2 em→#e3b96a、步骤号→#e0a55a；CSS/JS 版本号 bump 到 20261028f。Playwright 实测 computed color 全部命中预期，零 JS 错误。
- 08:01 官网域名上线：https://cc.idky.tech（Cloudflare Tunnel 名 cc，id e77edd40；cloudflared 跑在 VPS tunnel 账号 ~/cc-tunnel/，回源 127.0.0.1:8319，cron @reboot+*/5 keepalive 保活；本机 VM 因出口代理无法直连 CF 边缘 7844，cloudflared 放本机的方案已弃，VM 侧 chouce-cftunnel 单元已禁用）。实测首页 200、/blueprint/ 200。
- 08:05 按用户定位拍板加「未来设想」板块（官网第 10 节，原问答/问策顺延 11/12）：酿见只作设想展示（明示未上线），主推仍是筹策进销存+AI；板块链到 /blueprint/ 完整蓝图，配图用蓝图酒窖图。页脚公司名「筹策求知科技有限公司」已实测渲染。
- 08:08 官网 V4.4（按用户口径）：全站改 FDE 定制叙事——首屏 kicker/副文案/背书行、页脚品牌行、01/07/08/12 节导语改为「针对德鉴酒业 FDE 定制开发」，标题改为同口径；首屏后新增 FDE 定制带（驻场调研/按规则开发/上线后迭代，底图为酿见瓶身图）；参考酿见把 .sec h2 放大到 clamp(34px,4.6vw,64px)。cc.idky.tech 实测生效（FDE 出现 5 处，200，零 JS 错误）。
- 08:04 本机 VM 再次被替换，chouce 四服务全停，cc.idky.tech 一度 502（用户截图反馈）。08:10 已按 runbook 恢复：重建 /workspace 软链与 workspace 下 dejian-ioe/dejian-showcase 两个软链（母本在 work/ 下），prod-units 单元拷回 /etc/systemd/system 后 daemon-reload 并 enable --now，showcase/main/site/tunnel 四服务 active，cc 域名连测 3 次 200、8318 为 302（正常跳登录）。

- 10:15 域名切换与隧道退役（用户自部署接管）：用户已在 VPS 以 root 部署 /opt/dejian-ioe（docker-compose.huawei.yml，gunicorn 10:06 起）与 /opt/dejian-site（nginx 静态，public 10:13 更新），cc.idky.tech 经 Cloudflare 代理 + VPS Caddy 直达用户部署（响应 Via: 1.1 Caddy，首页 md5 与 /opt/dejian-site/public/index.html 一致 c6ec381a）；官网登录入口已指向用户应用 https://ioe.159-138-136-40.sslip.io/accounts/login/（实测 200）。助手侧退役动作：停 VPS tunnel 账号下 cloudflared（pid 168366）并摘除其 crontab 保活两行（备份 ~/cc-tunnel/crontab.bak-20261028，TripStar 保活未动）；本机 chouce-tunnel 等四单元在当前 VM 实例本就不存在（VM 替换后未恢复），无隧道进程。停后复测：cc.idky.tech 与 /blueprint/ 均 200 且内容不变，公网 8318/8319 已无监听（释放）。prod-units/chouce-tunnel.service 仅作历史档案保留，后续恢复本机服务时不要再装它。
