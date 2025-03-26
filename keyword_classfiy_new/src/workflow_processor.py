import os
import pandas as pd
import datetime
import re
from typing import List, Dict, Any, Tuple, Optional, Set
from keyword_classifier import KeywordClassifier

class WorkflowProcessor:
    def __init__(self, classifier=None):
        """初始化工作流处理器
        
        Args:
            classifier: 关键词分类器实例，如果为None则创建新实例
        """
        self.classifier = classifier if classifier else KeywordClassifier()
        self.output_dir = './工作流结果'
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    def read_workflow_rules(self, file_path: str) -> Dict[str, Any]:
        """读取工作流规则文件
        
        Args:
            file_path: 工作流规则文件路径
            
        Returns:
            包含各个sheet规则的字典
        """
        try:
            # 检查文件名是否符合规范
            file_name = os.path.basename(file_path)
            if not file_name.startswith("工作流规则_"):
                raise ValueError(f"工作流规则文件名必须以'工作流规则_'开头，当前文件名: {file_name}")
            
            # 读取Excel文件的所有sheet
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            workflow_rules = {}
            
            # 遍历所有sheet，读取规则
            for i, sheet_name in enumerate(sheet_names):
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # 检查sheet是否有数据
                if df.empty:
                    continue
                
                # 检查必需列
                required_cols = ['分类规则', '结果文件名称']
                if i > 0:  # Sheet2及以上需要额外的列
                    required_cols.append('分类sheet名称')
                if i > 2:  # Sheet4及以上需要上层分类规则
                    required_cols.append('上层分类规则')
                
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    raise ValueError(f"Sheet '{sheet_name}' 缺少必需列: {', '.join(missing_cols)}")
                
                # 读取规则数据
                rules_data = []
                for _, row in df.iterrows():
                    rule_data = {
                        'rule': row['分类规则'],
                        'output_name': row['结果文件名称']
                    }
                    
                    # 添加额外的列
                    if i > 0 and '分类sheet名称' in df.columns:
                        rule_data['sheet_name'] = row['分类sheet名称']
                    
                    if i > 2 and '上层分类规则' in df.columns:
                        rule_data['parent_rule'] = row['上层分类规则']
                    
                    # 只添加非空规则
                    if pd.notna(rule_data['rule']) and rule_data['rule'].strip():
                        rules_data.append(rule_data)
                
                # 将处理后的数据添加到工作流规则中
                workflow_rules[f'Sheet{i+1}'] = {
                    'rules': rules_data,
                    'level': i + 1  # 记录sheet的层级
                }
            
            # 检查是否至少有Sheet1
            if 'Sheet1' not in workflow_rules:
                raise ValueError("工作流规则文件必须包含Sheet1")
            
            return workflow_rules
        except Exception as e:
            raise Exception(f"读取工作流规则文件失败: {str(e)}")
    
    def read_classification_file(self, file_path: str) -> pd.DataFrame:
        """读取待分类文件
        
        Args:
            file_path: 待分类文件路径
            
        Returns:
            包含关键词的DataFrame
        """
        try:
            # 检查文件名是否符合规范
            file_name = os.path.basename(file_path)
            if not file_name.startswith("待分类_"):
                raise ValueError(f"待分类文件名必须以'待分类_'开头，当前文件名: {file_name}")
            
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 检查是否包含关键词列
            if '关键词' not in df.columns:
                raise ValueError("待分类文件必须包含'关键词'列")
            
            # 清理数据
            df['关键词'] = df['关键词'].astype(str)
            
            return df
        except Exception as e:
            raise Exception(f"读取待分类文件失败: {str(e)}")
    
    def find_latest_classification_files(self, directory: str = None) -> List[str]:
        """查找最新的分类结果文件
        
        Args:
            directory: 目录路径，默认为输出目录
            
        Returns:
            最新的分类结果文件路径列表
        """
        if directory is None:
            directory = self.output_dir
        
        try:
            # 获取目录下所有xlsx文件
            files = [f for f in os.listdir(directory) if f.endswith('.xlsx')]
            
            # 按时间戳排序
            files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
            
            return [os.path.join(directory, f) for f in files]
        except Exception as e:
            raise Exception(f"查找分类结果文件失败: {str(e)}")
    
    def process_stage1(self, keywords_df: pd.DataFrame, workflow_rules: Dict[str, Any], 
                      error_callback=None) -> Dict[str, pd.DataFrame]:
        """处理阶段1：基础分类（Sheet1处理）
        
        Args:
            keywords_df: 包含关键词的DataFrame
            workflow_rules: 工作流规则字典
            error_callback: 错误回调函数
            
        Returns:
            分类结果字典，键为结果文件名称，值为对应的DataFrame
        """
        try:
            # 获取Sheet1规则
            sheet1_rules = workflow_rules['Sheet1']['rules']
            
            # 初始化分类结果
            classification_results = {}
            
            # 初始化未匹配项
            unmatched_keywords = keywords_df.copy()
            
            # 设置分类器规则
            for rule_data in sheet1_rules:
                rule = rule_data['rule']
                output_name = rule_data['output_name']
                
                # 跳过空规则
                if not rule or not output_name:
                    continue
                
                # 设置分类器规则
                self.classifier.set_rules([rule], error_callback)
                
                # 获取关键词列表
                keywords = unmatched_keywords['关键词'].tolist()
                
                # 分类关键词
                results = self.classifier.classify_keywords(keywords, error_callback)
                
                # 处理匹配结果
                matched_indices = []
                matched_data = []
                
                for i, result in enumerate(results):
                    if result['matched_rules']:  # 如果有匹配的规则
                        keyword = result['keyword']
                        matched_indices.append(i)
                        
                        # 获取原始行数据
                        row_data = unmatched_keywords.iloc[i].to_dict()
                        row_data['分类规则'] = result['matched_rules']
                        matched_data.append(row_data)
                
                # 如果有匹配项，添加到结果中
                if matched_data:
                    # 创建结果DataFrame
                    result_df = pd.DataFrame(matched_data)
                    
                    # 添加到分类结果
                    classification_results[output_name] = result_df
                    
                    # 从未匹配项中移除已匹配的行
                    unmatched_keywords = unmatched_keywords.drop(unmatched_keywords.index[matched_indices])
            
            # 处理未匹配项
            if not unmatched_keywords.empty:
                # 添加分类规则列
                unmatched_keywords['分类规则'] = ''
                
                # 添加到分类结果
                classification_results['无分类规则'] = unmatched_keywords
            
            return classification_results
        except Exception as e:
            raise Exception(f"处理阶段1失败: {str(e)}")
    
    def save_stage1_results(self, classification_results: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """保存阶段1分类结果
        
        Args:
            classification_results: 分类结果字典
            
        Returns:
            保存的文件路径字典
        """
        try:
            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 获取当前时间作为文件名的一部分
            current_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            
            # 初始化文件路径字典
            file_paths = {}
            
            # 保存每个分类结果
            for output_name, df in classification_results.items():
                # 替换特殊字符
                safe_output_name = self.replace_special_chars(output_name)
                
                # 创建输出文件名
                output_file = f"{self.output_dir}/{safe_output_name}_{current_time}.xlsx"
                
                # 保存到Excel
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='分类结果', index=False)
                
                # 添加到文件路径字典
                file_paths[output_name] = output_file
            
            return file_paths
        except Exception as e:
            raise Exception(f"保存阶段1结果失败: {str(e)}")
    
    def process_stage2(self, stage1_files: Dict[str, str], workflow_rules: Dict[str, Any], 
                      error_callback=None) -> Dict[str, str]:
        """处理阶段2：分层处理（Sheet2处理）
        
        Args:
            stage1_files: 阶段1生成的文件路径字典
            workflow_rules: 工作流规则字典
            error_callback: 错误回调函数
            
        Returns:
            更新后的文件路径字典
        """
        # 检查是否有Sheet2规则
        if 'Sheet2' not in workflow_rules:
            return stage1_files
        
        try:
            # 获取Sheet2规则
            sheet2_rules = workflow_rules['Sheet2']['rules']
            
            # 处理每个阶段1文件
            for output_name, file_path in stage1_files.items():
                # 读取阶段1文件
                with pd.ExcelFile(file_path) as xls:
                    stage1_df = pd.read_excel(xls, sheet_name='分类结果')
                
                # 使用Excel写入器追加新Sheet
                with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
                    # 处理每条Sheet2规则
                    for rule_data in sheet2_rules:
                        rule = rule_data['rule']
                        sheet_name = rule_data['sheet_name']
                        
                        # 跳过空规则
                        if not rule or not sheet_name:
                            continue
                        
                        # 检查是否为"全"值
                        if rule == '全':
                            # 全部关键词都匹配
                            matched_df = stage1_df.copy()
                        else:
                            # 设置分类器规则
                            self.classifier.set_rules([rule], error_callback)
                            
                            # 获取关键词列表
                            keywords = stage1_df['关键词'].tolist()
                            
                            # 分类关键词
                            results = self.classifier.classify_keywords(keywords, error_callback)
                            
                            # 处理匹配结果
                            matched_indices = []
                            
                            for i, result in enumerate(results):
                                if result['matched_rules']:  # 如果有匹配的规则
                                    matched_indices.append(i)
                            
                            # 如果有匹配项，创建结果DataFrame
                            if matched_indices:
                                matched_df = stage1_df.iloc[matched_indices].copy()
                            else:
                                matched_df = pd.DataFrame(columns=stage1_df.columns)
                        
                        # 限制sheet名长度（Excel限制为31字符）
                        safe_sheet_name = sheet_name[:31]
                        
                        # 只有当有匹配结果时才创建对应的sheet
                        if not matched_df.empty:
                            # 保存到对应的sheet
                            matched_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                    
                    # 处理未匹配项
                    unmatched_df = self._get_unmatched_keywords(stage1_df, sheet2_rules)
                    if not unmatched_df.empty:
                        unmatched_df.to_excel(writer, sheet_name='无匹配规则', index=False)
            
            return stage1_files
        except Exception as e:
            raise Exception(f"处理阶段2失败: {str(e)}")
    
    def process_stage3(self, stage2_files: Dict[str, str], workflow_rules: Dict[str, Any], 
                      error_callback=None) -> Dict[str, str]:
        """处理阶段3：多层级处理（Sheet3+处理）
        
        Args:
            stage2_files: 阶段2更新的文件路径字典
            workflow_rules: 工作流规则字典
            error_callback: 错误回调函数
            
        Returns:
            更新后的文件路径字典
        """
        # 检查是否有Sheet3及以上规则，并按层级排序
        higher_sheets = sorted([k for k in workflow_rules.keys() if k.startswith('Sheet') and int(k[5:]) >= 3],
                             key=lambda x: int(x[5:]))
        if not higher_sheets:
            return stage2_files
        
        try:
            # 处理每个阶段2文件
            for output_name, file_path in stage2_files.items():
                # 读取文件中的所有sheet
                with pd.ExcelFile(file_path) as xls:
                    sheet_names = xls.sheet_names
                    
                    # 跳过分类结果和无匹配规则sheet
                    process_sheets = [s for s in sheet_names if s not in ['分类结果', '无匹配规则']]
                    
                    # 如果没有需要处理的sheet，跳过
                    if not process_sheets:
                        continue
                    
                    # 读取所有sheet的数据
                    sheet_data = {}
                    for sheet in process_sheets:
                        sheet_data[sheet] = pd.read_excel(xls, sheet_name=sheet)
                
                # 处理每个Sheet3及以上规则
                for sheet_key in higher_sheets:
                    sheet_level = int(sheet_key[5:])
                    sheet_rules = workflow_rules[sheet_key]['rules']
                    
                    # 创建新的工作簿用于存储当前层级的结果
                    new_sheet_data = {}
                    
                    # 处理每个sheet
                    for sheet_name, df in sheet_data.items():
                        # 创建新的DataFrame用于存储结果
                        result_df = df.copy()
                        matched_any = False
                        
                        # 处理每条规则
                        for rule_data in sheet_rules:
                            rule = rule_data['rule']
                            col_name = rule_data['sheet_name']
                            
                            # 跳过空规则
                            if not rule or not col_name:
                                continue
                            
                            # 检查上层分类规则
                            if sheet_level > 3 and 'parent_rule' in rule_data:
                                parent_rule = rule_data['parent_rule']
                                if parent_rule != '全':
                                    # 检查父级规则是否存在且有匹配项
                                    parent_col = next((col for col in result_df.columns 
                                                     if col.startswith(parent_rule)), None)
                                    if not parent_col or result_df[parent_col].isna().all():
                                        continue
                            
                            # 检查是否为"全"值
                            if rule == '全':
                                # 全部关键词都匹配
                                result_df[col_name] = '全部匹配'
                                matched_any = True
                            else:
                                # 设置分类器规则
                                self.classifier.set_rules([rule], error_callback)
                                
                                # 获取关键词列表
                                keywords = result_df['关键词'].tolist()
                                
                                # 分类关键词
                                results = self.classifier.classify_keywords(keywords, error_callback)
                                
                                # 添加结果列
                                matched_rules = [r['matched_rules'] for r in results]
                                if any(matched_rules):
                                    result_df[col_name] = matched_rules
                                    matched_any = True
                        
                        # 如果有任何规则匹配成功，保存结果
                        if matched_any:
                            # 限制sheet名长度（Excel限制为31字符）
                            safe_sheet_name = f"{sheet_name[:28]}_{sheet_level}"[:31]
                            new_sheet_data[safe_sheet_name] = result_df
                    
                    # 使用Excel写入器更新文件，一次性写入所有结果
                    if new_sheet_data:
                        with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
                            for sheet_name, df in new_sheet_data.items():
                                df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        # 更新sheet_data用于下一个层级的处理
                        sheet_data = new_sheet_data
            
            return stage2_files
        except Exception as e:
            raise Exception(f"处理阶段3失败: {str(e)}")
            
            return stage2_files
        except Exception as e:
            raise Exception(f"处理阶段3失败: {str(e)}")
    
    def _get_unmatched_keywords(self, df: pd.DataFrame, rules: List[Dict[str, Any]]) -> pd.DataFrame:
        """获取未匹配任何规则的关键词
        
        Args:
            df: 包含关键词的DataFrame
            rules: 规则列表
            
        Returns:
            未匹配的DataFrame
        """
        # 如果规则中包含'全'，则没有未匹配项
        for rule_data in rules:
            if rule_data['rule'] == '全':
                return pd.DataFrame(columns=df.columns)
        
        # 初始化未匹配项
        unmatched_df = df.copy()
        
        # 处理每条规则
        for rule_data in rules:
            rule = rule_data['rule']
            
            # 跳过空规则
            if not rule:
                continue
            
            # 设置分类器规则
            self.classifier.set_rules([rule])
            
            # 获取关键词列表
            keywords = unmatched_df['关键词'].tolist()
            
            # 分类关键词
            results = self.classifier.classify_keywords(keywords)
            
            # 处理匹配结果
            matched_indices = []
            
            for i, result in enumerate(results):
                if result['matched_rules']:  # 如果有匹配的规则
                    matched_indices.append(i)
            
            # 从未匹配项中移除已匹配的行
            if matched_indices:
                unmatched_df = unmatched_df.drop(unmatched_df.index[matched_indices])
        
        return unmatched_df
    
    def process_workflow(self, rules_file: str, classification_file: str, error_callback=None) -> Dict[str, str]:
        """处理完整工作流
        
        Args:
            rules_file: 工作流规则文件路径
            classification_file: 待分类文件路径
            error_callback: 错误回调函数
            
        Returns:
            生成的文件路径字典
        """
        try:
            # 读取工作流规则
            workflow_rules = self.read_workflow_rules(rules_file)
            
            # 读取待分类文件
            keywords_df = self.read_classification_file(classification_file)
            
            # 处理阶段1：基础分类
            stage1_results = self.process_stage1(keywords_df, workflow_rules, error_callback)
            
            # 保存阶段1结果
            stage1_files = self.save_stage1_results(stage1_results)
            
            # 处理阶段2：分层处理
            stage2_files = self.process_stage2(stage1_files, workflow_rules, error_callback)
            
            # 处理阶段3：多层级处理
            final_files = self.process_stage3(stage2_files, workflow_rules, error_callback)
            
            return final_files
        except Exception as e:
            raise Exception(f"处理工作流失败: {str(e)}")
