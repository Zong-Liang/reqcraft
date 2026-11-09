# 规格格式检查

对按模板维护的 Markdown，可从目标项目运行：

```sh
python3 <reqcraft技能目录>/scripts/check_spec.py docs/requirements/feature.md
```

Python 3.9+。脚本只读指定文件，检查编号格式及重复定义、BR 和 AC 的关联，以及 AC 下的 Given、When、Then、状态。退出码 `0` 表示通过这些结构检查，`1` 表示发现问题，`2` 表示无法读取输入。自由格式文档可由宿主直接按质量规则审阅。
