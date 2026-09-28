# AGENTS.md

本仓库是 zy（泽音）的个人 Skills 源码仓库，由 AI 参与维护。改动前先读这里。

## 铁律

1. **源码唯一**。`skills/` 是唯一可编辑的地方。`~/.workbuddy/skills/` 下的同名目录是安装产物（软链或副本），不要直接改那里——改了不会进 Git，下次安装会被覆盖。
2. **目录名 = frontmatter 的 `name`**，两者必须一致，小写 kebab-case，≤40 字符。
3. **`description` 是触发开关**。必须写清「做什么」和「何时触发」，带用户真实会说的关键词。不要留 TODO，不要写空话。
4. **frontmatter 保留 `agent_created: true`**，否则后续工具无法自动修改/删除这个 skill。
5. **不要引入额外元数据文件**（`_meta.json`、`registry.yaml` 之类）。索引是从 SKILL.md 自动生成的，加第二套清单只会不同步。

## 新增或修改 skill 的流程

```bash
make new name=<skill-name>   # 或 make validate 检查已有改动
# 写 SKILL.md；需要脚本/文档/模板再建 scripts/ references/ assets/
make check                   # 提交前必跑：validate + index 一致性
make install                 # 装到本机（软链）
git commit
```

提交前自检清单：

- `make validate` 零错误
- `SKILL.md` 里没有 TODO 残留
- 正文控制在 5000 词以内，超了往 `references/` 拆
- `scripts/` `references/` `assets/` 若在 SKILL.md 里被引用，路径必须真实存在
- 脚本可执行（`chmod +x`），且不依赖本机绝对路径：用相对 skill 目录的路径或环境变量

## 仓库级工具的边界

`scripts/` 下的是**仓库工具**，不属于任何 skill，不会被安装到 `~/.workbuddy/skills/`。要改它们先确认是否会影响 CI（`.github/workflows/validate.yml` 依赖 CLI：`validate.py`、 `update_index.py --check`）。

## 不确定的处理

发现规范冲突或缺少某项约定时，不要自己发明——按 `~/.workbuddy/skills/../..` 下的官方 `skill-creator` 规范走，并在最终回复里明确列出 `TODO(待确认)`。
