import pandas as pd
import os
import datetime

class ExcelHandler:
    def __init__(self):
        pass
    
    def read_rules(self, file_path):
        """从Excel文件中读取分词规则，并进行去重"""
        try:
            # 默认读取分词规则sheet的分词规则列
            df = pd.read_excel(file_path, sheet_name='分词规则')
            
            # 检查是否存在分词规则列
            if '分词规则' in df.columns:
                rules = df['分词规则'].dropna().astype(str).tolist()
            else:
                # 如果没有找到分词规则列，使用第一列
                rules = df.iloc[:, 0].dropna().astype(str).tolist()
            
            # 进一步处理规则，按逗号分隔，并保序去重
            result_rules = []
            seen = set()
            for rule in rules:
                for r in rule.split(','):
                    r = r.strip()
                    if r and r not in seen:
                        seen.add(r)
                        result_rules.append(r)
            
            return result_rules
        except Exception as e:
            raise Exception(f"读取规则文件失败: {str(e)}")
    
    def read_keywords(self, file_path):
        """从Excel文件中读取关键词，并进行去重"""
        try:
            df = pd.read_excel(file_path)
            
            # 使用第一列作为关键词列
            keywords = df.iloc[:, 0].dropna().astype(str).tolist()
            
            # 保序去重
            seen = set()
            unique_keywords = []
            for keyword in keywords:
                if keyword not in seen:
                    seen.add(keyword)
                    unique_keywords.append(keyword)
            keywords = unique_keywords
            
            return keywords
        except Exception as e:
            raise Exception(f"读取关键词文件失败: {str(e)}")
    
    def save_results(self, results, output_file=None):
        """保存分类结果到Excel文件
        
        Args:
            results: 字典列表，每个字典包含'keyword'和'matched_rules'两个键
            output_file: 输出文件路径，如果为None则使用默认路径
        """
        try:
            # 创建DataFrame
            df = pd.DataFrame(results)
            
            # 如果没有指定输出文件路径，则使用默认路径
            if output_file is None:
                # 获取当前时间作为文件名的一部分
                current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                # 设置默认输出目录为classfiy_result
                output_dir = './classfiy_result'
                # 设置默认文件名
                output_file = f'{output_dir}/关键词分类结果_{current_time}.xlsx'
            
            # 确保输出目录存在
            try:
                # 获取输出文件的目录路径
                dir_path = os.path.dirname(output_file)
                # 如果目录路径不为空，则创建目录
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                    print(f"已创建或确认输出目录: {os.path.abspath(dir_path)}")
            except PermissionError:
                # 权限错误时，尝试使用用户目录作为备选
                user_dir = os.path.expanduser("~")
                current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = os.path.join(user_dir, f"关键词分类结果_{current_time}.xlsx")
                print(f"无法创建原目录，将保存到用户目录: {output_file}")
            except Exception as e:
                print(f"创建目录时出错: {str(e)}，将尝试保存到当前目录")
                # 如果创建目录失败，尝试保存到当前目录
                current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"关键词分类结果_{current_time}.xlsx"
            
            # 保存到Excel
            df.to_excel(output_file, index=False, sheet_name='分类结果')
            
            return output_file
        except Exception as e:
            raise Exception(f"保存结果失败: {str(e)}")