# 配色 V2（Riep 指定参考：docs/color-reference.html「酿见 · 白酒经营智能决策蓝图」）——取代 DESIGN_SPEC.md 第 1 节的颜色

| Token | 值 | 用途 |
|---|---|---|
| paper | #fbf8f3 | 页面底色 |
| card | #fffdf9 | 卡片/表格/表单 |
| ink | #241e1b | 正文、深色区块（深底可用 #211b18 / #2d2523） |
| muted | #7c716c | 次要文字 |
| line | #e8dfd7 | 细线分隔 |
| wine | #6e1f2c | **人的决定与执行**：采纳/审批/发货按钮、待拍板、当前导航 |
| wine-2 | #a43f45 | wine 的悬停/强调、风险警示 |
| gold | #c99a57 | **AI 产出**：建议、测算值、AI 标签（取代原靛蓝 #5149cf）；深底上用 #e4b76f |
| green | #43685e | 正常/达标/回测改善 |
| shadow | 0 18px 44px rgba(57,35,27,.08) | 卡片轻投影（允许，取代"无阴影"） |

字体：标题 Georgia / "Songti SC" / Noto Serif SC 衬线；正文系统无衬线（PingFang SC / Microsoft YaHei）；数字标签等宽 ui-monospace。
原则不变：AI=金、人=酒红，两者语义不可混用；颜色只用上表。

## 气质补充（Riep 2026-10-27：酱香酒，要有历史厚重感；参考 docs/mood-reference.png）
- 首页 Hero、登录页、侧栏用**深色区块**：#211b18 / #2d2523 底，标题米白 #fbf8f3，重点词酒红 #a43f45，小标签暗金 #e4b76f（等宽大写，如 BAIJIU OPERATING SYSTEM）。
- 内容区仍用纸底 #fbf8f3 + 卡片 #fffdf9，保证表格易读；深浅交替而不是全站暗色。
- 意象：竹影、老木桌/木格窗、陶坛、酒瓶礼盒、印章；暗调暖光，低饱和。主视觉可用原创生成的产品场景图（不得仿真实品牌如习酒/茅台的瓶标与字样，瓶身用「德鉴」或无字）。
- 主按钮酒红 #6e1f2c 实心圆角小胶囊；次按钮深底描边。
