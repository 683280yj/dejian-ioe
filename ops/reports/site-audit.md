# 筹策官网静态审查报告（逐页实测对照用）

- 审查对象：`extracted/shiyu/dejian-design-proposal/release/chouce-site/`（纯静态站，共 3.0 MB）
- 审查日期：2026-10-28
- 方法：只读。逐个 `test -f` 核对各 HTML 的 src/href/srcset/poster/data-src 相对路径、site.css 的 url()、404 内联 @font-face 路径；grep 抽查禁用词与「每天」；对照 `extracted/weier/copy/chouce-site-copy.md`、`extracted/ling/chouce-feature-list.md`、`delivery/交付说明.md`。
- **总结论：本地资源零死链**（见 §1 明细）；**待填项集中在 site-config.js，8 个字段全部为空**（见 §2）；index.html 禁用词与「每天」均为 **0 命中**（见 §3）。

---

## 1. 全部页面与资源引用

站点共 3 个 HTML 页面，另有 `robots.txt`（内容仅 `User-agent: * / Allow: /`）、`favicon.svg`、`favicon-32.png`、`apple-touch-icon.png`、`site-config.js`。

### 1.1 index.html（355 行）— 首页（单页站）

用途：产品主页，自上而下为：导航（栏目锚点 +「登录系统」+「预约产品讲解」）→ 首屏（主标题「每一箱货，都算过再进」、补货建议卡 + 库存预警卡）→ 数字条（28 天 / 60 天 / 6 大模块 / 1 套系统）→ 补货测算四步 `#how` → 补货测算器 `#try` → 单据流程 `#flow` → 价值 → 真实截图 `#tour`（5 个标签页）→ 库存预警 → 进销存账目 `#ledger` → 六类行业方案 `#industries` → 客户案例（贵州德鉴酒业）→ 常见问题 `#faq` → 预约/联系 `#contact` → 页脚。
标题（L6）：「筹策 · 经销商进销存与补货测算」——交付说明 §七清单里「网页标题改成正式名称（现在写的是『筹策·动态首屏』）」一项，**成品已改好，实测时不要再按旧清单报缺**。

本地资源引用（全部存在）：

| 行号 | 引用 | 结果 |
|---|---|---|
| L21–23 | `favicon.svg`、`favicon-32.png`、`apple-touch-icon.png` | OK |
| L24 | `assets/site.css` | OK |
| L189/197/205/213/221 | `assets/shots/{overview,wholesale,po,statement,b2b}.jpg` 及 `<source srcset>` 对应 `.webp` | 10 个文件全 OK |
| L313 | `<video poster="assets/video/mist-poster.jpg" data-src="assets/video/mist.mp4">`（问策板块背景视频，懒加载） | OK |
| L351–353 | `site-config.js`、`assets/js/main.js`、`assets/calc.js` | OK |
| L345 | `credits.html`（页脚「素材与字体授权」） | OK |
| meta | og:image 为绝对地址 `https://chouce.deed.page/assets/og.jpg`，本地 `assets/og.jpg` 存在；canonical 同为该域名 | OK（依赖域名不变） |

页内锚点 `#main/#top/#how/#try/#tour/#ledger/#industries/#faq/#contact` 逐个核对 id，**全部有对应元素，无死锚**。
site.css 的 url() 亦全部存在：4 个字体 `assets/fonts/{NotoSerifSC-Heavy,NotoSansSC-Regular,NotoSansSC-Bold,GeistMono}-subset.woff2`、首屏背景 `assets/img/hero-{fanjingshan,huangguoshu}.{jpg,webp}`（L55–56）、`assets/video/mist-poster.jpg`（L218）。

### 1.2 credits.html（64 行）— 素材与字体授权页

用途：列明本站图片（梵净山、黄果树瀑布，CC0，附 Wikimedia Commons 原始页外链）、背景视频（Mixkit 免费许可，附 mixkit.co 外链）、字体（思源宋体/黑体、Geist Mono，SIL OFL 1.1）的来源与授权；从 index 页脚进入，页内有「返回首页」链接。
本地资源：`favicon.svg`（L8）、`favicon-32.png`（L9）、`assets/site.css`（L10）、`index.html`（L26/28/61）——**全部存在**。
注意：**本页不加载任何 JS**（无 site-config.js / main.js），页脚只有「© 2026 筹策」，不显示公司名/备案号（与 §2 的配置注入无关，属预期）。

### 1.3 404.html（29 行）— 错误页

用途：`noindex` 的独立错误页（标题「页面不存在 · 筹策」，正文「这一页没有找到」+ 返回首页按钮），样式全部内联，不依赖 site.css / JS。
本地资源：`/favicon.svg`（L8）、内联 @font-face 的 `/assets/fonts/NotoSerifSC-Heavy-subset.woff2`（L10）与 `/assets/fonts/NotoSansSC-Regular-subset.woff2`（L11）、`/index.html`（L26）——**文件全部存在**。
注意：本页用的是**根绝对路径**（`/…`），只有部署在域名根目录时成立；若实测时用子路径/本地目录打开，字体与图标会 404，这是路径写法问题，不是文件缺失。

**死链结论：三个页面 + site.css 的全部本地引用逐个核对，无一缺失。** 外链仅 credits 的 Wikimedia/Mixkit 来源页、页脚备案查询链接（`beian.miit.gov.cn`、`beian.mps.gov.cn`，且备案号未填时不显示，见 §2），静态审查无法验活，留待实测点开确认。

---

## 2. site-config.js 待填项（核心待办）

文件头注明「甲方只需改这一个文件，留空的项目不会在页面上显示」。**当前 8 个字段全部为空 `''`**：

