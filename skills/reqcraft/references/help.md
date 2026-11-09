# 用法

| 任务 | 入口 | 需要的资料 |
|---|---|---|
| 澄清需求 | `reqcraft-analyze` | PRD、用户故事或变更说明 |
| 生成验收规格 | `reqcraft-spec` | 需求资料，可补充现有规格与相关仓库 |
| 验收审计 | `reqcraft-audit` | 现有规格，可补充 PRD、源码与已有运行报告 |

Codex 使用 `$reqcraft-spec` 等入口。Claude Code 独立安装使用 `/reqcraft-spec`，插件安装使用 `/reqcraft:reqcraft-spec`。只有主技能入口时，可写 `$reqcraft spec` 或 `/reqcraft spec`，也可直接描述任务。

默认在对话中交付。需要写文件时在请求中指定创建或更新，仓库有既有规格时直接引用。审计只读已有资料，业务实现和测试执行由下游任务处理。
