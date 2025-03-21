from lark import Lark, Transformer, v_args

class KeywordClassifier:
    def __init__(self, case_sensitive=False):
        self.rules = []
        self.parsed_rules = []
        self.case_sensitive = case_sensitive
        self.parser = self._create_parser()
    
    def _create_parser(self):
        """创建Lark解析器"""
        grammar = r"""
            ?start: expr
            
            ?expr: or_expr
            
            ?or_expr: and_expr
                   | or_expr "|" and_expr -> or_op
            
            ?and_expr: atom
                    | and_expr "+" atom -> and_op
            
            ?atom: exact
                 | term_exclude
                 | term
                 | "(" expr ")" -> group
            
            term_exclude: WORD "<" expr ">" -> term_exclude_match
            
            exact: "[" WORD "]" -> exact_match
            exclude: "<" expr ">" -> exclude_match
            term: WORD -> simple_term
            
            WORD: /[^\[\]<>|+()\s]+/
            
            %import common.WS
            %ignore WS
        """
        return Lark(grammar, parser='lalr')
    
    @v_args(inline=True)
    class RuleTransformer(Transformer):
        """转换解析树为可执行的匹配函数"""
        def __init__(self, case_sensitive=False):
            super().__init__()
            self.case_sensitive = case_sensitive
        
        def or_op(self, left, right):
            return lambda keyword: left(keyword) or right(keyword)
        
        def and_op(self, left, right):
            return lambda keyword: left(keyword) and right(keyword)
        
        def group(self, expr):
            return expr
        
        def exact_match(self, word):
            word_str = str(word)
            if self.case_sensitive:
                return lambda keyword: keyword == word_str
            else:
                return lambda keyword: keyword.lower() == word_str.lower()
        
        def exclude_match(self, expr):
            return lambda keyword: not expr(keyword)
        
        def term_exclude_match(self, term, expr):
            term_str = str(term)
            if self.case_sensitive:
                return lambda keyword: term_str in keyword and not expr(keyword)
            else:
                return lambda keyword: term_str.lower() in keyword.lower() and not expr(keyword)
        
        def simple_term(self, word):
            word_str = str(word)
            if self.case_sensitive:
                return lambda keyword: word_str in keyword
            else:
                return lambda keyword: word_str.lower() in keyword.lower()
    
    def set_rules(self, rules, error_callback=None):
        """设置分词规则
        
        Args:
            rules: 规则列表
            error_callback: 错误回调函数，用于将错误信息传递给UI显示
        """
        self.rules = rules
        self.parsed_rules = []
        parse_errors = []
        
        # 解析每条规则
        for i, rule in enumerate(rules):
            try:
                tree = self.parser.parse(rule)
                transformer = self.RuleTransformer(self.case_sensitive)
                matcher = transformer.transform(tree)
                self.parsed_rules.append((rule, matcher))
            except Exception as e:
                error_msg = f"规则 '{rule}' 解析失败: {str(e)}"
                parse_errors.append(error_msg)
                print(error_msg)  # 保留控制台输出
                # 如果提供了错误回调函数，则调用它
                if error_callback:
                    error_callback(error_msg)
        
        return parse_errors  # 返回解析错误列表
    
    def classify_keywords(self, keywords):
        """对关键词进行分类"""
        results = []
        
        for keyword in keywords:
            matched_rules = []
            
            # 对每个关键词应用所有规则
            for rule_text, rule_matcher in self.parsed_rules:
                try:
                    if rule_matcher(keyword):
                        matched_rules.append(rule_text)
                except Exception as e:
                    print(f"应用规则 '{rule_text}' 到关键词 '{keyword}' 时出错: {str(e)}")
            
            # 添加结果
            results.append({
                'keyword': keyword,
                'matched_rules': '|'.join(matched_rules) if matched_rules else ''
            })
        
        return results