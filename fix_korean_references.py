#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
from pathlib import Path

def fix_korean_references_in_file(file_path):
    """修复单个JSON文件中的韩语标识"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替换规则
        replacements = [
            # m_Name字段中的korean替换为simp_chinese
            (r'"m_Name":\s*"korean([^"]*?)"', r'"m_Name": "simp_chinese\1"'),
            # m_AssetBundleName字段中的korean替换为simp_chinese
            (r'"m_AssetBundleName":\s*"korean"', r'"m_AssetBundleName": "simp_chinese"'),
            # labelName中的korean_替换为simp_chinese_
            (r'"labelName":\s*"([^"]*?)korean_([^"]*?)"', r'"labelName": "\1simp_chinese_\2"'),
            # 其他可能的korean路径替换
            (r'"korean_', r'"simp_chinese_'),
            (r'/korean/', r'/simp_chinese/'),
            (r'\\korean\\', r'\\simp_chinese\\'),
        ]
        
        changes_made = False
        for pattern, replacement in replacements:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                changes_made = True
                content = new_content
        
        # 如果有修改，写回文件
        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "修改成功"
        else:
            return False, "无需修改"
            
    except Exception as e:
        return False, f"处理失败: {str(e)}"

def scan_and_fix_directories(directories):
    """扫描并修复指定目录下的所有JSON文件"""
    total_files = 0
    modified_files = 0
    error_files = 0
    
    print("开始扫描和修复韩语标识...")
    print("="*60)
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"目录不存在: {directory}")
            continue
            
        print(f"\n处理目录: {directory}")
        
        # 遍历目录下的所有JSON文件
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    total_files += 1
                    
                    success, message = fix_korean_references_in_file(file_path)
                    
                    if success:
                        modified_files += 1
                        print(f"✓ {file}: {message}")
                    elif "处理失败" in message:
                        error_files += 1
                        print(f"✗ {file}: {message}")
                    # 无需修改的文件不打印，避免输出过多
    
    print("\n" + "="*60)
    print(f"处理完成!")
    print(f"总文件数: {total_files}")
    print(f"修改文件数: {modified_files}")
    print(f"错误文件数: {error_files}")
    print(f"无需修改文件数: {total_files - modified_files - error_files}")

def main():
    # 要处理的目录
    directories = [
        "/Users/bytedance/work/project/pokemon-simple-chinese/simp_chinese_Export",
        "/Users/bytedance/work/project/pokemon-simple-chinese/common_simp_chinese_msbt_Export"
    ]
    
    scan_and_fix_directories(directories)

if __name__ == "__main__":
    main()