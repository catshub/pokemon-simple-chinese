import os
import re
import json

# 处理文件夹中的所有JSON文件
def process_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            process_file(file_path)
            print(f"处理完成: {file_path}")

# 处理单个JSON文件
def process_file(file_path):
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换韩语标识
        # 替换m_Name中的korean，包括korean_开头的文件名
        content = re.sub(r'"m_Name":\s*"korean"', '"m_Name": "simp_chinese"', content)
        content = re.sub(r'"m_Name":\s*"korean_', '"m_Name": "simp_chinese_', content)
        content = re.sub(r'"m_AssetBundleName":\s*"korean"', '"m_AssetBundleName": "simp_chinese"', content)
        
        # 替换路径中的ko/korean/korean_为si/simp_chinese/simp_chinese_
        content = re.sub(r'assets/format_msbt/ko/korean/korean_', 'assets/format_msbt/si/simp_chinese/simp_chinese_', content)
        
        # 确保修改后的内容是有效的JSON
        json.loads(content)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception as e:
        print(f"处理文件时出错 {file_path}: {e}")

if __name__ == "__main__":
    # 处理两个文件夹
    print("开始处理 simp_chinese_Export 文件夹...")
    process_folder(r'd:\switch\code\simp_chinese_Export')
    
    print("\n开始处理 common_msbt_Export 文件夹中的 simp_chinese_* 文件...")
    # 只处理common_msbt_Export中的simp_chinese_*文件
    common_folder = r'd:\switch\code\common_msbt_Export'
    for filename in os.listdir(common_folder):
        if filename.startswith('simp_chinese_') and filename.endswith('.json'):
            file_path = os.path.join(common_folder, filename)
            process_file(file_path)
            print(f"处理完成: {file_path}")
    
    print("\n开始处理 common_simp_chinese_msbt_Export 文件夹中的所有文件...")
    # 处理common_simp_chinese_msbt_Export文件夹中的所有文件
    common_simp_folder = r'd:\switch\code\common_simp_chinese_msbt_Export'
    process_folder(common_simp_folder)
    
    print("\n所有文件处理完成！")