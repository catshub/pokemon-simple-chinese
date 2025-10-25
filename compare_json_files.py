import os
import json
import difflib

def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件失败 {file_path}: {e}")
        return None

def is_likely_text_field(key, value):
    """判断是否可能是语言文本字段"""
    if not isinstance(value, str):
        return False
    
    # 检查键名是否暗示这是文本字段
    text_key_patterns = ['_text', '_name', '_desc', '_title', 'text_', 'name_', 'desc_', 'title_']
    if any(pattern.lower() in key.lower() for pattern in text_key_patterns):
        return True
    
    # 检查值长度或内容是否暗示这是文本
    if len(value) > 50:
        return True
    
    # 排除明显不是文本的值（如纯数字、简短标识符等）
    if value.isdigit():
        return False
    if len(value) <= 5 and all(c.isalnum() or c in ['_', '-'] for c in value):
        return False
    
    return False

def compare_json_structures(file1_data, file2_data, file1_name, file2_name):
    """比较两个JSON对象的结构，忽略可能的文本字段"""
    differences = []
    
    # 获取所有键
    file1_keys = set(file1_data.keys())
    file2_keys = set(file2_data.keys())
    
    # 检查缺失或额外的键
    missing_in_file2 = file1_keys - file2_keys
    extra_in_file2 = file2_keys - file1_keys
    
    if missing_in_file2:
        differences.append(f"{file2_name} 缺少键: {sorted(missing_in_file2)}")
    if extra_in_file2:
        differences.append(f"{file2_name} 多出键: {sorted(extra_in_file2)}")
    
    # 比较共同键的值
    common_keys = file1_keys & file2_keys
    for key in sorted(common_keys):
        val1 = file1_data[key]
        val2 = file2_data[key]
        
        # 如果是对象，递归比较
        if isinstance(val1, dict) and isinstance(val2, dict):
            nested_diffs = compare_json_structures(val1, val2, file1_name, file2_name)
            if nested_diffs:
                for diff in nested_diffs:
                    differences.append(f"键 '{key}' 下: {diff}")
        # 如果是列表，比较长度和元素类型
        elif isinstance(val1, list) and isinstance(val2, list):
            if len(val1) != len(val2):
                differences.append(f"键 '{key}' 的列表长度不同: {len(val1)} vs {len(val2)}")
            else:
                # 简单比较列表元素的类型
                for i, (item1, item2) in enumerate(zip(val1, val2)):
                    if isinstance(item1, dict) and isinstance(item2, dict):
                        nested_diffs = compare_json_structures(item1, item2, file1_name, file2_name)
                        if nested_diffs:
                            for diff in nested_diffs:
                                differences.append(f"键 '{key}' 列表索引 {i} 下: {diff}")
                    elif not is_likely_text_field(key, item1) and not is_likely_text_field(key, item2):
                        if item1 != item2:
                            differences.append(f"键 '{key}' 列表索引 {i} 的值不同: {item1} vs {item2}")
        # 对于非文本值，检查是否相等
        elif not is_likely_text_field(key, val1) and not is_likely_text_field(key, val2):
            if val1 != val2:
                differences.append(f"键 '{key}' 的值不同: {val1} vs {val2}")
    
    return differences

# 此函数已在主程序中直接实现，不再需要单独的函数定义

def write_results_to_file(results, output_file):
    """将比较结果写入文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("JSON文件比较结果\n")
        f.write("=" * 80 + "\n\n")
        for file, diffs in results.items():
            f.write(f"文件: {file}\n")
            for diff in diffs:
                f.write(f"  - {diff}\n")
            f.write("\n" + "-" * 80 + "\n\n")
        
        if not results:
            f.write("除语言文本外，所有文件的结构和非文本字段值均相同\n")

if __name__ == "__main__":
    chinese_folder = "d:\\switch\\code\\common_simp_chinese_msbt_Export"
    korean_folder = "d:\\switch\\code\\common_msbt_korean_Export"
    output_file = "d:\\switch\\code\\json_compare_results.txt"
    
    print(f"正在比较 {chinese_folder} 和 {korean_folder} 文件夹中的对应文件")
    print(f"将忽略可能的语言文本字段，只比较结构和非文本字段")
    print(f"结果将保存到 {output_file}")
    print("=" * 80)
    
    # 修改compare_corresponding_files函数调用，获取结果
    all_differences = {}
    chinese_files = os.listdir(chinese_folder)
    korean_files = os.listdir(korean_folder)
    
    file_mapping = {}
    for chinese_file in chinese_files:
        if chinese_file.startswith('simp_chinese_'):
            korean_version = chinese_file.replace('simp_chinese_', 'korean_')
            if korean_version in korean_files:
                file_mapping[chinese_file] = korean_version
    
    print(f"找到 {len(file_mapping)} 对对应文件进行比较")
    
    for chinese_file, korean_file in file_mapping.items():
        print(f"比较 {chinese_file} 和 {korean_file}")
        
        chinese_path = os.path.join(chinese_folder, chinese_file)
        korean_path = os.path.join(korean_folder, korean_file)
        
        chinese_data = load_json_file(chinese_path)
        korean_data = load_json_file(korean_path)
        
        if chinese_data is None or korean_data is None:
            print("  无法加载文件，跳过比较")
            continue
        
        differences = compare_json_structures(chinese_data, korean_data, chinese_file, korean_file)
        if differences:
            all_differences[chinese_file] = differences
            print(f"  发现 {len(differences)} 处差异")
        else:
            print("  除语言文本外，未发现其他差异")
    
    # 写入结果到文件
    write_results_to_file(all_differences, output_file)
    print(f"\n比较完成！结果已保存到 {output_file}")