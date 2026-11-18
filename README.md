# ReqCraft

需求分析、验收规格和只读验收审计。由 Codex 或 Claude Code 直接加载技能。分析时以 PRD 和已确认决策为准，审计时区分静态实现线索与已有运行证据。

## 安装与更新

ReqCraft 的主技能和四个快捷入口随同一个插件版本更新。以下命令在终端运行。

### Codex

首次安装时添加 ReqCraft 的 Git 市场，再安装插件。

```sh
codex plugin marketplace add Zong-Liang/reqcraft --ref main
codex plugin add reqcraft@reqcraft
```

后续升级只需刷新这个市场。升级后可查看安装状态，并在新对话中选择技能。

```sh
codex plugin marketplace upgrade reqcraft
codex plugin list --marketplace reqcraft
```

### Claude Code

首次安装可用以下命令（Claude Code 2.1.292 及以上）。

```sh
claude plugin install reqcraft --marketplace Zong-Liang/reqcraft
```

支持插件的较早版本可先运行 `claude plugin marketplace add Zong-Liang/reqcraft`，再运行 `claude plugin install reqcraft@reqcraft`。

```sh
claude plugin update reqcraft@reqcraft
```

更新后在当前会话运行 `/reload-plugins` 或重新启动 Claude Code。若希望自动更新，可在 `/plugin` 的 Marketplaces 页面为 reqcraft 开启该选项。[Claude Code 插件更新说明](https://code.claude.com/docs/en/plugins/install#keep-plugins-updated)

### 从独立安装迁移

通过 `$skill-installer`、本地安装器或复制目录安装的用户，先安装对应宿主的插件并确认版本，再把原技能目录中的 `reqcraft`、`reqcraft-analyze`、`reqcraft-spec`、`reqcraft-audit`、`reqcraft-help` 移到技能搜索路径之外备份。只安装过主技能时只需移动 `reqcraft`。原目录取决于当时选择的用户级或项目级安装位置。备份会保留本地修改，新会话通过插件入口加载新版。

## 使用

| Codex | Claude Code 插件 | 交付物 |
|---|---|---|
| `$reqcraft:reqcraft-analyze` | `/reqcraft:reqcraft-analyze` | 场景、规则、状态和待确认项 |
| `$reqcraft:reqcraft-spec` | `/reqcraft:reqcraft-spec` | Given–When–Then、验收责任和验证层次 |
| `$reqcraft:reqcraft-audit` | `/reqcraft:reqcraft-audit` | 规格缺口、静态实现线索和已有验证证据 |
| `$reqcraft:reqcraft-help` | `/reqcraft:reqcraft-help` | 用法和范围 |

Claude Code 独立技能使用 `/reqcraft-spec` 等入口。只有主技能时可用 `$reqcraft spec` 或 `/reqcraft spec`。

```text
$reqcraft:reqcraft-spec 将 docs/prd/reminder.md 转为验收规格，保存到 docs/requirements/reminder.md。
$reqcraft:reqcraft-audit 审计 docs/requirements/reminder.md，核对相关源码与 reports/reminder.xml。
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
| `reqcraft-plugin.zip` | 将解压后的 `reqcraft/` 作为 Codex 或 Claude Code 本地市场；在线升级使用上面的 Git 市场 |

主技能及共享规则见 [SKILL.md](skills/reqcraft/SKILL.md)。可选的 [规格格式检查](skills/reqcraft/references/scripts-check.md) 只读 Markdown，校验编号、追踪关系和验收字段。

## 许可

采用 [MIT 许可证](LICENSE)。
