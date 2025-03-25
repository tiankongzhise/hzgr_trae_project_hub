from lark import Lark, Transformer, v_args

class KeywordClassifier:
    def __init__(self, case_sensitive=False, separator='&'):
        self.rules = []
        self.parsed_rules = []
        self.case_sensitive = case_sensitive
        self.separator = separator
        self.parser = self._create_parser()
        
    def _preprocess_text(self, text, error_callback=None):
        """预处理文本，清除不可见的干扰字符
        
        Args:
            text: 需要预处理的文本
            error_callback: 错误回调函数，用于将错误信息传递给UI显示
            
        Returns:
            清除干扰字符后的文本
        """
        if not text:
            return text
            
        # 定义需要清除的不可见字符列表
        invisible_chars = [
            0x200B,  # 零宽空格
            0x200C,  # 零宽非连接符
            0x200D,  # 零宽连接符
            0x200E,  # 从左至右标记
            0x200F,  # 从右至左标记
            0x202A,  # 从左至右嵌入
            0x202B,  # 从右至左嵌入
            0x202C,  # 弹出方向格式
            0x202D,  # 从左至右覆盖
            0x202E,  # 从右至左覆盖
            0x2060,  # 单词连接符
            0x2061,  # 函数应用
            0x2062,  # 隐形乘号
            0x2063,  # 隐形分隔符
            0x2064,  # 隐形加号
            0xFEFF,  # 零宽非断空格(BOM)
        ]
        
        """清理规则中的不可见字符并检查编码"""
        # 检查是否包含零宽空格等不可见字符
        has_invisible = False
        cleaned_rule = ""
        
        for char in text:
            code_point = ord(char)
            if code_point in invisible_chars:
                msg = f"发现不可见字符: U+{code_point:04X} 在规则 '{text}' 中"
                print(msg)
                if error_callback:
                    error_callback(msg)
                has_invisible = True
                # 不添加这个字符到清理后的规则
            else:
                cleaned_rule += char
        
        # 如果规则被清理了，打印出来
        if has_invisible:
            msg1 = f"清理前: '{text}' (长度: {len(text)})"
            msg2 = f"清理后: '{cleaned_rule}' (长度: {len(cleaned_rule)})"
            print(msg1)
            print(msg2)
            
            if error_callback:
                error_callback(msg1)
                error_callback(msg2)
            
            # # 打印每个字符的编码
            # print("字符编码详情:")
            # if error_callback:
            #     error_callback("字符编码详情:")
            
            # for i, char in enumerate(text):
            #     char_info = f"  位置 {i+1}: '{char}' - U+{ord(char):04X}"
            #     print(char_info)
            #     if error_callback:
            #         error_callback(char_info)
        
        return cleaned_rule if has_invisible else text

    
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
                # 修复单个字符匹配逻辑 - 移除冗余条件
                return lambda keyword: word_str.lower() in keyword.lower()
    
    def set_rules(self, rules, error_callback=None):
        """设置分词规则
        
        Args:
            rules: 规则列表
            error_callback: 错误回调函数，用于将错误信息传递给UI显示
        """
        # 预处理规则，清除不可见字符
        processed_rules = [self._preprocess_text(rule, error_callback) for rule in rules]
        self.rules = processed_rules
        self.parsed_rules = []
        parse_errors = []
        
        # 解析每条规则
        for i, rule in enumerate(processed_rules):
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
    
    def classify_keywords(self, keywords, error_callback=None):
        """对关键词进行分类（单进程版本）"""
        results = []
        
        # 预处理关键词，清除不可见字符
        processed_keywords = [self._preprocess_text(keyword, error_callback) for keyword in keywords]
        
        for keyword in processed_keywords:
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
                'matched_rules': self.separator.join(matched_rules) if matched_rules else ''
            })
        
        return results
    
    def _process_keyword_batch(self, keyword_batch):
        """处理一批关键词（用于多进程）
        
        Args:
            keyword_batch: 关键词列表
            
        Returns:
            处理结果列表
        """
        results = []
        for keyword in keyword_batch:
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
                'matched_rules': self.separator.join(matched_rules) if matched_rules else ''
            })
        
        return results
    
    def classify_keywords_parallel(self, keywords, error_callback=None, num_processes=None):
        """对关键词进行分类（多进程版本）
        
        Args:
            keywords: 关键词列表
            error_callback: 错误回调函数
            num_processes: 进程数，默认为CPU核心数
            
        Returns:
            分类结果列表
        """
        import pathos.multiprocessing as mp



        # 预处理关键词，清除不可见字符
        processed_keywords = [self._preprocess_text(keyword, error_callback) for keyword in keywords]
        
        # 如果没有指定进程数，使用CPU核心数
        if num_processes is None:
            num_processes = mp.cpu_count()
        
        # 确保进程数不超过关键词数量和CPU核心数
        num_processes = min(num_processes, len(processed_keywords), mp.cpu_count())
        
        # 如果关键词数量很少，直接使用单进程版本
        if len(processed_keywords) < 10 or num_processes <= 1:
            return self.classify_keywords(keywords, error_callback)
        
        # 将关键词分成多个批次
        batch_size = max(1, len(processed_keywords) // num_processes)
        batches = [processed_keywords[i:i+batch_size] for i in range(0, len(processed_keywords), batch_size)]
        
        # 创建进程池
        with mp.Pool(processes=num_processes) as pool:
            # 使用进程池并行处理每个批次
            batch_results = pool.map(self._process_keyword_batch, batches)
        
        # 合并所有批次的结果
        results = []
        for batch in batch_results:
            results.extend(batch)
        
        return results