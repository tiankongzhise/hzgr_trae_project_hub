from pathlib import Path
from .keyword_classifier import KeywordClassifier
from .excel_handler import ExcelHandler
from . import models
from typing import List,Dict

import pandas as pd
import datetime


class WorkFlowProcessor:
    def __init__(self,
                 excel_handler: ExcelHandler | None = None,
                 keyword_classifier: KeywordClassifier | None = None):
        """初始化工作流处理器
        
        Args:
            classifier: 关键词分类器实例，如果为None则创建新实例
            excel_handler: Excel处理器实例，如果为None则创建新实例
        """
        self.excel_handler = excel_handler or ExcelHandler()
        self.classifier = keyword_classifier or KeywordClassifier()
        self.output_dir = Path('./工作流结果')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    
    def _transfrom_unmathced_keywords(self,unmatched_keywords:List[models.UnMatchedKeyword])->pd.DataFrame:
        result = []
        for unmatched_keyword in unmatched_keywords:
            temp_dict = {}
            temp_dict['关键词'] = unmatched_keyword.keyword
            temp_dict['分类层级'] = unmatched_keyword.level
            if unmatched_keyword.parent_rule:
                temp_dict['父级规则'] = unmatched_keyword.parent_rule
            result.append(temp_dict)
        return pd.DataFrame(result)
    
    def _transfrom_classified_keywords(self,classified_keywords:List[models.ClassifiedKeyword])->pd.DataFrame:
        result = []
        for classified_keyword in classified_keywords:
            temp_dict = {}
            temp_dict['关键词'] = classified_keyword.keyword
            temp_dict['匹配的规则'] = classified_keyword.matched_rule
            if classified_keyword.parent_rule:
                temp_dict['父级规则'] = classified_keyword.parent_rule
            result.append(temp_dict)
        return pd.DataFrame(result)
                
            
        

    def _transform_to_df(self,data:List[models.UnMatchedKeyword|models.ClassifiedKeyword])->pd.DataFrame:
        map_func = {
            models.UnMatchedKeyword:self._transfrom_unmathced_keywords,
            models.ClassifiedKeyword:self._transfrom_classified_keywords
        }
        return map_func[type(data[0])](data)
        
        
    
    def process_stage1(self,keywords:models.UnclassifiedKeywords,workflow_rules:models.WorkFlowRules,
                       error_callback=None)->models.ClassifiedResult:
        """处理第一阶段的关键词分类"""
        try:
            classified_keywords = []
            unclassified_keywords = []
            # 获取一阶段分类规则
            stage1_rules = workflow_rules.get_rules_by_level(1)
            mapping_dict = {}
            rules = []
            for rule in stage1_rules.rules:
                mapping_dict[rule.rule] = {"分类文件":rule.output_name}
                rules.append(rule.rule)
            # 设置分类规则
            self.classifier.set_rules(models.SourceRules(data=rules,error_callback=error_callback))
            # 分类关键词
            classify_result = self.classifier.classify_keywords(keywords)
            # 处理分类结果
            for temp in classify_result:
                keyword = temp.keyword
                matched_rules = temp.matched_rule
                if matched_rules:
                    classified_keywords.append(
                        models.ClassifiedKeyword(
                            level=1,
                            keyword=keyword,
                            matched_rule=matched_rules,
                            output_name=mapping_dict[matched_rules]['分类文件'],
                            output_sheet_name='Sheet1'
                            ))
                else:
                    unclassified_keywords.append(
                        models.UnMatchedKeyword(
                            level=1,
                            keyword=keyword,
                            output_name='未匹配关键词',
                            output_sheet_name='Sheet1'
                            )
                    )
            return models.ClassifiedResult(classified_keywords=classified_keywords,unclassified_keywords=unclassified_keywords)
        except Exception as e:
            msg = f"获取一阶段分类规则失败：{e}"
            if error_callback:
                error_callback(f"获取一阶段分类规则失败：{e}")
            raise Exception(msg) from e

    def save_stage1_results(self,classified_result:models.ClassifiedResult,error_callback=None)->dict[str,Path]:
        """保存第一阶段分类结果
        
        Args:
            classified_result: 分类结果
            error_callback: 错误回调函数
            
        Returns:
            保存的文件路径字典
        """
        success_file_paths = {}
        try:
            # 获取分类结果
            unmatched_keywords = classified_result.get_grouped_keywords(group_by='output_name',match_type='unmatch')
            matched_keywords = classified_result.get_grouped_keywords(group_by='output_name',match_type='match')
            
            try:
                # 保存分类失败的关键词
                if unmatched_keywords:
                    for output_name, unclassify_keyword_list in unmatched_keywords.items():
                        output_file = self.output_dir / f'{output_name}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
                        df = self._transform_to_df(unclassify_keyword_list)
                        self.excel_handler.save_results(df, output_file,sheet_name='Sheet1')
            except Exception as e:
                err_msg = f'保存分类失败的关键词失败：{e}'
                if error_callback:
                    error_callback(err_msg)
                raise Exception(f"保存分类失败的关键词失败：{e}")
            
            try:
                if matched_keywords:
                    for output_name, matched_keyword_list in matched_keywords.items():
                        output_file = self.output_dir / f'{output_name}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
                        df = self._transform_to_df(matched_keyword_list)
                        self.excel_handler.save_results(df, output_file,sheet_name='Sheet1')
                        success_file_paths[output_name] = output_file
                    return success_file_paths
            except Exception as e:
                err_msg = f'保存分类成功的关键词失败：{e}'
                if error_callback:
                    error_callback(err_msg)
                raise Exception(f"保存分类成功的关键词失败：{e}")
        except Exception as e:
            err_msg = f'获取分类结果失败：{e}'
            if error_callback:
                error_callback(err_msg)
            raise Exception(f"获取分类结果失败：{e}")
    

    def process_stage2(self, stage1_files: Dict[str, Path], workflow_rules: models.WorkFlowRules, 
                      error_callback=None) -> models.ClassifiedResult:
        """处理阶段2：分层处理（Sheet2处理）
        
        Args:
            stage1_files: 阶段1生成的文件路径字典
            workflow_rules: 工作流规则字典
            error_callback: 错误回调函数
            
        Returns:
            更新后的文件路径字典
        """
        # 检查是否有Sheet2规则
        if workflow_rules['Sheet2']:
            return stage1_files
        
        try:
            # 获取Sheet2规则
            sheet2_rules = workflow_rules.filter_rules(source_sheet_name='Sheet2')
            # 处理每个阶段1文件
            for output_name, file_path in stage1_files.items():
                # 读取阶段1文件
                with pd.ExcelFile(file_path) as xls:
                    stage1_df = pd.read_excel(xls, sheet_name='Sheet1')
                rule_ouput_name_mapping = {}
                # 使用Excel写入器追加新Sheet
                with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
                    # 处理每条Sheet2规则
                    
                    for rule_data in sheet2_rules.filter_rules(output_name=output_name).rules:
                        rule = rule_data.rule
                        if rule_ouput_name_mapping.get(rule) is None:
                            rule_ouput_name_mapping[rule] = rule_data.classified_sheet_name
                        
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
    


    def process_workflow(self, rules_file: Path, classification_file: Path, error_callback=None):
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
            workflow_rules = self.excel_handler.read_workflow_rules(rules_file)
            # 读取待分类文件
            keywords_df = self.excel_handler.read_keyword_file(classification_file)
            # 处理阶段1：基础分类
            stage1_results = self.process_stage1(keywords_df, workflow_rules, error_callback)
            
            # 保存阶段1结果
            stage1_files = self.save_stage1_results(stage1_results)
            print(stage1_files)

        except Exception as e:
            err_msg = f'处理完整工作流失败：{e}'
            if error_callback:
                error_callback(err_msg)
            raise Exception(f"处理完整工作流失败：{e}")
