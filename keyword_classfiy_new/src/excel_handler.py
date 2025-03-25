import pandas as pd
import os
import datetime
import re
from typing import List, Dict, Any, Tuple, Optional

class ExcelHandler:
    def __init__(self):
        pass
        
    def read_workflow_file(self, file_path: str) -> Dict[str, Any]:
        """读取工作流文件，返回各个sheet的规则和关键词
        
        Args:
            file_path: 工作流文件路径
            
        Returns:
            包含各个sheet规则和关键词的字典
        """
        try:
            # 读取Excel文件的所有sheet
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            workflow_data = {}
            
            # 遍历所有sheet，读取规则和关键词
            for i, sheet_name in enumerate(sheet_names):
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # 检查sheet是否有数据
                if df.empty:
                    continue
                    
                # 获取第一列作为关键词列
                keywords = df.iloc[:, 0].dropna().astype(str).tolist()
                
                # 保序去重
                seen = set()
                unique_keywords = []
                for keyword in keywords:
                    if keyword not in seen:
                        seen.add(keyword)
                        unique_keywords.append(keyword)
                
                # 将处理后的数据添加到工作流数据中
                workflow_data[sheet_name] = {
                    'keywords': unique_keywords,
                    'level': i + 1  # 记录sheet的层级
                }
            
            return workflow_data
        except Exception as e:
            raise Exception(f"读取工作流文件失败: {str(e)}")
    
    def replace_special_chars(self, text: str, level: int = 1) -> str:
        """根据不同层级替换特殊字符
        
        Args:
            text: 需要替换特殊字符的文本
            level: sheet层级
            
        Returns:
            替换后的文本
        """
        # 替换通用特殊字符
        result = text
        
        # 替换<>为《》
        result = re.sub(r'<([^>]*)>', r'《\1》', result)
        
        # 替换|为~
        result = result.replace('|', '~')
        
        # 替换[]为【】
        result = re.sub(r'\[([^\]]*)\]', r'【\1】', result)
        
        return result
    
    def process_workflow(self, workflow_file: str, rules_file: str) -> str:
        """处理工作流文件
        
        Args:
            workflow_file: 工作流文件路径
            rules_file: 规则文件路径
            
        Returns:
            输出目录路径
        """
        try:
            # 读取规则
            rules = self.read_rules(rules_file)
            
            # 读取工作流文件
            workflow_data = self.read_workflow_file(workflow_file)
            
            # 创建输出目录
            output_dir = './工作流结果'
            os.makedirs(output_dir, exist_ok=True)
            
            # 获取当前时间作为文件名的一部分
            current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 处理第一层级（sheet1）- 生成不同的Excel文件
            if len(workflow_data) > 0:
                sheet1_name = list(workflow_data.keys())[0]
                sheet1_data = workflow_data[sheet1_name]
                
                # 对每个sheet1关键词进行分类
                for keyword in sheet1_data['keywords']:
                    # 替换特殊字符
                    safe_keyword = self.replace_special_chars(keyword, 1)
                    
                    # 创建输出文件名
                    output_file = f"{output_dir}/{safe_keyword}_{current_time}.xlsx"
                    
                    # 如果只有一个sheet，直接处理并保存结果
                    if len(workflow_data) == 1:
                        # 对关键词应用规则
                        results = self._apply_rules_to_keyword(keyword, rules)
                        
                        # 创建DataFrame并保存
                        df = pd.DataFrame([{
                            '关键词': keyword,
                            '匹配规则': results
                        }])
                        
                        # 保存到Excel
                        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                            df.to_excel(writer, sheet_name='分类结果', index=False)
                    else:
                        # 处理多层级情况
                        self._process_multilevel_workflow(workflow_data, keyword, rules, output_file)
            
            return output_dir
        except Exception as e:
            raise Exception(f"处理工作流失败: {str(e)}")
    
    def _apply_rules_to_keyword(self, keyword: str, rules: List[str]) -> str:
        """对关键词应用规则，返回匹配的规则
        
        Args:
            keyword: 关键词
            rules: 规则列表
            
        Returns:
            匹配的规则，用&分隔
        """
        # 这里简化处理，实际应该调用KeywordClassifier的方法
        # 在实际实现中，应该使用KeywordClassifier的classify_keywords方法
        matched_rules = []
        for rule in rules:
            if rule.lower() in keyword.lower():
                matched_rules.append(rule)
        
        return '&'.join(matched_rules) if matched_rules else ''
    
    def _process_multilevel_workflow(self, workflow_data: Dict[str, Any], 
                                    level1_keyword: str, rules: List[str], 
                                    output_file: str) -> None:
        """处理多层级工作流
        
        Args:
            workflow_data: 工作流数据
            level1_keyword: 第一层级关键词
            rules: 规则列表
            output_file: 输出文件路径
        """
        # 创建Excel写入器
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 处理第二层级（sheet2）- 生成不同的sheet
            if len(workflow_data) > 1:
                sheet2_name = list(workflow_data.keys())[1]
                sheet2_data = workflow_data[sheet2_name]
                
                # 如果只有两个层级
                if len(workflow_data) == 2:
                    for sheet2_keyword in sheet2_data['keywords']:
                        # 替换特殊字符
                        safe_sheet2_keyword = self.replace_special_chars(sheet2_keyword, 2)
                        
                        # 对关键词应用规则
                        results = self._apply_rules_to_keyword(sheet2_keyword, rules)
                        
                        # 创建DataFrame
                        df = pd.DataFrame([{
                            '关键词': sheet2_keyword,
                            '匹配规则': results
                        }])
                        
                        # 保存到对应的sheet
                        df.to_excel(writer, sheet_name=safe_sheet2_keyword[:31], index=False)  # Excel限制sheet名最长31字符
                else:
                    # 处理三层及以上的情况
                    self._process_level3_and_above(workflow_data, level1_keyword, rules, writer)
            else:
                # 只有一个层级，创建默认sheet
                results = self._apply_rules_to_keyword(level1_keyword, rules)
                df = pd.DataFrame([{
                    '关键词': level1_keyword,
                    '匹配规则': results
                }])
                df.to_excel(writer, sheet_name='分类结果', index=False)
    
    def _process_level3_and_above(self, workflow_data: Dict[str, Any], 
                                level1_keyword: str, rules: List[str], 
                                writer: pd.ExcelWriter) -> None:
        """处理第三层级及以上的工作流
        
        Args:
            workflow_data: 工作流数据
            level1_keyword: 第一层级关键词
            rules: 规则列表
            writer: Excel写入器
        """
        sheet2_name = list(workflow_data.keys())[1]
        sheet2_data = workflow_data[sheet2_name]
        
        # 获取第三层级及以上的sheet
        higher_levels = {}
        for sheet_name, sheet_data in workflow_data.items():
            if sheet_data['level'] > 2:
                higher_levels[sheet_name] = sheet_data
        
        # 对每个sheet2关键词创建一个sheet
        for sheet2_keyword in sheet2_data['keywords']:
            # 替换特殊字符
            safe_sheet2_keyword = self.replace_special_chars(sheet2_keyword, 2)
            
            # 创建数据框架
            data = []
            
            # 添加基本列
            row = {'关键词': sheet2_keyword}
            
            # 对于每个更高层级，添加一个列
            for sheet_name, sheet_data in higher_levels.items():
                for higher_keyword in sheet_data['keywords']:
                    # 对组合关键词应用规则
                    combined_keyword = f"{level1_keyword} {sheet2_keyword} {higher_keyword}"
                    results = self._apply_rules_to_keyword(combined_keyword, rules)
                    
                    # 替换特殊字符
                    safe_higher_keyword = self.replace_special_chars(higher_keyword, sheet_data['level'])
                    
                    # 添加到行中
                    row[safe_higher_keyword] = results
            
            # 添加行到数据中
            data.append(row)
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            # 保存到对应的sheet
            df.to_excel(writer, sheet_name=safe_sheet2_keyword[:31], index=False)  # Excel限制sheet名最长31字符
    
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
