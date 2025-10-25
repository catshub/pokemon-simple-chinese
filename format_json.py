#!/usr/bin/env python3
import json
import os
import sys

def format_json_file(file_path):
    """格式化单个JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        
        return True
    except Exception as e:
        print(f"格式化文件 {file_path} 时出错: {e}")
        return False

def main():
    # 读取JSON文件列表
    with open('json_files_list.txt', 'r') as f:
        json_files = [line.strip() for line in f if line.strip()]
    
    print(f"找到 {len(json_files)} 个JSON文件，开始格式化...")
    
    success_count = 0
    fail_count = 0
    
    for file_path in json_files:
        if os.path.exists(file_path):
            if format_json_file(file_path):
                success_count += 1
                print(f"✓ 格式化完成: {os.path.basename(file_path)}")
            else:
                fail_count += 1
        else:
            print(f"文件不存在: {file_path}")
            fail_count += 1
    
    print(f"\n格式化完成！")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {fail_count} 个文件")

if __name__ == '__main__':
    main()