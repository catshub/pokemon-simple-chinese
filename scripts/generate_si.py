#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BDSP Simplified Chinese (si) Text Generator

SOP summary implemented:
- common: use English JSON structure as template; for text fields, prefer Traditional Chinese from common_msbt_Export/trad_chinese_*. If missing, fallback to English text (optionally report as TODO for translation). Output to common_si_msbt_Export with si_ prefix.
- logo_dia/text_dia: build si JSON in logo_dia/si and text_dia/si, mirroring structure & naming from existing ko/tr assets but with 'si' prefix.
- korean_Export: for each korean_*.json, prefer text from trad_chinese_Export/trad_chinese_*. Output to si_Export with si_ prefix.
- Quality check: verify keys/labels alignment, emit simple diff reports under reports/.

Notes:
- We DO NOT convert Traditional Chinese to Simplified per SOP; we directly copy Traditional text when available.
- We preserve English structural fields for common outputs (keys, label arrays, style info, tag arrays, placeholders etc.).
- We keep numeric fields like strWidth intact from the template to avoid unexpected layout changes.
"""

import json
import os
import sys
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
# project root is one level up from scripts/
PROJECT_ROOT = os.path.abspath(os.path.join(REPO_ROOT, os.pardir))

COMMON_EXPORT_DIR = os.path.join(PROJECT_ROOT, 'common_msbt_Export')
COMMON_KO_EXPORT_DIR = os.path.join(PROJECT_ROOT, 'common_msbt_korean_Export')
COMMON_SI_EXPORT_DIR = os.path.join(PROJECT_ROOT, 'common_si_msbt_Export')

LOGO_DIA_KO_EXPORT_DIR = os.path.join(PROJECT_ROOT, 'logo_dia_ko_Export')
LOGO_DIA_TR_EXPORT_DIR = os.path.join(PROJECT_ROOT, 'logo_dia_tr_Export')
LOGO_DIA_SI_DIR = os.path.join(PROJECT_ROOT, 'logo_dia', 'si')

TEXT_DIA_KO_OP_EXPORT_DIR = os.path.join(PROJECT_ROOT, 'text_dia_ko_op_pushbutton_Export')
TEXT_DIA_TR_OP_EXPORT_DIR = os.path.join(PROJECT_ROOT, 'text_dia_tr_op_pushbutton_Export')
TEXT_DIA_SI_DIR = os.path.join(PROJECT_ROOT, 'text_dia', 'si')

KOREAN_EXPORT_DIR = os.path.join(PROJECT_ROOT, 'korean_Export')
TRAD_EXPORT_DIR = os.path.join(PROJECT_ROOT, 'trad_chinese_Export')
SI_EXPORT_DIR = os.path.join(PROJECT_ROOT, 'si_Export')

REPORTS_DIR = os.path.join(PROJECT_ROOT, 'reports')


def safe_load_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] failed to load JSON: {path}: {e}")
        return None


def safe_save_json(path: str, data: Dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        # Compact but readable
        text = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"[WRITE] {path}")
    except Exception as e:
        print(f"[ERROR] failed to write: {path}: {e}")
        raise


def iter_json_files(dir_path: str) -> List[str]:
    files = []
    if not os.path.isdir(dir_path):
        return files
    for name in os.listdir(dir_path):
        if name.lower().endswith('.json'):
            files.append(os.path.join(dir_path, name))
    return sorted(files)


def replace_texts_by_trad(english: Dict[str, Any], trad: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Return a new dict based on English structure, replacing wordDataArray[].str using Traditional Chinese when available.
    We keep all non-text fields from English to preserve exact structure.
    """
    result = deepcopy(english)
    # m_Name -> si_<suffix>
    name: str = result.get('m_Name', '')
    if name.startswith('english_'):
        result['m_Name'] = 'si_' + name[len('english_'):]
    else:
        result['m_Name'] = 'si_' + name

    if trad is None:
        # no replacement possible, keep English texts, but still rename m_Name
        return result

    eng_labels: List[Dict[str, Any]] = result.get('labelDataArray', [])
    trad_labels: List[Dict[str, Any]] = trad.get('labelDataArray', [])

    for i, eng_label in enumerate(eng_labels):
        if i < len(trad_labels):
            tlabel = trad_labels[i]
            e_words: List[Dict[str, Any]] = eng_label.get('wordDataArray', [])
            t_words: List[Dict[str, Any]] = tlabel.get('wordDataArray', [])
            for j, e_word in enumerate(e_words):
                if j < len(t_words):
                    # Copy Traditional text as-is (no conversion)
                    e_word['str'] = t_words[j].get('str', e_word.get('str', ''))
    return result


