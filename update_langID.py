import os
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 目标文件夹列表
target_folders = [
    'd:\\switch\\code\\simp_chinese_Export',
    'd:\\switch\\code\\common_simp_chinese_msbt_Export'
]

def update_langID_in_file(file_path):
    """更新单个文件中的langID字段"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查并更新langID字段
        if 'langID' in data:
            old_value = data['langID']
            if old_value != 9:
                data['langID'] = 9
                
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f'Updated {file_path}: langID changed from {old_value} to 9')
                return True
        return False
    except Exception as e:
        logger.error(f'Error processing {file_path}: {str(e)}')
        return False

def main():
    total_files = 0
    updated_files = 0
    
    for folder in target_folders:
        logger.info(f'Processing folder: {folder}')
        
        if not os.path.exists(folder):
            logger.warning(f'Folder not found: {folder}')
            continue
        
        for filename in os.listdir(folder):
            if filename.endswith('.json'):
                file_path = os.path.join(folder, filename)
                total_files += 1
                
                if update_langID_in_file(file_path):
                    updated_files += 1
    
    logger.info(f'Processing completed. Total JSON files: {total_files}, Updated files: {updated_files}')

if __name__ == '__main__':
    main()