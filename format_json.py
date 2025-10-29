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

def find_json_files(root_dir):
    """递归查找所有JSON文件"""
    json_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    return json_files

def main():
    # 从当前目录开始搜索JSON文件
    current_dir = os.getcwd()
    json_files = find_json_files(current_dir)
    
    if not json_files:
        print("未找到任何JSON文件！")
        return
    
    print(f"找到 {len(json_files)} 个JSON文件，开始格式化...")
    
    success_count = 0
    fail_count = 0
    
    for file_path in json_files:
        if format_json_file(file_path):
            success_count += 1
            print(f"✓ 格式化完成: {os.path.basename(file_path)}")
        else:
            fail_count += 1
    
    print(f"\n格式化完成！")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {fail_count} 个文件")

if __name__ == '__main__':
    main()