def process_common():
    os.makedirs(COMMON_SI_EXPORT_DIR, exist_ok=True)
    # map english_* to trad_chinese_* within common_msbt_Export
    for path in iter_json_files(COMMON_EXPORT_DIR):
        base = os.path.basename(path)
        if not base.startswith('english_'):
            continue
        suffix = base[len('english_'):]  # e.g., ss_monsname.json
        english = safe_load_json(path)
        if not english:
            continue
        trad_path = os.path.join(COMMON_EXPORT_DIR, 'trad_chinese_' + suffix)
        trad = safe_load_json(trad_path)
        si = replace_texts_by_trad(english, trad)
        out_path = os.path.join(COMMON_SI_EXPORT_DIR, 'si_' + suffix)
        safe_save_json(out_path, si)


def build_logo_dia_si():
    # Prefer KO JSON as template; adjust strings to si
    src = os.path.join(LOGO_DIA_KO_EXPORT_DIR, 'logo_dia_ko.json')
    data = safe_load_json(src)
    if not data:
        return
    # adjust asset-related fields to si
    data['m_Name'] = 'movie/dia/logo/logo_dia_si'
    # m_Container path
    try:
        # structure: [ ["assets/...png", { ... }] ]
        if isinstance(data.get('m_Container'), list) and len(data['m_Container']) > 0:
            entry = data['m_Container'][0]
            if isinstance(entry, list) and len(entry) >= 1 and isinstance(entry[0], str):
                entry[0] = 'assets/movie/dia/logo/logo_dia_si.png'
    except Exception:
        pass
    data['m_AssetBundleName'] = 'movie/dia/logo/logo_dia_si'
    out = os.path.join(LOGO_DIA_SI_DIR, 'logo_dia_si.json')
    safe_save_json(out, data)


def build_text_dia_si():
    src = os.path.join(TEXT_DIA_KO_OP_EXPORT_DIR, 'text_dia_ko_op_pushbutton.json')
    data = safe_load_json(src)
    if not data:
        return
    data['m_Name'] = 'movie/dia/text/text_dia_si_op_pushbutton'
    try:
        if isinstance(data.get('m_Container'), list) and len(data['m_Container']) > 0:
            entry = data['m_Container'][0]
            if isinstance(entry, list) and len(entry) >= 1 and isinstance(entry[0], str):
                entry[0] = 'assets/movie/dia/text/text_dia_si_op_pushbutton.png'
    except Exception:
        pass
    data['m_AssetBundleName'] = 'movie/dia/text/text_dia_si_op_pushbutton'
    out = os.path.join(TEXT_DIA_SI_DIR, 'text_dia_si_op_pushbutton.json')
    safe_save_json(out, data)


