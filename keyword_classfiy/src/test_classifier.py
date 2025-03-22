from keyword_classifier import KeywordClassifier
import os

def check_c_character(text):
    """检查字符串中的'c'字符是否为标准ASCII编码"""
    for i, char in enumerate(text.lower()):
        if char == 'c':
            # 获取字符的Unicode码点
            code_point = ord(char)
            # ASCII的'c'的码点是99
            if code_point != 99:
                print(f"警告: 在'{text}'中第{i+1}个位置的'c'字符使用了非标准编码: Unicode U+{code_point:04X}")
                return False
        elif char.lower() in ['с', 'ϲ', 'ꮯ']:  # 一些看起来像'c'的Unicode字符
            code_point = ord(char)
            print(f"警告: 在'{text}'中第{i+1}个位置发现类似'c'的字符: Unicode U+{code_point:04X}")
            return False
    return True

def clean_and_check_rule(rule):
    """清理规则中的不可见字符并检查编码"""
    # 检查是否包含零宽空格等不可见字符
    has_invisible = False
    cleaned_rule = ""
    
    for char in rule:
        code_point = ord(char)
        if code_point in [0x200B, 0x200C, 0x200D, 0xFEFF]:
            print(f"发现不可见字符: U+{code_point:04X} 在规则 '{rule}' 中")
            has_invisible = True
            # 不添加这个字符到清理后的规则
        else:
            cleaned_rule += char
    
    # 如果规则被清理了，打印出来
    if has_invisible:
        print(f"清理前: '{rule}' (长度: {len(rule)})")
        print(f"清理后: '{cleaned_rule}' (长度: {len(cleaned_rule)})")
        
        # 打印每个字符的编码
        print("字符编码详情:")
        for i, char in enumerate(rule):
            print(f"  位置 {i+1}: '{char}' - U+{ord(char):04X}")
    
    return cleaned_rule if has_invisible else rule

def test_term_exclude_rule(file_path):
    classifier = KeywordClassifier(case_sensitive=False)
    
    # # 测试更复杂的规则
    # raw_rules = [item for item in get_root(file_path) if 'c' in item.lower()]
    
    # # 清理并检查规则
    # complex_rules_f = []
    # for rule in raw_rules:
    #     cleaned_rule = clean_and_check_rule(rule)
    #     complex_rules_f.append(cleaned_rule)
        
    #     # 如果规则是单个字符'c'，特别检查
    #     if cleaned_rule.lower() == 'c':
    #         print(f"发现单字符'c'规则，编码: U+{ord(cleaned_rule):04X}")
    
    # # complex_rules_s = ['c','c语言','excel']
    # complex_rules_s = []
    # # 打印手动添加的'c'的编码
    # if complex_rules_s:
    #     print(f"手动添加的'c'编码: U+{ord(complex_rules_s[0]):04X}")
    
    # complex_rules = complex_rules_f + complex_rules_s
    # complex_rules = [clean_and_check_rule(item) for item in get_root(file_path)]
    complex_rules = get_root(file_path)
    print("\n测试复杂规则:")
    classifier.set_rules(complex_rules)
    for rule in classifier.rules:
        print(f"规则: {[rule]}")
        if len(rule) == 1:
            print(f'规则: {[rule]}的码点是: {ord(rule)}')
    
    # 测试更多关键词
    more_keywords = [
        'C语言学什么', 'c语言好学吗', 'c++课程','hcie安全培训费用'
    ]
    
    results = classifier.classify_keywords(more_keywords)
    print("\n复杂规则分类结果:")
    for r in results:
        print(f"{r['keyword']} -> {r['matched_rules']}")

def get_root(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return [line.strip() for line in lines]

if __name__ == "__main__":
    file = r'./分词规则.txt'
    file_path = os.path.abspath(file)

    test_term_exclude_rule(file_path)
    # test_clean(file_path)