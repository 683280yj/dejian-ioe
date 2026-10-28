# 筹策体验系统 · 香港 VPS 部署记录

执行时间：2026-10-28 02:01 起（北京时间）
目标服务器：华为云 ecs-7a4d，EIP 159.138.136.40（Ubuntu 24.04，2026-11-11 到期）
部署范围：仅体验库（showcase），gunicorn + systemd + Caddy 方案

## 结论：未上线 —— 卡在第 1 步，无可用 SSH 通道

## 第 1 步：SSH 通道验证（失败，停在此处）

服务器只允许公钥登录（与渚交接文档一致）。本机现有两把密钥均已试，均被拒
（`Permission denied (publickey)`）：

| 密钥 | 指纹 | 试过的用户名 | 结果 |
| --- | --- | --- | --- |
| ~/.ssh/id_ed25519 | SHA256:qWfEYs8TYmZWxboVbSnmnk6s1G4egV97/yx2njETA0w | root、ubuntu、ecs-user | 全部拒绝 |
| ~/.ssh/tunnel-key | SHA256:WZpMXvfjiCKkfrRUwKrlAVBzF60kRVM1A2p6m3DxaG4 | root、ubuntu、ecs-user | 全部拒绝 |

- 本机无 ~/.ssh/config，无其它密钥或现成通道可试。
- 与交接记录吻合：渚的公钥尚未装入服务器（他当时正准备用控制台 VNC 手动加入，中途停止）；
  root 新密码 10/28 凌晨刚重置，只在渚的电脑上，本机没有。

## 后续步骤（第 2–7 步）均未执行

侦察、传代码、建体验库、起 systemd 服务、接 Caddy/域名，全部依赖先登入服务器，
未登入前没有动服务器上的任何东西（sing-box、CPA、muse2api 等既有服务未受任何影响）。

## 解卡需要用户二选一

1. **让渚把公钥装上**（他在做的就是这件事）：把本机公钥
   `~/.ssh/id_ed25519.pub`（指纹见上表）通过华为云控制台 VNC 登录后追加到
   `/root/.ssh/authorized_keys`，装好告诉我即可，我接着从第 2 步往下部署。
2. **提供新 root 密码**（渚重置的那个）：拿到后我先用密码登入装公钥，
   再改回纯公钥通道部署。密码请走安全渠道给，不要发在公开群里。

## 备注

- 本地部署与逐页测试已在此前完成并全绿（见《本地部署测试报告.md》），
  代码与链条就绪，通道一通即可按原计划继续：侦察端口 → 传代码到 /workspace/ →
  建体验库（seed → build_showcase_db → create_guest → 存快照）→ gunicorn+systemd →
  Caddy 反代 chouce.idky.tech（DNS 待 Cloudflare 加 A 记录）。
