import json
import os
import re

def analyze_korean_text(text):
    """分析文本是否包含韩文"""
    # 韩文字符范围：AC00-D7A3 (韩文音节), 1100-11FF (韩文辅音), 3130-318F (韩文字母)
    korean_pattern = re.compile(r'[\uAC00-\uD7A3\u1100-\u11FF\u3130-\u318F]')
    return bool(korean_pattern.search(text))

def analyze_json_file(file_path):
    """分析单个JSON文件中的str字段"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        str_fields = []
        non_str_korean = []
        
        def extract_strings(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if key == "str" and isinstance(value, str):
                        str_fields.append({
                            'path': current_path,
                            'value': value,
                            'has_korean': analyze_korean_text(value)
                        })
                    elif isinstance(value, str) and analyze_korean_text(value):
                        non_str_korean.append({
                            'path': current_path,
                            'value': value
                        })
                    else:
                        extract_strings(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]"
                    extract_strings(item, current_path)
        
        extract_strings(data)
        return str_fields, non_str_korean
    except Exception as e:
        print(f"错误：无法读取文件 {file_path} - {str(e)}")
        return [], []

def analyze_folder(folder_path):
    """分析整个文件夹"""
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    
    total_files = 0
    total_str_fields = 0
    korean_str_fields = 0
    non_str_korean_fields = 0
    
    for json_file in json_files:
        file_path = os.path.join(folder_path, json_file)
        str_fields, non_str_korean = analyze_json_file(file_path)
        
        total_files += 1
        total_str_fields += len(str_fields)
        korean_str_fields += sum(1 for field in str_fields if field['has_korean'])
        non_str_korean_fields += len(non_str_korean)
        
        if non_str_korean:
            print(f"\n文件 {json_file} 中发现非str字段的韩文：")
            for field in non_str_korean:
                print(f"  路径：{field['path']}")
                print(f"  内容：{field['value'][:50]}...")
    
    return {
        'total_files': total_files,
        'total_str_fields': total_str_fields,
        'korean_str_fields': korean_str_fields,
        'non_str_korean_fields': non_str_korean_fields
    }

def main():
    print("开始分析韩文JSON文件...")
    
    # 分析 korean_Export 文件夹
    print("\n=== 分析 korean_Export 文件夹 ===")
    korean_results = analyze_folder("d:\\switch\\code\\korean_Export")
    
    # 分析 common_msbt_korean_Export 文件夹
    print("\n=== 分析 common_msbt_korean_Export 文件夹 ===")
    common_results = analyze_folder("d:\\switch\\code\\common_msbt_korean_Export")
    
    # 打印统计结果
    print("\n=== 统计结果 ===")
    print(f"korean_Export 文件夹：")
    print(f"  总文件数：{korean_results['total_files']}")
    print(f"  总str字段数：{korean_results['total_str_fields']}")
    print(f"  包含韩文的str字段数：{korean_results['korean_str_fields']}")
    print(f"  非str字段的韩文数：{korean_results['non_str_korean_fields']}")
    
    print(f"\ncommon_msbt_korean_Export 文件夹：")
    print(f"  总文件数：{common_results['total_files']}")
    print(f"  总str字段数：{common_results['total_str_fields']}")
    print(f"  包含韩文的str字段数：{common_results['korean_str_fields']}")
    print(f"  非str字段的韩文数：{common_results['non_str_korean_fields']}")
    
    # 结论
    total_str = korean_results['korean_str_fields'] + common_results['korean_str_fields']
    total_non_str = korean_results['non_str_korean_fields'] + common_results['non_str_korean_fields']
    
    print(f"\n=== 结论 ===")
    if total_non_str == 0:
        print("✓ 所有韩文文本都存储在str字段中")
    else:
        print(f"⚠ 发现 {total_non_str} 处非str字段包含韩文")
    
    print(f"str字段中韩文占比：{total_str}/{total_str + total_non_str} ({total_str/(total_str + total_non_str)*100:.1f}%)")

if __name__ == "__main__":
    main()