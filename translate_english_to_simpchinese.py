#!/usr/bin/env python3
import json
import os
import logging
import re
import argparse
from typing import Dict, List, Any, Set

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("translate_english_to_simpchinese.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 常量定义
CACHE_FILE = "translation_cache.json"
MANUAL_TRANSLATION_FILE = "manual_translation_needed.txt"
SRC_FOLDER = "d:\\switch\\code\\lm原版\\common_msbt_Export"

class EnglishToChineseTranslator:
    def __init__(self):
        self.cache = {}
        self.load_cache()
    
    def load_cache(self):
        """加载翻译缓存"""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"加载缓存成功，共{len(self.cache)}条记录")
            except Exception as e:
                logger.error(f"加载缓存失败: {e}")
    
    def save_cache(self):
        """保存翻译缓存"""
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.info(f"缓存已保存，共{len(self.cache)}条记录")
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def collect_strings(self, folder_path: str) -> Set[str]:
        """收集所有需要翻译的字符串"""
        import glob
        
        # 查找所有以english开头的JSON文件
        file_pattern = os.path.join(folder_path, "english*.json")
        json_files = glob.glob(file_pattern)
        
        logger.info(f"找到 {len(json_files)} 个英文JSON文件")
        
        all_strings = set()
        file_stats = {}
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                strings = set()
                self._extract_strings(data, strings)
                
                non_empty_strings = {s for s in strings if s.strip()}
                
                file_stats[os.path.basename(file_path)] = {
                    "total": len(strings),
                    "non_empty": len(non_empty_strings),
                    "empty": len(strings) - len(non_empty_strings)
                }
                
                all_strings.update(non_empty_strings)
                
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
        
        # 保存文件统计信息
        with open("translation_stats.txt", 'w', encoding='utf-8') as f:
            f.write("文件翻译统计\n")
            f.write("="*50 + "\n")
            for filename, stats in sorted(file_stats.items()):
                f.write(f"{filename}:\n")
                f.write(f"  总字符串数: {stats['total']}\n")
                f.write(f"  非空字符串: {stats['non_empty']}\n")
                f.write(f"  空字符串: {stats['empty']}\n")
                f.write("-"*50 + "\n")
            
            total_non_empty = sum(stats['non_empty'] for stats in file_stats.values())
            f.write(f"\n总计非空字符串数: {total_non_empty}\n")
        
        logger.info(f"共收集 {len(all_strings)} 个非空英文字符串需要翻译")
        return all_strings
    
    def _extract_strings(self, data: Any, strings: Set[str]):
        """递归提取JSON中的str字段"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "str" and isinstance(value, str):
                    strings.add(value)
                else:
                    self._extract_strings(value, strings)
        elif isinstance(data, list):
            for item in data:
                self._extract_strings(item, strings)
    
    def generate_manual_translation_file(self, strings: Set[str]):
        """生成手动翻译文件"""
        # 过滤掉已有翻译的字符串
        strings_to_translate = [s for s in sorted(strings) if s not in self.cache]
        
        if not strings_to_translate:
            logger.info("所有字符串都已有翻译，无需生成手动翻译文件")
            return
        
        logger.info(f"生成手动翻译文件，包含 {len(strings_to_translate)} 条待翻译内容")
        
        with open(MANUAL_TRANSLATION_FILE, 'w', encoding='utf-8') as f:
            f.write("========================================================\n")
            f.write("                   手动翻译模板                           \n")
            f.write("========================================================\n")
            f.write("说明：\n")
            f.write("1. 请在'中文翻译:'后面输入对应的简体中文翻译\n")
            f.write("2. 不要修改文件格式，每行以EN:或CN:开头\n")
            f.write("3. 翻译完成后运行脚本的update命令更新翻译\n")
            f.write("========================================================\n\n")
            
            for i, text in enumerate(strings_to_translate, 1):
                f.write(f"[条目 {i}]\n")
                f.write(f"EN: {text}\n")
                f.write("CN: \n")
                f.write("--------------------------------------------------------\n\n")
        
        logger.info(f"手动翻译文件已生成: {MANUAL_TRANSLATION_FILE}")
    
    def update_translations_from_file(self):
        """从手动翻译文件更新缓存"""
        if not os.path.exists(MANUAL_TRANSLATION_FILE):
            logger.error(f"手动翻译文件不存在: {MANUAL_TRANSLATION_FILE}")
            return 0
        
        updated_count = 0
        
        try:
            with open(MANUAL_TRANSLATION_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 使用正则表达式提取翻译对
                pattern = re.compile(r'\[条目 \d+\]\s*EN:\s*(.+?)\s*CN:\s*(.+?)\s*--------------------------------------------------------', re.DOTALL)
                matches = pattern.findall(content)
                
                for english, chinese in matches:
                    if english and chinese.strip():
                        self.cache[english.strip()] = chinese.strip()
                        updated_count += 1
            
            if updated_count > 0:
                self.save_cache()
                logger.info(f"成功更新 {updated_count} 条翻译")
            else:
                logger.info("没有找到有效的翻译更新")
                
        except Exception as e:
            logger.error(f"更新翻译失败: {e}")
        
        return updated_count
    
    def translate_files(self, folder_path: str):
        """翻译所有英文JSON文件"""
        import glob
        
        # 查找所有以english开头的JSON文件
        file_pattern = os.path.join(folder_path, "english*.json")
        json_files = glob.glob(file_pattern)
        
        success_count = 0
        fail_count = 0
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 执行翻译
                self._translate_json_structure(data)
                
                # 生成输出文件名
                output_file = file_path.replace("english_", "simp_chinese_")
                
                # 保存翻译后的文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # 检查是否有未翻译的内容
                missing_translations = []
                self._find_missing_translations(data, missing_translations)
                
                if missing_translations:
                    logger.warning(f"文件 {os.path.basename(file_path)} 中存在 {len(missing_translations)} 处未翻译的内容")
                
                success_count += 1
                logger.info(f"成功翻译文件: {os.path.basename(file_path)} -> {os.path.basename(output_file)}")
                
            except Exception as e:
                logger.error(f"翻译文件失败 {file_path}: {e}")
                fail_count += 1
        
        # 生成翻译报告
        self._generate_translation_report(json_files)
        
        return {
            "total_files": len(json_files),
            "success": success_count,
            "fail": fail_count
        }
    
    def _translate_json_structure(self, data: Any):
        """递归翻译JSON结构中的str字段"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "str" and isinstance(value, str):
                    if value.strip() and value in self.cache:
                        data[key] = self.cache[value]
                else:
                    self._translate_json_structure(value)
        elif isinstance(data, list):
            for item in data:
                self._translate_json_structure(item)
    
    def _find_missing_translations(self, data: Any, missing: List[str]):
        """查找未翻译的内容"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "str" and isinstance(value, str):
                    if value.strip() and value not in self.cache:
                        missing.append(value)
                else:
                    self._find_missing_translations(value, missing)
        elif isinstance(data, list):
            for item in data:
                self._find_missing_translations(item, missing)
    
    def _generate_translation_report(self, json_files: List[str]):
        """生成翻译完成报告"""
        report_path = "translation_complete_report.txt"
        
        # 统计翻译情况
        total_strings = len(self.cache)
        
        # 检查每个文件的翻译完整性
        file_reports = []
        for file_path in json_files:
            try:
                with open(file_path.replace("english_", "simp_chinese_"), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                missing_translations = []
                self._find_missing_translations(data, missing_translations)
                
                # 总字符串数
                all_strings = set()
                self._extract_strings(data, all_strings)
                non_empty_strings = {s for s in all_strings if s.strip()}
                
                file_reports.append({
                    "filename": os.path.basename(file_path),
                    "total": len(non_empty_strings),
                    "missing": len(missing_translations),
                    "completed": len(non_empty_strings) - len(missing_translations),
                    "completion_rate": 0 if len(non_empty_strings) == 0 else 
                                      ((len(non_empty_strings) - len(missing_translations)) / len(non_empty_strings)) * 100
                })
                
            except Exception as e:
                logger.error(f"生成文件报告失败 {file_path}: {e}")
        
        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("翻译完成报告\n")
            f.write("="*50 + "\n")
            f.write(f"总翻译缓存记录: {total_strings}\n\n")
            
            f.write("文件翻译详情:\n")
            f.write("-"*50 + "\n")
            
            for report in sorted(file_reports, key=lambda x: x['filename']):
                f.write(f"{report['filename']}:\n")
                f.write(f"  总字符串数: {report['total']}\n")
                f.write(f"  已翻译: {report['completed']}\n")
                f.write(f"  未翻译: {report['missing']}\n")
                f.write(f"  完成率: {report['completion_rate']:.1f}%\n")
                f.write("-"*50 + "\n")
            
            # 计算总体统计
            total_total = sum(r['total'] for r in file_reports)
            total_completed = sum(r['completed'] for r in file_reports)
            total_missing = sum(r['missing'] for r in file_reports)
            total_rate = 0 if total_total == 0 else (total_completed / total_total) * 100
            
            f.write(f"\n总体统计:\n")
            f.write(f"  总字符串数: {total_total}\n")
            f.write(f"  已翻译: {total_completed}\n")
            f.write(f"  未翻译: {total_missing}\n")
            f.write(f"  总完成率: {total_rate:.1f}%\n")
        
        logger.info(f"翻译完成报告已生成: {report_path}")
    
    def verify_translations(self):
        """验证翻译完整性"""
        import glob
        
        # 查找所有生成的简体中文文件
        file_pattern = os.path.join(SRC_FOLDER, "simp_chinese_*.json")
        json_files = glob.glob(file_pattern)
        
        if not json_files:
            logger.warning("未找到已翻译的简体中文文件")
            return
        
        logger.info(f"开始验证 {len(json_files)} 个已翻译文件")
        
        all_missing = []
        file_issues = {}
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                missing_translations = []
                self._find_missing_translations(data, missing_translations)
                
                # 检查是否有英文残留
                english_residues = []
                self._find_english_residues(data, english_residues)
                
                if missing_translations or english_residues:
                    file_issues[os.path.basename(file_path)] = {
                        "missing": missing_translations,
                        "english_residues": english_residues
                    }
                    all_missing.extend(missing_translations)
            
            except Exception as e:
                logger.error(f"验证文件失败 {file_path}: {e}")
        
        # 生成验证报告
        self._generate_verification_report(file_issues)
        
        if all_missing:
            # 重新生成需要翻译的内容
            self.generate_manual_translation_file(set(all_missing))
            logger.warning(f"发现 {len(all_missing)} 处未翻译的内容，请检查验证报告")
        else:
            logger.info("验证完成，所有内容已成功翻译！")
    
    def _find_english_residues(self, data: Any, residues: List[str]):
        """查找英文残留（简单检测）"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "str" and isinstance(value, str):
                    # 简单检测：如果字符串包含大量英文字母但不包含中文字符
                    if re.search(r'[a-zA-Z]{3,}', value) and not re.search(r'[\u4e00-\u9fa5]', value):
                        residues.append(value)
                else:
                    self._find_english_residues(value, residues)
        elif isinstance(data, list):
            for item in data:
                self._find_english_residues(item, residues)
    
    def _generate_verification_report(self, file_issues: Dict[str, Dict]):
        """生成验证报告"""
        report_path = "translation_verification_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("翻译验证报告\n")
            f.write("="*60 + "\n")
            
            if not file_issues:
                f.write("✓ 所有文件验证通过！\n")
                logger.info("所有文件验证通过！")
                return
            
            f.write(f"发现问题的文件数: {len(file_issues)}\n\n")
            
            for filename, issues in sorted(file_issues.items()):
                f.write(f"\n【文件】: {filename}\n")
                f.write("-"*60 + "\n")
                
                if issues["missing"]:
                    f.write(f"未翻译内容 ({len(issues['missing'])}):\n")
                    for i, text in enumerate(issues["missing"][:50], 1):  # 限制输出数量
                        f.write(f"  {i}. {text[:100]}{'...' if len(text) > 100 else ''}\n")
                    if len(issues["missing"]) > 50:
                        f.write(f"  ... 还有 {len(issues['missing']) - 50} 条未显示\n")
                
                if issues["english_residues"]:
                    f.write(f"\n英文残留 ({len(issues['english_residues'])}):\n")
                    for i, text in enumerate(issues["english_residues"][:50], 1):
                        f.write(f"  {i}. {text[:100]}{'...' if len(text) > 100 else ''}\n")
                    if len(issues["english_residues"]) > 50:
                        f.write(f"  ... 还有 {len(issues['english_residues']) - 50} 条未显示\n")
        
        logger.info(f"验证报告已生成: {report_path}")

