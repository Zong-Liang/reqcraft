#!/usr/bin/env python3
"""Check IDs, trace links, and acceptance fields in ReqCraft Markdown."""

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys


ID = re.compile(r"\b(?:SC|BR|AC|Q)-[0-9]{2,}\b")
SECTIONS = {
    "业务场景": "SC",
    "业务规则与状态": "BR",
    "业务验收标准": "AC",
    "待确认事项": "Q",
}
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
AC_TITLE = re.compile(r"^#{3,6}\s+`?(AC-[^\s`：:]+)`?(?=[\s：:]|$)(.*)$")
FIELD = re.compile(r"^\s*[-*]\s+\*\*(Given|When|Then|状态)\*\*[\s:：]*(.*)$")
TABLE_SEPARATOR = re.compile(r"(?<!\\)(?:\\\\)*\|")


@dataclass
class Entry:
    identifier: str
    line: int
    refs: set
    fields: dict = field(default_factory=dict)


def document_lines(markdown):
    fence = None
    in_comment = False
    for line_number, text in enumerate(markdown.splitlines(), 1):
        match = FENCE.match(text)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            continue
        if not in_comment and match:
            fence = match[1]
            continue
        if in_comment:
            _, end, text = text.partition("-->")
            if not end:
                continue
            in_comment = False
        text, start, comment = text.partition("<!--")
        if start and "-->" not in comment:
            in_comment = True
        yield line_number, text


def check(markdown):
    entries = {}
    errors = []
    section = None
    current_ac = None

    def register(identifier, line, text):
        if not ID.fullmatch(identifier) or not identifier.startswith(section + "-"):
            errors.append((line, f"编号格式错误 {identifier}"))
            return None
        if identifier in entries:
            errors.append((line, f"重复定义 {identifier}，首次定义在第 {entries[identifier].line} 行"))
            return None
        entry = Entry(identifier, line, set(ID.findall(text)))
        entries[identifier] = entry
        return entry

    for line, text in document_lines(markdown):
        if text.startswith("## "):
            title = re.sub(r"^[0-9]+[.、]\s*", "", text[3:].strip())
            section = SECTIONS.get(title)
            current_ac = None
            continue
        if section == "AC":
            match = AC_TITLE.match(text)
            if match:
                # Scenario and rule links belong in the AC heading.
                current_ac = register(match[1], line, match[2])
            elif text.startswith("###"):
                current_ac = None
            elif current_ac and (match := FIELD.match(text)):
                label, value = match.groups()
                if label in current_ac.fields:
                    errors.append((line, f"{current_ac.identifier} 重复填写 {label}"))
                current_ac.fields[label] = value.strip()
        elif section in ("SC", "BR", "Q") and text.strip().startswith("|"):
            cells = TABLE_SEPARATOR.split(text.strip())
            identifier = cells[1].strip().strip("`")
            if identifier.startswith(("SC-", "BR-", "Q-", "AC-")):
                link_column = {"BR": 3, "Q": 3}.get(section, len(cells))
                links = cells[link_column] if link_column < len(cells) else ""
                register(identifier, line, links)

    if not any(entry.identifier.startswith("AC-") for entry in entries.values()):
        errors.append((1, "未找到 AC 定义，请使用模板的业务验收标准章节"))

    for entry in entries.values():
        prefix = entry.identifier.split("-")[0]
        required = {"BR": ("SC",), "AC": ("SC", "BR")}.get(prefix, ())
        for target in required:
            if not any(ref.startswith(target + "-") for ref in entry.refs):
                errors.append((entry.line, f"{entry.identifier} 缺少 {target} 关联"))
        for ref in sorted(entry.refs - entries.keys()):
            errors.append((entry.line, f"{entry.identifier} 引用了未定义的 {ref}"))
        if prefix == "AC":
            for label in ("Given", "When", "Then", "状态"):
                value = entry.fields.get(label, "")
                if not value or value.startswith("<"):
                    errors.append((entry.line, f"{entry.identifier} 缺少有效的 {label}"))
            status = entry.fields.get("状态", "")
            if status and status not in {"已确认", "草案待确认", "已废弃"}:
                errors.append((entry.line, f"{entry.identifier} 状态无效 {status}"))
    return sorted(errors)


def main():
    parser = argparse.ArgumentParser(description="只读检查 ReqCraft Markdown 规格结构。")
    parser.add_argument("specification", type=Path)
    args = parser.parse_args()
    try:
        if not args.specification.is_file():
            raise ValueError("输入须为普通文件")
        markdown = args.specification.read_text(encoding="utf-8-sig")
    except (OSError, ValueError) as error:
        print(f"{args.specification}: {error}", file=sys.stderr)
        return 2

    errors = check(markdown)
    for line, message in errors:
        print(f"{args.specification}:{line}: {message}", file=sys.stderr)
    if errors:
        return 1
    print(f"{args.specification} 规格结构检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
