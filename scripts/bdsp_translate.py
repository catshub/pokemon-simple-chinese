#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BDSP JSON 翻译落盘脚本
- 处理 common_msbt_korean_Export → common_simp_chinese_msbt_Export
- 处理 logo_dia_ko_Export、text_dia_ko_op_pushbutton_Export → 对应简体中文导出目录
- 处理 korean_Export → simp_chinese_Export

策略：
- 优先按文件后缀匹配已有人和繁中文文件；使用 labelName 作为键对齐 wordDataArray
- common 集使用现有 simp_chinese_* 文件直接对齐；若缺失则从 trad_chinese_* 转简体处理
- korean_Export 集使用 trad_chinese_Export 对齐后繁转简；若缺失/不匹配，按内置术语表做最小替换
- 保留原 JSON 结构、键、非文本字段；仅替换 wordDataArray 内的 str（或直接采用中文文件的 wordDataArray）

注意：
- 部分资产索引 JSON（logo_dia/text_dia/korean.json）不含 labelDataArray 文本，直接复制到简体目录即可
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

import orjson
from opencc import OpenCC

REPO_ROOT = Path('pokemon-simple-chinese')

# 路径常量
COMMON_KO_DIR = REPO_ROOT / 'common_msbt_korean_Export'
COMMON_BASE_DIR = REPO_ROOT / 'common_msbt_Export'
COMMON_SC_OUT = REPO_ROOT / 'common_simp_chinese_msbt_Export'

LOGO_KO_DIR = REPO_ROOT / 'logo_dia_ko_Export'
TEXT_KO_DIR = REPO_ROOT / 'text_dia_ko_op_pushbutton_Export'
LOGO_SC_OUT = REPO_ROOT / 'logo_dia_simp_chinese_Export'
TEXT_SC_OUT = REPO_ROOT / 'text_dia_simp_chinese_op_pushbutton_Export'

KO_EXPORT_DIR = REPO_ROOT / 'korean_Export'
TRAD_EXPORT_DIR = REPO_ROOT / 'trad_chinese_Export'
SC_EXPORT_OUT = REPO_ROOT / 'simp_chinese_Export'

# OpenCC 转换器：繁 → 简
opencc_t2s = OpenCC('t2s')

# 最小韩→中术语替换（兜底用）
KOR_CN_TERMS = [
    # 常用 UI/系统
    ('포켓몬', '宝可梦'), ('타입', '属性'), ('레벨', '等级'), ('HP', 'HP'), ('MP', 'MP'),
    ('공격', '攻击'), ('방어', '防御'), ('특수공격', '特攻'), ('특공', '特攻'), ('특수방어', '特防'), ('특방', '特防'), ('스피드', '速度'),
    ('상태', '状态'), ('기술', '招式'), ('이름', '名称'), ('메모', '备注'), ('라이선스', '许可证'), ('트레이너', '训练家'),
    ('박스', '盒子'), ('가방', '背包'), ('아이템', '道具'), ('없음', '无'), ('도감', '图鉴'), ('진화', '进化'), ('리본', '缎带'),
    ('경고', '警告'), ('에러', '错误'), ('설정', '设置'), ('선택', '选择'), ('확인', '确定'), ('취소', '取消'), ('저장', '保存'), ('불러오기', '载入'),
]

# 文件读写封装

def load_json(path: Path) -> Any:
    with path.open('rb') as f:
        return orjson.loads(f.read())


def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # 使用 orjson，紧凑序列化，确保中文不转义
    content = orjson.dumps(data, option=orjson.OPT_APPEND_NEWLINE | orjson.OPT_NON_STR_KEYS)
    with path.open('wb') as f:
        f.write(content)


# 工具函数

def get_suffix_after_prefix(filename: str, prefix: str) -> Optional[str]:
    if filename.startswith(prefix):
        return filename[len(prefix):]
    return None


