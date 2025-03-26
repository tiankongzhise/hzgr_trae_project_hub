from src.keyword_classifier import KeywordClassifier
from src.excel_handler import ExcelHandler



class TestKeywordClassifier:
    def __init__(self,rule_file:str,keyword_file:str):
        self.rule_file = rule_file
        self.keyword_file = keyword_file
        self.excel_handler = ExcelHandler()
        self.keyword_classifier = KeywordClassifier()
    
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
    
        


def main():
    test_keyword_classfier = TestKeywordClassifier(rule_file='./data/分词规则.xlsx',keyword_file='./data/待分类.xlsx')
    test_keyword_classfier.test_keyword_classfier()

if __name__ == '__main__':
    main()

