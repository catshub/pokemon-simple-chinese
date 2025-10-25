import os
import json

def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件失败 {file_path}: {e}")
        return None

def analyze_differences(chinese_data, korean_data):
    """分析两个JSON对象之间的非语言文本差异"""
    differences = {
        'strWidth': 0,
        'numeric_format': 0,
        'other': 0,
        'total': 0
    }
    
    def is_str_field(key, value):
        """判断是否为字符串字段"""
        return isinstance(value, str)
    
    def is_numeric_format_diff(val1, val2):
        """判断是否为数字格式差异"""
        if not isinstance(val1, str) or not isinstance(val2, str):
            return False
        
        # 检查是否包含全角/半角数字差异
        fullwidth_digits = '０１２３４５６７８９'
        halfwidth_digits = '0123456789'
        
        if any(c in fullwidth_digits for c in val1) or any(c in fullwidth_digits for c in val2):
            # 转换全角数字为半角
            trans_table = str.maketrans(fullwidth_digits, halfwidth_digits)
            val1_normalized = val1.translate(trans_table)
            val2_normalized = val2.translate(trans_table)
            return val1 != val2 and val1_normalized == val2_normalized
        
        return False
    
    def compare_structures(data1, data2, path=""):
        """递归比较结构"""
        if isinstance(data1, dict) and isinstance(data2, dict):
            for key in data1:
                if key in data2:
                    new_path = f"{path}.{key}" if path else key
                    compare_structures(data1[key], data2[key], new_path)
        elif isinstance(data1, list) and isinstance(data2, list):
            for i, (item1, item2) in enumerate(zip(data1, data2)):
                new_path = f"{path}[{i}]"
                compare_structures(item1, item2, new_path)
        else:
            # 检查是否为strWidth字段
            if path.endswith('strWidth') and data1 != data2:
                differences['strWidth'] += 1
                differences['total'] += 1
            # 检查是否为数字格式差异
            elif is_str_field(path, data1) and is_str_field(path, data2):
                if is_numeric_format_diff(data1, data2):
                    differences['numeric_format'] += 1
                    differences['total'] += 1
                elif data1 != data2 and not path.endswith('str'):
                    differences['other'] += 1
                    differences['total'] += 1
    
    compare_structures(chinese_data, korean_data)
    return differences

def main():
    chinese_folder = "d:\\switch\\code\\common_simp_chinese_msbt_Export"
    korean_folder = "d:\\switch\\code\\common_msbt_korean_Export"
    
    # 获取文件列表并建立映射
    chinese_files = os.listdir(chinese_folder)
    korean_files = os.listdir(korean_folder)
    
    file_mapping = {}
    for chinese_file in chinese_files:
        if chinese_file.startswith('simp_chinese_'):
            korean_version = chinese_file.replace('simp_chinese_', 'korean_')
            if korean_version in korean_files:
                file_mapping[chinese_file] = korean_version
    
    print(f"找到 {len(file_mapping)} 对对应文件进行分析")
    print("=" * 80)
    
    # 总体统计
    total_stats = {
        'strWidth': 0,
        'numeric_format': 0,
        'other': 0,
        'total': 0
    }
    
    # 分析每个文件
    for chinese_file, korean_file in file_mapping.items():
        print(f"分析 {chinese_file} 和 {korean_file}")
        
        chinese_path = os.path.join(chinese_folder, chinese_file)
        korean_path = os.path.join(korean_folder, korean_file)
        
        chinese_data = load_json_file(chinese_path)
        korean_data = load_json_file(korean_path)
        
        if chinese_data is None or korean_data is None:
            print("  无法加载文件，跳过分析")
            continue
        
        # 分析差异
        diffs = analyze_differences(chinese_data, korean_data)
        
        # 累加统计
        for key in total_stats:
            total_stats[key] += diffs[key]
        
        # 打印当前文件统计
        print(f"  strWidth差异: {diffs['strWidth']}")
        print(f"  数字格式差异: {diffs['numeric_format']}")
        print(f"  其他差异: {diffs['other']}")
        print(f"  总计差异: {diffs['total']}")
        print("-" * 80)
    
    # 打印总体统计
    print("\n总体分析报告:")
    print("=" * 80)
    print(f"strWidth字段差异: {total_stats['strWidth']} ({total_stats['strWidth']/total_stats['total']*100:.1f}%)")
    print(f"数字格式差异(全角/半角): {total_stats['numeric_format']} ({total_stats['numeric_format']/total_stats['total']*100:.1f}%)")
    print(f"其他非语言文本差异: {total_stats['other']} ({total_stats['other']/total_stats['total']*100:.1f}%)")
    print(f"总计非语言文本差异: {total_stats['total']}")
    
    # 保存分析结果
    with open("d:\\switch\\code\\json_differences_analysis.txt", 'w', encoding='utf-8') as f:
        f.write("JSON文件差异分析报告\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("总体统计:\n")
        f.write(f"strWidth字段差异: {total_stats['strWidth']} ({total_stats['strWidth']/total_stats['total']*100:.1f}%)\n")
        f.write(f"数字格式差异(全角/半角): {total_stats['numeric_format']} ({total_stats['numeric_format']/total_stats['total']*100:.1f}%)\n")
        f.write(f"其他非语言文本差异: {total_stats['other']} ({total_stats['other']/total_stats['total']*100:.1f}%)\n")
        f.write(f"总计非语言文本差异: {total_stats['total']}\n\n")
        
        f.write("结论:\n")
        if total_stats['strWidth'] > total_stats['total'] * 0.8:
            f.write("1. 绝大多数非语言文本差异是strWidth字段，这是由于不同语言字符宽度不同导致的正常现象\n")
        if total_stats['numeric_format'] > 0:
            f.write("2. 存在数字格式差异，主要是全角数字和半角数字的使用不同\n")
        if total_stats['other'] == 0:
            f.write("3. 除了上述差异外，未发现其他类型的非语言文本差异\n")
        else:
            f.write("3. 存在少量其他类型的非语言文本差异\n")
    
    print(f"\n分析结果已保存到 d:\\switch\\code\\json_differences_analysis.txt")

if __name__ == "__main__":
    main()