# zy-skills

个人 Skills 仓库。所有自研 skill 的源码都放在这里，用 Git 做版本管理，安装到本机 `~/.workbuddy/skills/` 供 WorkBuddy 使用。

核心约定：**仓库里是源码，`~/.workbuddy/skills/` 里只是安装结果。** 不要直接在 skills 安装目录里改 skill，那里改的东西不会进 Git。

## 目录结构

```
zy-skills/
├── README.md                      # 本文件 + Skill 索引（索引由脚本自动生成）
├── AGENTS.md                      # 给 AI 看的仓库约定
├── Makefile                       # 常用命令入口
├── skills/                        # 所有 skill 源码，每个子目录一个 skill
│   ├── _template/                 # 新 skill 模板（下划线开头，不会被安装）
│   │   └── SKILL.md
│   └── <skill-name>/              # 一个具体 skill
│       ├── SKILL.md               # 必须。元数据 + 正文指令
│       ├── scripts/               # 可选。可执行脚本
│       ├── references/            # 可选。按需读进上下文的文档
│       └── assets/                # 可选。产出物模板/图片/字体
├── scripts/                       # 仓库级工具，不属于任何 skill
│   ├── new_skill.py               # 新建 skill
│   ├── validate.py                # 规范校验
│   ├── install.sh                 # 安装/卸载到本机
│   └── update_index.py            # 重新生成 README 索引
└── .github/workflows/validate.yml # CI：校验 + 索引一致性
```

## 一个标准 Skill 长什么样

最小形态只有一个文件：

```
<skill-name>/
└── SKILL.md
```

复杂一点加上三类可选资源，各自有明确分工，不要混用：

| 目录 | 放什么 | 怎么被使用 |
|------|--------|-----------|
| `scripts/` | Python / Bash / Node 脚本 | 直接执行，**不占用上下文**。重复写的代码、需要确定性结果的步骤放这里 |
| `references/` | API 文档、schema、详细流程、领域知识 | 需要时才读进上下文。**超长内容务必拆到这里**，保持 SKILL.md 精简 |
| `assets/` | 模板 PPTX/DOCX、HTML 骨架、图标、字体 | 不进上下文，直接被拷到产出物里用 |

### SKILL.md 的 frontmatter

```yaml
---
name: my-skill              # 必须，必须与目录名完全一致（小写 kebab-case）
description: 一句话说明做什么 + 何时触发。建议写成第三人称：This skill should be used when ...
agent_created: true         # 建议加上，否则后续无法被工具自动修改/删除
---
```

`name` 和 `description` 决定了 skill 会不会被触发，是整个 skill 里最重要的两行：

- **name**：`^[a-z0-9]+(-[a-z0-9]+)*$`，不超过 40 字符，必须等于目录名。
- **description**：不能含尖括号；要写清「做什么」和「什么情况下用它」，带上用户真正会说的关键词。写得含糊 = 永远不会被触发。

### 正文的组织方式

正文按「另一个 AI 实例拿到就能干活」的标准写，控制在 5000 词以内（中文字也算），超了就往 `references/` 拆。常见骨架按用途选：

- **流程型**（有明确先后顺序）：概述 → 前置条件 → 步骤一 / 步骤二 / … → 校验与兜底
- **任务型**（一组并列能力）：概述 → 快速开始 → 任务 A → 任务 B → …
- **规范型**（标准/风格约束）：概述 → 规则清单 → 正反例 → 检查表
- **能力型**（一个完整系统）：概述 → 核心能力 → 逐个能力展开

用祈使句写指令（"读取 X，然后执行 Y"），不要写"你应该…"。

### 三层渐进加载

1. `name` + `description` — 常驻上下文，约 100 词，决定是否触发
2. `SKILL.md` 正文 — 触发后才加载
3. `scripts/` `references/` `assets/` — 按需加载，脚本可不读直接跑

这就是为什么细节文档要放 references：写进 SKILL.md 会白白吃掉每一轮的上下文。

## 工作流

```bash
# 1. 新建
make new name=wechat-draft-polish

# 2. 编写 skills/wechat-draft-polish/SKILL.md（补完所有 TODO）
#    需要脚本/文档/模板就往 scripts/ references/ assets/ 里加

# 3. 校验
make validate

# 4. 安装到本机
make install            # 软链，改源码即时生效（推荐）
make install-copy       # 副本方式

# 5. 更新 README 索引并提交
make index
git add -A && git commit -m "feat: add wechat-draft-polish"
```

不用 Makefile 也可以：`python3 scripts/new_skill.py <name>`、`python3 scripts/validate.py`、`./scripts/install.sh`。

## 安装与卸载

`./scripts/install.sh` 默认用**软链**，好处是仓库里改一行，本机立刻生效，不用反复同步。

安全行为（重要）：

- 目标位置已存在同名 skill **不会被覆盖**，脚本会跳过并提示。
- 带 `_skillhub_meta.json` / `_knot_meta.json` 的目录判定为市场安装，默认一律跳过。
- 加 `--force` 才会覆盖，且会先把原目录 `mv` 到 `~/.workbuddy/skills_backup/<name>-<时间戳>` 做备份，不会直接删。
- `DRY_RUN=1 ./scripts/install.sh` 可以只看将要发生什么。
- `./scripts/install.sh --uninstall` 只移除本仓库装进去的东西。

目标目录可用环境变量覆盖：`WORKBUDDY_SKILLS_DIR=/some/path ./scripts/install.sh`。

安装后如果 WorkBuddy 没有立刻识别，重开一个会话。

## 收编已有的散落 skill

之前在 `~/.workbuddy/skills/` 里手写过的 skill，可以移进来统一管理：

```bash
mv ~/.workbuddy/skills/<name> skills/<name>
./scripts/install.sh            # 重新装软链回去
```

注意检查里面有没有 `_skillhub_meta.json`（市场安装的元信息），有的话删掉，避免和市场更新冲突。

## 放到 GitHub

```bash
git init
git add -A
git commit -m "init: skills repo scaffold"
git branch -M main
git remote add origin git@github.com:<你的账号>/zy-skills.git
git push -u origin main
```

CI 会在 push 和 PR 时跑两件事：校验所有 skill 是否合规（含 TODO 残留检查）、确认 README 索引和源码一致。默认仓库建议设为 Private。

## Skill 索引

<!-- SKILL_INDEX_START -->

还没有任何 skill。用 `python3 scripts/new_skill.py <name>` 创建第一个。

<!-- SKILL_INDEX_END -->