| 字段 | 行 | 被哪里引用 / 留空时页面表现 |
|---|---|---|
| `companyName` 公司全称 | L8 | `main.js` applyConfig 填入 index 页脚 `data-cfg="companyName"`（index L342）；留空则页脚只有「© 2026 筹策」，无公司名 |
| `bookingUrl` 预约表单/企微链接 | L11 | `main.js` L48–58 给 `#bookBtn`（index L319「预约产品讲解」）赋值，优先级最高；三项全空时按钮点击只弹提示「预约产品讲解，请联系筹策顾问」，不跳走 |
| `email` 联系邮箱 | L12 | 同上：bookingUrl 为空时 bookBtn 变 `mailto:`；且填入联系列表 `#clines`（index L321）显示「邮箱」一行 |
| `phone` 联系电话 | L13 | 同上：再空则 bookBtn 变 `tel:`；`#clines` 显示「电话」一行（可一键拨打）。三项全空时 `#clines` 整块隐藏，只显示 `#cpending` 提示句（index L322） |
| `loginUrl` 系统登录页地址 | L17 | `main.js` L24–29 处理全部 5 处 `[data-login]`「登录系统」：index L40（导航）、L55（首屏）、L228（截图区）、L319（预约区）、L336（页脚）。留空时不跳转，点击只弹提示「系统账号由筹策开通，请联系筹策顾问」 |
| `icp` ICP 备案号 | L20 | index 页脚 `data-cfg="icp"`（L343），填后显示并链到 beian.miit.gov.cn；留空不显示 |
| `police` 公安备案显示文字 | L23 | index 页脚 `data-cfg="police"`（L344）；留空不显示 |
| `policeCode` 公安备案编号 | L24 | 与 police 配套，`main.js` 用它拼 beian.mps.gov.cn 查询链接 |

附带发现（实测时留意）：`main.js` 中 `#cpending` 提示句的显示条件是「bookingUrl 为空」，即使只填了 email/phone、bookBtn 已可用，该提示句仍会显示，可能造成观感矛盾，建议实测确认。
另：交付说明 §六写「配置项都在 `assets/config.js`」——**成品实际文件名/位置是根目录 `site-config.js`**，按旧说明找会找不到，以成品为准。

### 补货测算器（calc）

- 位置：index.html `#try` 板块「02 · 动手算一笔 · 补货测算器」（标题 L113，副标 L114），容器 `<div id="chouce-calc"></div>`（L117），由 L353 `<script src="assets/calc.js" defer>` 注入表单与结果。
- **`assets/calc.js` 存在**（96 行，单品补货测算，公式头注与系统 `ai_assist` 的 replenish 口径一致）。
- 注意区分：首屏还有一条 `<ol class="calc" id="calc">`（L62），那是补货步骤动画卡，由 main.js 驱动，**不是测算器本体**，实测勿混。

---

## 3. 禁用词与「每天」抽查（对象：index.html）

对 index.html 全文 grep「试点 / 测试 / 演示 / 示例 / 规划中 / 试用 / 即将」：

- **7 个禁用词全部 0 命中**（与交付说明 §七「全文复查：搜一遍试点/测试/演示/示例/规划中，一处都没有」的要求一致）。
- **「每天」在 index.html 中 0 命中**，无行号可列。

相关的两处在 index.html 之外，实测对照时不要误报/漏报：

1. **文案稿里有、网页里已删**：`chouce-site-copy.md` L238 原稿副标「填四个数，马上得出该补几箱。系统里**每天**就是这样替你算的。」→ index.html L114 已改为「填几项数据，马上得出该补几箱。系统里就是这样替你算的。」——「每天」已去掉，与「ai_refresh 未配好前不写每天」的交接口径相符。
2. **calc.js 里有「每天」，但属测算器字段说明、非刷新承诺**：`assets/calc.js` L59 表单标签「近 28 天**每天**卖出的瓶数（用逗号或空格分开）」、L73 校验提示「请填入**每天**的销量。」——这两处会随测算器渲染到 index 页面上，指的是日销量输入，不是「每天自动刷新/测算」的说法；是否要改由文案口径决定，静态层面先标注位置。

---

## 4. 官网宣称的 6 大模块 / 功能清单（标题级，供测试报告引用）

口径一 —— 官网数字条原文（index.html L85）：「6 大模块：**采购、库存、盘点、批发开单、供应商对账、补货测算**」（另滚动字带含第 7 个词「库存预警」，main.js L104）。

口径二 —— `chouce-feature-list.md` §四「对外功能清单」（只列代码已实现者）共 6 组标题：

1. 采购
2. 库存与盘点
3. 批发开单
4. 应收
5. 补货建议
6. 多租户与权限

两套口径对照差异（实测引用时注意）：官网的「供应商对账」在功能清单里归入「采购」组（对账只有供应商侧，无客户对账单）；官网未单列「应收」与「多租户与权限」，功能清单则把「库存/盘点」合并为一组、把「补货测算」写作「补货建议」。

---

## 5. 待填 / 待确认清单汇总（实测对照）

1. site-config.js 8 字段全空：companyName、bookingUrl、email、phone、loginUrl、icp、police、policeCode（§2）。
2. 「登录系统」5 处入口在 loginUrl 未填前全部只弹提示，无真实跳转（§2）。
3. 「预约产品讲解」在三项联系方式未填前无真实去向（§2）。
4. 页脚无公司全称、无 ICP/公安备案号（配置未填所致，非代码缺失）（§2）。
5. `#cpending` 提示句显示条件与 bookBtn 可用条件不一致，待实测确认观感（§2）。
6. calc.js L59/L73「每天」两处是否按文案口径处理，待定（§3）。
7. 404.html 根绝对路径决定其只能在域名根目录部署下成立（§1.3）。
8. og:image / canonical 写死 `https://chouce.deed.page/`，换域名时需同步改（§1.1）。
