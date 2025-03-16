import pandas as pd
import os

class ExcelHandler:
    def __init__(self):
        pass
    
    def read_rules(self, file_path):
        """从Excel文件中读取分词规则"""
        try:
            # 默认读取分词规则sheet的分词规则列
            df = pd.read_excel(file_path, sheet_name='分词规则')
            
            # 检查是否存在分词规则列
            if '分词规则' in df.columns:
                rules = df['分词规则'].dropna().astype(str).tolist()
            else:
                # 如果没有找到分词规则列，使用第一列
                rules = df.iloc[:, 0].dropna().astype(str).tolist()
            
            # 进一步处理规则，按逗号分隔
            result_rules = []
            for rule in rules:
                result_rules.extend([r.strip() for r in rule.split(',') if r.strip()])
            
            return result_rules
        except Exception as e:
            raise Exception(f"读取规则文件失败: {str(e)}")
    
    def read_keywords(self, file_path):
        """从Excel文件中读取关键词"""
        try:
            df = pd.read_excel(file_path)
            
            # 使用第一列作为关键词列
            keywords = df.iloc[:, 0].dropna().astype(str).tolist()
            
            return keywords
        except Exception as e:
            raise Exception(f"读取关键词文件失败: {str(e)}")
    
    def save_results(self, results, output_file):
        """保存分类结果到Excel文件
        
        Args:
            results: 字典列表，每个字典包含'keyword'和'matched_rules'两个键
            output_file: 输出文件路径
        """
        try:
            # 创建DataFrame
            df = pd.DataFrame(results)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # 保存到Excel
            df.to_excel(output_file, index=False, sheet_name='分类结果')
            
            return True
        except Exception as e:
            raise Exception(f"保存结果失败: {str(e)}")