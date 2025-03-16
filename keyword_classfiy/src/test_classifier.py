from keyword_classifier import KeywordClassifier

def test_term_exclude_rule():
    classifier = KeywordClassifier()
    
    # 测试排除规则
    rule = '培训<学校|中学|中心|班|机构>'
    classifier.set_rules([rule])
    
    # 测试关键词
    keywords = ['培训机构', '培训学校', '职业培训', '培训课程']
    results = classifier.classify_keywords(keywords)
    
    print(f"规则: {rule}")
    print("分类结果:")
    for r in results:
        print(f"{r['keyword']} -> {r['matched_rules']}")
    
    # 测试更复杂的规则
    complex_rules = [
        '培训<学校|中学|中心|班|机构>',
        '教育+(学校|培训)',
        '[在线]教育',
        '(英语|数学|语文)+培训'
    ]
    
    print("\n测试复杂规则:")
    classifier.set_rules(complex_rules)
    for rule in complex_rules:
        print(f"规则: {rule}")
    
    # 测试更多关键词
    more_keywords = [
        '培训机构', '培训学校', '职业培训', '培训课程',
        '教育学校', '教育培训', '在线教育', '教育平台',
        '英语培训', '数学培训', '语文培训', '编程培训'
    ]
    
    results = classifier.classify_keywords(more_keywords)
    print("\n复杂规则分类结果:")
    for r in results:
        print(f"{r['keyword']} -> {r['matched_rules']}")

if __name__ == "__main__":
    test_term_exclude_rule()