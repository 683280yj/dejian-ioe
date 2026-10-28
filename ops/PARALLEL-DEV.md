# 并行开发与 GitHub 同步约定（2026-10-28 定）

两边并行开发，GitHub 私有仓 `683280yj/dejian-ioe` 是唯一同步中枢。

## 分支分工

- `main`：用户侧维护。用户在本地开发、直接推 main；助手侧**永不推 main**。
- `vm-dev`：助手（VM）侧工作分支。助手的所有改动提交到 vm-dev 并推到同名远程分支。
- 合并：vm-dev → main 由用户侧发起（GitHub PR 或本地合并后推 main）。
  合并后知会助手一声，助手以合并后的 main 树为新基线再继续 vm-dev。

## 助手侧工具（VM 无 git 凭据，走 GitHub API）

- 推送：`~/workspace/chouce-20261028/push_branch.py 683280yj/dejian-ioe vm-dev`
  —— 禁推 main、引用更新 force=false、远程分叉立即停，不覆盖任何人的提交。
- 检查：`~/workspace/chouce-20261028/sync_check.py`
  —— 只读，比对远程 main / vm-dev 与本地镜像状态，报告用户侧是否有新提交。
- 旧脚本 `push_via_api.py` 会强推 main，**并行期禁用**，仅留作单边恢复用。

## 纪律

- 开工前先跑 sync_check；远程 main 有新提交时，先把新树合进 vm-dev 再动手。
- 两边尽量不改同一文件；热点文件：`inventory/settings.py`、`site/index.html`、`site/site-config.js`。
- 数据库（*.sqlite3）与 *.env 永远不进仓（.gitignore 已排除），两边数据各自独立。
- 助手侧本地历史经 API 镜像后远程 SHA 与本地 SHA 不同、树哈希一致，以树哈希对账。