def build_label_map_from_msbt(json_obj: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """从含 labelDataArray 的 JSON 构建 labelName → wordDataArray 映射"""
    out: Dict[str, List[Dict[str, Any]]] = {}
    arr = json_obj.get('labelDataArray')
    if not isinstance(arr, list):
        return out
    for it in arr:
        name = it.get('labelName')
        wd = it.get('wordDataArray')
        if name is not None and isinstance(wd, list):
            out[name] = wd
    return out


def t2s_str(s: str) -> str:
    try:
        return opencc_t2s.convert(s)
    except Exception:
        return s


def kor_min_translate(s: str) -> str:
    out = s
    for k, v in KOR_CN_TERMS:
        out = out.replace(k, v)
    return out


def replace_worddata_strs(dst_worddata: List[Dict[str, Any]], src_worddata: List[Dict[str, Any]], convert_t2s: bool = False) -> List[Dict[str, Any]]:
    """按源中文 wordDataArray 替换目标的文本；默认复制整个条目（含 strWidth），以确保宽度等与中文保持一致。
    若 convert_t2s=True，对 src_worddata 中的 str 做繁转简。
    """
    # 直接深拷贝 src_worddata（但 orjson 已返回 Python dict/list，可直接复制内容实例）
    new_wd: List[Dict[str, Any]] = []
    for item in src_worddata:
        new_item = dict(item)
        if isinstance(new_item.get('str'), str):
            new_item['str'] = t2s_str(new_item['str']) if convert_t2s else new_item['str']
        new_wd.append(new_item)
    return new_wd


def process_common() -> Dict[str, Any]:
    summary = {
        'processed_files': [],
        'aligned_by_simp': 0,
        'aligned_by_trad_t2s': 0,
        'fallback_translated': 0,
    }
    if not COMMON_KO_DIR.exists():
        return summary

    for ko_path in sorted(COMMON_KO_DIR.glob('korean_*.json')):
        fname = ko_path.name  # korean_xxx.json
        suffix = get_suffix_after_prefix(fname, 'korean_')
        if not suffix:
            continue
        # 目标输出
        out_path = COMMON_SC_OUT / f'simp_chinese_{suffix}'

        ko_obj = load_json(ko_path)
        ko_arr = ko_obj.get('labelDataArray')
        if not isinstance(ko_arr, list):
            # 结构异常，直接复制
            save_json(ko_obj, out_path)
            summary['processed_files'].append(str(out_path))
            continue

        # 优先用 simp_chinese 对齐
        simp_path = COMMON_BASE_DIR / f'simp_chinese_{suffix}'
        trad_path = COMMON_BASE_DIR / f'trad_chinese_{suffix}'
        label_map: Dict[str, List[Dict[str, Any]]] = {}
        convert_t2s = False
        if simp_path.exists():
            simp_obj = load_json(simp_path)
            label_map = build_label_map_from_msbt(simp_obj)
            summary['aligned_by_simp'] += 1
        elif trad_path.exists():
            trad_obj = load_json(trad_path)
            label_map = build_label_map_from_msbt(trad_obj)
            convert_t2s = True
            summary['aligned_by_trad_t2s'] += 1

        # 遍历并替换
        for it in ko_arr:
            name = it.get('labelName')
            src_wd = None
            if name in label_map:
                src_wd = label_map[name]
                it['wordDataArray'] = replace_worddata_strs(it.get('wordDataArray', []), src_wd, convert_t2s)
            else:
                # 兜底：最小术语替换
                wd = it.get('wordDataArray')
                if isinstance(wd, list):
                    changed = False
                    for w in wd:
                        s = w.get('str')
                        if isinstance(s, str):
                            new_s = kor_min_translate(s)
                            if new_s != s:
                                w['str'] = new_s
                                changed = True
                    if changed:
                        summary['fallback_translated'] += 1
        save_json(ko_obj, out_path)
        summary['processed_files'].append(str(out_path))
    return summary


def process_logo_text() -> Dict[str, Any]:
    summary = {'logo': None, 'text': None}
    # logo_dia
    logo_in = LOGO_KO_DIR / 'logo_dia_ko.json'
    logo_out = LOGO_SC_OUT / 'logo_dia_simp_chinese.json'
    if logo_in.exists():
        obj = load_json(logo_in)
        save_json(obj, logo_out)
        summary['logo'] = str(logo_out)
    # text_dia
    text_in = TEXT_KO_DIR / 'text_dia_ko_op_pushbutton.json'
    text_out = TEXT_SC_OUT / 'text_dia_simp_chinese_op_pushbutton.json'
    if text_in.exists():
        obj = load_json(text_in)
        save_json(obj, text_out)
        summary['text'] = str(text_out)
    return summary


def process_korean_export() -> Dict[str, Any]:
    summary = {
        'processed_files': [],
        'aligned_by_trad_t2s': 0,
        'copied_untranslated_struct': 0,
        'labels_aligned': 0,
        'labels_fallback_translated': 0,
    }
    if not KO_EXPORT_DIR.exists():
        return summary

    SC_EXPORT_OUT.mkdir(parents=True, exist_ok=True)

    # 处理所有 korean_*.json
    for ko_path in sorted(KO_EXPORT_DIR.glob('korean_*.json')):
        fname = ko_path.name
        suffix = get_suffix_after_prefix(fname, 'korean_')
        if not suffix:
            continue
        out_path = SC_EXPORT_OUT / f'simp_chinese_{suffix}'

        ko_obj = load_json(ko_path)
        ko_arr = ko_obj.get('labelDataArray')
        # 尝试匹配繁体源
        trad_path = TRAD_EXPORT_DIR / f'trad_chinese_{suffix}'
        if trad_path.exists():
            trad_obj = load_json(trad_path)
            label_map = build_label_map_from_msbt(trad_obj)
            if isinstance(ko_arr, list) and label_map:
                for it in ko_arr:
                    name = it.get('labelName')
                    src_wd = label_map.get(name)
                    if src_wd is not None:
                        it['wordDataArray'] = replace_worddata_strs(it.get('wordDataArray', []), src_wd, convert_t2s=True)
                        summary['labels_aligned'] += 1
                    else:
                        # 兜底最小术语替换
                        wd = it.get('wordDataArray')
                        if isinstance(wd, list):
                            changed = False
                            for w in wd:
                                s = w.get('str')
                                if isinstance(s, str):
                                    new_s = kor_min_translate(s)
                                    if new_s != s:
                                        w['str'] = new_s
                                        changed = True
                            if changed:
                                summary['labels_fallback_translated'] += 1
                summary['aligned_by_trad_t2s'] += 1
                save_json(ko_obj, out_path)
                summary['processed_files'].append(str(out_path))
            else:
                # 结构不含 labelDataArray：直接复制
                save_json(ko_obj, out_path)
                summary['copied_untranslated_struct'] += 1
                summary['processed_files'].append(str(out_path))
        else:
            # 没有繁体源：若含 labelDataArray，做最小术语替换；否则直接复制
            if isinstance(ko_arr, list):
                for it in ko_arr:
                    wd = it.get('wordDataArray')
                    if isinstance(wd, list):
                        for w in wd:
                            s = w.get('str')
                            if isinstance(s, str):
                                w['str'] = kor_min_translate(s)
                save_json(ko_obj, out_path)
                summary['labels_fallback_translated'] += 1
                summary['processed_files'].append(str(out_path))
            else:
                save_json(ko_obj, out_path)
                summary['copied_untranslated_struct'] += 1
                summary['processed_files'].append(str(out_path))
    # 额外处理根文件 korean.json（资产索引），直接复制到 simp_chinese.json
    root_ko = KO_EXPORT_DIR / 'korean.json'
    if root_ko.exists():
        obj = load_json(root_ko)
        out_path = SC_EXPORT_OUT / 'simp_chinese.json'
        save_json(obj, out_path)
        summary['processed_files'].append(str(out_path))
    return summary


def main():
    report = {
        'common': process_common(),
        'logo_text': process_logo_text(),
        'korean_export': process_korean_export(),
    }
    # 将报告打印到 stdout
    print(orjson.dumps(report, option=orjson.OPT_INDENT_2).decode())


if __name__ == '__main__':
    main()