def main():
    parser = argparse.ArgumentParser(description="英文到简体中文翻译工具")
    parser.add_argument('command', choices=['collect', 'translate', 'update', 'verify', 'full'], 
                        help='命令: collect(收集待翻译内容), translate(执行翻译), update(更新翻译), verify(验证翻译), full(完整流程)')
    args = parser.parse_args()
    
    translator = EnglishToChineseTranslator()
    
    if args.command == 'collect':
        # 收集所有需要翻译的字符串并生成手动翻译文件
        strings = translator.collect_strings(SRC_FOLDER)
        translator.generate_manual_translation_file(strings)
        logger.info("收集完成！请编辑 'manual_translation_needed.txt' 文件进行手动翻译")
    
    elif args.command == 'update':
        # 从手动翻译文件更新缓存
        updated = translator.update_translations_from_file()
        if updated > 0:
            logger.info("翻译已更新，可以开始执行翻译了")
    
    elif args.command == 'translate':
        # 执行翻译
        results = translator.translate_files(SRC_FOLDER)
        logger.info(f"翻译完成！成功: {results['success']}, 失败: {results['fail']}")
    
    elif args.command == 'verify':
        # 验证翻译完整性
        translator.verify_translations()
    
    elif args.command == 'full':
        # 完整流程：收集 -> 提示翻译 -> 更新 -> 翻译 -> 验证
        logger.info("开始完整翻译流程...")
        strings = translator.collect_strings(SRC_FOLDER)
        translator.generate_manual_translation_file(strings)
        
        logger.info("\n==== 第一步完成 ====")
        logger.info(f"请编辑 '{MANUAL_TRANSLATION_FILE}' 文件进行手动翻译")
        logger.info("翻译完成后，运行 'python translate_english_to_simpchinese.py update' 继续")

if __name__ == "__main__":
    main()