def replace_texts_by_trad_on_korean(korean: Dict[str, Any], trad: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    For korean_Export files: keep Korean structure, only swap text to Traditional Chinese when available.
    Rename m_Name to si_* (replacing 'korean_' prefix).
    """
    result = deepcopy(korean)
    name: str = result.get('m_Name', '')
    if name.startswith('korean_'):
        result['m_Name'] = 'si_' + name[len('korean_'):]
    else:
        result['m_Name'] = 'si_' + name

    if trad is None:
        return result

    kor_labels: List[Dict[str, Any]] = result.get('labelDataArray', [])
    trad_labels: List[Dict[str, Any]] = trad.get('labelDataArray', [])

    for i, klabel in enumerate(kor_labels):
        if i < len(trad_labels):
            tlabel = trad_labels[i]
            k_words: List[Dict[str, Any]] = klabel.get('wordDataArray', [])
            t_words: List[Dict[str, Any]] = tlabel.get('wordDataArray', [])
            for j, kw in enumerate(k_words):
                if j < len(t_words):
                    kw['str'] = t_words[j].get('str', kw.get('str', ''))
    return result


def process_korean_export():
    os.makedirs(SI_EXPORT_DIR, exist_ok=True)
    # iterate korean_* JSONs
    for path in iter_json_files(KOREAN_EXPORT_DIR):
        base = os.path.basename(path)
        if base == 'korean.json':
            # skip manifest
            continue
        korean = safe_load_json(path)
        if not korean:
            continue
        # compute trad counterpart filename
        if not base.startswith('korean_'):
            # unexpected naming; still attempt mapping
            suffix = base
        else:
            suffix = base[len('korean_'):]  # e.g., ss_wazaname.json
        trad_path = os.path.join(TRAD_EXPORT_DIR, 'trad_chinese_' + suffix)
        trad = safe_load_json(trad_path)
        si = replace_texts_by_trad_on_korean(korean, trad)
        out_path = os.path.join(SI_EXPORT_DIR, 'si_' + suffix)
        safe_save_json(out_path, si)


def collect_structure_keys(d: Dict[str, Any]) -> List[str]:
    return sorted(list(d.keys()))


def verify_common_against_english(si_path: str, english_path: str) -> Dict[str, Any]:
    si = safe_load_json(si_path) or {}
    en = safe_load_json(english_path) or {}
    report = {
        'si_file': os.path.basename(si_path),
        'english_file': os.path.basename(english_path),
        'top_keys_equal': collect_structure_keys(si) == collect_structure_keys(en),
        'label_count_equal': len(si.get('labelDataArray', [])) == len(en.get('labelDataArray', [])),
        'label_names_equal': True,
        'word_arrays_len_equal': True,
        'missing_labels': [],
        'mismatched_word_lengths': []
    }
    si_labels = si.get('labelDataArray', [])
    en_labels = en.get('labelDataArray', [])
    for i, en_label in enumerate(en_labels):
        if i >= len(si_labels):
            report['label_names_equal'] = False
            report['missing_labels'].append({'index': i, 'labelName': en_label.get('labelName')})
            continue
        si_label = si_labels[i]
        if si_label.get('labelName') != en_label.get('labelName'):
            report['label_names_equal'] = False
        si_words = si_label.get('wordDataArray', [])
        en_words = en_label.get('wordDataArray', [])
        if len(si_words) != len(en_words):
            report['word_arrays_len_equal'] = False
            report['mismatched_word_lengths'].append({'index': i, 'si_len': len(si_words), 'en_len': len(en_words)})
    return report


def verify_and_report():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    common_reports: List[Dict[str, Any]] = []
    for en_path in iter_json_files(COMMON_EXPORT_DIR):
        base = os.path.basename(en_path)
        if not base.startswith('english_'):
            continue
        si_path = os.path.join(COMMON_SI_EXPORT_DIR, 'si_' + base[len('english_'):])
        if not os.path.isfile(si_path):
            continue
        report = verify_common_against_english(si_path, en_path)
        common_reports.append(report)
    safe_save_json(os.path.join(REPORTS_DIR, 'common_structure_check.json'), {
        'summary': {
            'files_checked': len(common_reports),
            'all_top_keys_equal': all(r['top_keys_equal'] for r in common_reports),
            'all_label_count_equal': all(r['label_count_equal'] for r in common_reports),
            'all_label_names_equal': all(r['label_names_equal'] for r in common_reports),
            'all_word_arrays_len_equal': all(r['word_arrays_len_equal'] for r in common_reports),
        },
        'details': common_reports
    })

    # basic report for korean -> si alignment with trad availability
    kore_reports: List[Dict[str, Any]] = []
    for k_path in iter_json_files(KOREAN_EXPORT_DIR):
        base = os.path.basename(k_path)
        if base == 'korean.json':
            continue
        suffix = base[len('korean_'):] if base.startswith('korean_') else base
        si_path = os.path.join(SI_EXPORT_DIR, 'si_' + suffix)
        trad_path = os.path.join(TRAD_EXPORT_DIR, 'trad_chinese_' + suffix)
        report = {
            'korean_file': base,
            'si_exists': os.path.isfile(si_path),
            'trad_exists': os.path.isfile(trad_path)
        }
        kore_reports.append(report)
    safe_save_json(os.path.join(REPORTS_DIR, 'korean_si_mapping_check.json'), {
        'summary': {
            'files_checked': len(kore_reports),
            'si_generated': sum(1 for r in kore_reports if r['si_exists']),
            'trad_available': sum(1 for r in kore_reports if r['trad_exists'])
        },
        'details': kore_reports
    })


def main():
    print('[START] BDSP si translation generation')
    # common
    process_common()
    # logo & text dia
    build_logo_dia_si()
    build_text_dia_si()
    # korean export -> si export
    process_korean_export()
    # verification reports
    verify_and_report()
    print('[DONE] BDSP si translation generation')


if __name__ == '__main__':
    main()
