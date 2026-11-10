# ReqCraft

需求分析、验收规格和只读验收审计。由 Codex 或 Claude Code 直接加载技能。分析时以 PRD 和已确认决策为准，审计时区分静态实现线索与已有运行证据。

## 安装

### Codex

在 Codex 对话中发送下面这句话，安装主技能和四个快捷入口。

```text
$skill-installer 从 https://github.com/Zong-Liang/reqcraft 的 main 分支安装 skills/reqcraft、skills/reqcraft-analyze、skills/reqcraft-spec、skills/reqcraft-audit 和 skills/reqcraft-help，全部放到 ~/.agents/skills/。
```

安装后可用 `$reqcraft-spec` 等入口。若技能列表没有显示 ReqCraft，可重启 Codex。 [Codex 技能文档](https://learn.chatgpt.com/docs/build-skills#install-curated-skills-for-local-use)

### Claude Code

Claude Code 2.1.292 或更新版本可在终端用一条命令添加市场并安装插件。 [Claude Code 插件安装文档](https://code.claude.com/docs/en/plugins/install#add-a-marketplace-and-install-in-one-command)

```sh
claude plugin install reqcraft --marketplace Zong-Liang/reqcraft
```

较早版本可在 Claude Code 对话中依次运行以下命令，并按界面提示选择安装范围。

```text
/plugin marketplace add Zong-Liang/reqcraft
/plugin install reqcraft@reqcraft
```

### 本地安装和更新

已下载仓库时，可将 `skills/` 下的五个目录一起复制到 Codex 的 `~/.agents/skills/`、项目的 `.agents/skills/`，或 Claude Code 的 `~/.claude/skills/`。只用主入口时，复制 `skills/reqcraft/` 即可。Claude Code 也可用 `/plugin marketplace add /实际路径/reqcraft` 添加本地仓库或解压后的插件包，再安装 `reqcraft@reqcraft`。

也可在仓库根目录运行 `python3 tools/install_skill.py --host codex`，Claude Code 独立安装用 `--host claude`。加 `--dry-run` 只预览，加 `--replace` 会先备份内容不同的旧入口再更新。用 `--dest` 可指定技能父目录。安装器需要 macOS 或 Linux 和 Python 3.9+。

## 使用

| Codex | Claude Code 插件 | 交付物 |
|---|---|---|
| `$reqcraft-analyze` | `/reqcraft:reqcraft-analyze` | 场景、规则、状态和待确认项 |
| `$reqcraft-spec` | `/reqcraft:reqcraft-spec` | Given–When–Then、验收责任和验证层次 |
| `$reqcraft-audit` | `/reqcraft:reqcraft-audit` | 规格缺口、静态实现线索和已有验证证据 |
| `$reqcraft-help` | `/reqcraft:reqcraft-help` | 用法和范围 |

Claude Code 独立技能使用 `/reqcraft-spec` 等入口。只有主技能时可用 `$reqcraft spec` 或 `/reqcraft spec`。

```text
$reqcraft-spec 将 docs/prd/reminder.md 转为验收规格，保存到 docs/requirements/reminder.md。
$reqcraft-audit 审计 docs/requirements/reminder.md，核对相关源码与 reports/reminder.xml。
```

默认在对话交付。用户明确指定写入时，沿用目标仓库的规格目录和稳定编号。审计可读取源码、测试源码和已有报告，测试执行由下游任务负责。

## 分发与检查

```sh
python3 -B -m unittest discover -s tests -v
python3 tools/build_package.py
```

`dist/` 下有 SHA-256 校验文件和候选包清单。

| 包 | 用途 |
|---|---|
| `reqcraft.zip` | 仅主技能，包含全部工作流 |
| `reqcraft-skills.zip` | 将解压后 `reqcraft-skills/` 内五个目录放到宿主技能目录 |
| `reqcraft-plugin.zip` | 将解压后 `reqcraft/` 作为 Claude Code 本地 marketplace |

主技能及共享规则见 [SKILL.md](skills/reqcraft/SKILL.md)。可选的 [规格格式检查](skills/reqcraft/references/scripts-check.md) 只读 Markdown，校验编号、追踪关系和验收字段。

## 许可

采用 [MIT 许可证](LICENSE)。
