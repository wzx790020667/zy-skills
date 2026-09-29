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

| 目录          | 放什么                                | 怎么被使用                                                           |
| ------------- | ------------------------------------- | -------------------------------------------------------------------- |
| `scripts/`    | Python / Bash / Node 脚本             | 直接执行，**不占用上下文**。重复写的代码、需要确定性结果的步骤放这里 |
| `references/` | API 文档、schema、详细流程、领域知识  | 需要时才读进上下文。**超长内容务必拆到这里**，保持 SKILL.md 精简     |
| `assets/`     | 模板 PPTX/DOCX、HTML 骨架、图标、字体 | 不进上下文，直接被拷到产出物里用                                     |
