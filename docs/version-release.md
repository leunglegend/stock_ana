# 版本发布与记录（Version & Release）

本平台每次「可发布」里程碑都用 **git 日期 tag + GitHub Release** 记录，保证每个版本的**发布内容和时间**随时可回查。

## 触发条件

一次功能/大版本完成并合入 `main` 后（可部署、可回退的稳定点），即视为一个可发布版本。

## 发布流程

每个可发布里程碑按以下步骤执行（repo 为 public：`leunglegend/stock_ana`）：

1. **打日期 tag**（annotated，指向该版 `main` HEAD，日期取发布当天，如 `2026-09-04`）

   ```bash
   git tag -a 2026-09-04 -m "美股复盘（方向一）合入 main"
   ```

2. **推送 tag 到远端**

   ```bash
   git push origin 2026-09-04
   ```

3. **建 GitHub Release**（发布说明写清本版交付内容 / 数据口径 / 测试结果 / 已知项）

   ```bash
   gh release create 2026-09-04 \
     --title "美股复盘（方向一）" \
     --notes-file /tmp/release-2026-09-04.md
   ```

4. **校正 Latest 标记**：若同时有多个 Release，需把 Latest 指到**代码最新**的那一版（按创建时间新建的旧基线会被 GitHub 误标为 Latest）

   ```bash
   gh release edit 2026-09-04 --latest   # 把 Latest 给代码最新版
   ```

## 查询方式

```bash
gh release list                 # 所有版本 + 发布时间
gh release view 2026-09-04      # 某版发布说明全文
git show 2026-09-04             # tag 指向的 commit 与打标时刻
git tag -n                      # 本地 tag 一览
```

网页：`https://github.com/leunglegend/stock_ana/releases`

> 想「随时切换版本」时用 tag 检出对应 commit（会进入 detached HEAD）；想部署某稳定版时用其 tag 而非分支。

## 已发布版本

| Tag | 指向 commit | 内容 | 发布时间 | Release |
|-----|-------------|------|---------|---------|
| `2026-09-03` | `main@baa738b` | A股稳定基线（美股功能合入前，可回退基线） | 2026-09-04 | https://github.com/leunglegend/stock_ana/releases/tag/2026-09-03 |
| `2026-09-04` | `main@ec06a80b` | 美股复盘方向一（/us 页 + Dashboard 卡） | 2026-09-04 | https://github.com/leunglegend/stock_ana/releases/tag/2026-09-04 |

> 「发布时间」为该版 Release 实际创建（发布）时间（UTC）；`Tag` 名取该功能对应的日期，便于按日期记忆。新版本发布后在此追加一行并提交。
