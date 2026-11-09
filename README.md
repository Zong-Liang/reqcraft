# ReqCraft

需求分析、验收规格和只读验收审计。由 Codex 或 Claude Code 直接加载技能。分析时以 PRD 和已确认决策为准，审计时区分静态实现线索与已有运行证据。

## 安装

Codex 用户级安装。安装后开启新会话。

```sh
python3 tools/install_skill.py --host codex
```

项目级安装可用 `--dest /目标仓库/.agents/skills`。先查看安装范围可加 `--dry-run`。更新时用 `--replace`，不同内容的旧入口会备份到技能父目录之外，路径见安装输出。

Claude Code 可从本地仓库或解压后的插件包安装。把示例路径替换为实际目录。

```text
/plugin marketplace add /path/to/reqcraft
/plugin install reqcraft@reqcraft
```

也可运行 `python3 tools/install_skill.py --host claude` 直接安装独立技能。安装器需要 macOS 或 Linux 和 Python 3.9+。通过 ZIP 或插件安装后，宿主使用技能无需 Python，规格格式检查脚本除外。

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
