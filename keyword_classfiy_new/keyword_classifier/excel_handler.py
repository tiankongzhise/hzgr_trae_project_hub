import pandas as pd
from datetime import datetime
import os
from typing import List, Dict

class ExcelHandler:
    def __init__(self):
        self.rules = []
        self.keywords = []

    def read_rules_from_excel(self, file_path: str) -> List[str]:
        """从Excel文件中读取规则"""
        try:
            df = pd.read_excel(file_path, sheet_name='分词规则')
            if '分词规则' not in df.columns:
                raise ValueError('Excel文件中未找到分词规则列')
            self.rules = df['分词规则'].dropna().tolist()
            return self.rules
        except Exception as e:
            raise Exception(f'读取规则失败: {str(e)}')

    def read_keywords_from_excel(self, file_path: str) -> List[str]:
        """从Excel文件中读取关键词"""
        try:
            df = pd.read_excel(file_path, sheet_name='Sheet1')
            if '关键词' not in df.columns:
                raise ValueError('Excel文件中未找到关键词列')
            self.keywords = df['关键词'].dropna().tolist()
            return self.keywords
        except Exception as e:
            raise Exception(f'读取关键词失败: {str(e)}')

    def save_classification_result(self, results: Dict[str, List[str]]):
        """保存分类结果到Excel文件"""
        try:
            # 创建结果目录
            output_dir = 'classfiy_result'
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成输出文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(output_dir, f'关键词分类_{timestamp}.xlsx')
            
            # 准备数据
            data = []
            for keyword, matched_rules in results.items():
                data.append({
                    '关键词': keyword,
                    '匹配规则': '|'.join(matched_rules) if matched_rules else ''
                })
            
            # 保存到Excel
            df = pd.DataFrame(data)
            df.to_excel(output_file, index=False)
            return output_file
        except Exception as e:
            raise Exception(f'保存结果失败: {str(e)}')
