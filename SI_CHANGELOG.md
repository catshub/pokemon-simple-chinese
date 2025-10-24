# BDSP 简体中文文本生成（si）变更记录

本分支新增并落盘了《宝可梦 晶灿钻石／明亮珍珠》相关简体中文（语言标识符：si）资源，遵循以英文 JSON 结构为准、文本优先复用繁体的规则。

- 分支：aime/1761285935-bdsp-si-translation
- 生成日期：2025-10-24

目录与命名调整
- 新增 common_si_msbt_Export：以英文版结构为模板，产出 si_ 前缀文件。
- 新增 logo_dia/si 与 text_dia/si：以韩语资产 JSON 为基，按 si 前缀生成。
- 新增 si_Export：将 korean_Export 下全部 JSON 转为 si_ 前缀，文本优先复用 trad_chinese_Export。
- 新增 reports：结构一致性与映射检查报告。

执行原则
- 结构一致：所有 si 产物的键集合、层级与占位符保持与英文版一致（common 范畴以英文模板严格对齐）。
- 文本来源：存在繁体中文对应文本时，直接复制繁体，不做繁转简；缺失场景保留英文文本并在报告中标记。
- 命名统一：目录与文件均使用 “si” 标识，不再使用 “simp_chinese”。

质量报告
- reports/common_structure_check.json：common 范畴英文与 si 结构一致性核对。
- reports/korean_si_mapping_check.json：korean_Export → si_Export 的映射覆盖情况统计。

说明
- logo_dia/text_dia 的 PNG 资产未随本次产物生成，JSON 已按 “si” 路径与 AssetBundle 名称对齐，可根据后续需要补充素材文件。
