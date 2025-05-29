#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM服务模块
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.llm_service import LLMService
from src.models.schemas import LLMAnalysisRequest, LLMAnalysisResponse
from src.utils.logger import get_logger
from src.config import get_settings

logger = get_logger(__name__)


async def test_llm_service_init():
    """测试LLM服务初始化"""
    print("\n=== 测试LLM服务初始化 ===")
    
    try:
        settings = get_settings()
        print(f"LLM配置:")
        print(f"  API Key: {settings.llm.api_key[:10]}...")
        print(f"  Base URL: {settings.llm.base_url}")
        print(f"  Model: {settings.llm.model}")
        print(f"  Max Tokens: {settings.llm.max_tokens}")
        print(f"  Temperature: {settings.llm.temperature}")
        
        async with LLMService() as llm_service:
            print("✓ LLM服务初始化成功")
            return True
            
    except Exception as e:
        print(f"✗ LLM服务初始化失败: {e}")
        return False


async def test_build_prompt():
    """测试构建提示词"""
    print("\n=== 测试构建提示词 ===")
    
    try:
        async with LLMService() as llm_service:
            test_content = "这是一个测试招生简章内容，包含学校信息和招生要求。"
            school_name = "测试学校"
            source_url = "https://example.com/test.pdf"
            
            prompt = llm_service._build_analysis_prompt(test_content, school_name)
            
            if prompt and len(prompt) > 0:
                print(f"✓ 提示词构建成功，长度: {len(prompt)}")
                print(f"提示词预览: {prompt[:200]}...")
                return True
            else:
                print("✗ 提示词构建失败或为空")
                return False
                
    except Exception as e:
        print(f"✗ 提示词构建测试失败: {e}")
        return False


async def test_analyze_recruitment_content():
    """测试分析招生简章内容"""
    print("\n=== 测试分析招生简章内容 ===")
    
    try:
        async with LLMService() as llm_service:
            # 创建测试请求
            test_request = LLMAnalysisRequest(
                content="""湖南工业职业技术学院2025年招生简章
                
学校全称：湖南工业职业技术学院
地点：湖南省长沙市
主管部门：湖南省教育厅
办学层次：高职专科
院校代号：4343
办学类型：公办

学校是国家示范性高等职业院校，湖南省卓越高等职业技术学院建设单位。

优势专业：
1. 机械制造与自动化 - 国家重点专业
2. 数控技术 - 省级特色专业
3. 工业机器人技术 - 新兴专业

招生计划：
- 机械制造与自动化：100人
- 数控技术：80人
- 工业机器人技术：60人

录取要求：
1. 高中毕业或同等学历
2. 身体健康，符合专业要求
3. 按高考成绩择优录取
""",
                school_name="湖南工业职业技术学院",
                source_url="https://example.com/hngzy_2025.pdf"
            )
            
            print(f"测试内容长度: {len(test_request.content)}")
            print(f"学校名称: {test_request.school_name}")
            
            # 分析内容
            result = await llm_service.analyze_recruitment_content(test_request)
            
            if result and hasattr(result, 'school_info'):
                print(f"✓ LLM分析成功")
                print(f"  学校全称: {result.school_info.full_name}")
                print(f"  地点: {result.school_info.location}")
                print(f"  主管部门: {result.school_info.supervisor}")
                print(f"  办学层次: {result.school_info.education_level}")
                print(f"  院校代号: {result.school_info.institution_code}")
                print(f"  办学类型: {result.school_info.institution_type}")
                print(f"  是否示范院校: {result.school_info.is_demonstration}")
                print(f"  优势专业: {result.school_info.advantage_majors}")
                print(f"  置信度: {result.confidence}")
                print(f"  分析时间: {result.analysis_time}秒")
                
                if result.school_info.advantage_majors:
                    majors_list = result.school_info.advantage_majors.split(',') if isinstance(result.school_info.advantage_majors, str) else []
                    print(f"  优势专业列表:")
                    for major in majors_list[:3]:  # 只显示前3个
                        print(f"    - {major.strip()}")
                
                return True
            else:
                print(f"✗ LLM分析失败: {result.error_message if result else '未知错误'}")
                return False
                
    except Exception as e:
        print(f"✗ LLM分析测试失败: {e}")
        return False


async def test_batch_analyze():
    """测试批量分析"""
    print("\n=== 测试批量分析 ===")
    
    try:
        async with LLMService() as llm_service:
            # 创建多个测试请求
            test_requests = [
                LLMAnalysisRequest(
                    content="长沙民政职业技术学院招生简章，公办院校，民政部直属，社会工作专业为特色。",
                    school_name="长沙民政职业技术学院",
                    source_url="https://example.com/csmz.pdf"
                ),
                LLMAnalysisRequest(
                    content="湖南铁道职业技术学院招生简章，公办院校，铁路特色，轨道交通专业优势明显。",
                    school_name="湖南铁道职业技术学院",
                    source_url="https://example.com/hntd.pdf"
                ),
            ]
            
            print(f"批量分析 {len(test_requests)} 个请求")
            
            # 批量分析
            results = await llm_service.batch_analyze(test_requests)
            
            if results and len(results) == len(test_requests):
                print(f"✓ 批量分析成功，处理了 {len(results)} 个请求")
                
                successful = sum(1 for r in results if r.confidence > 0)
                failed = len(results) - successful
                
                print(f"  成功: {successful} 个")
                print(f"  失败: {failed} 个")
                
                # 显示成功的结果
                for i, result in enumerate(results):
                    if result.confidence > 0:
                        print(f"  结果{i+1}: {result.school_info.full_name} - {result.school_info.location}")
                        print(f"    置信度: {result.confidence}")
                    else:
                        print(f"  结果{i+1}: 分析失败，置信度为0")
                
                return successful > 0
            else:
                print(f"✗ 批量分析失败，期望 {len(test_requests)} 个结果，实际 {len(results) if results else 0} 个")
                return False
                
    except Exception as e:
        print(f"✗ 批量分析测试失败: {e}")
        return False


async def test_validate_analysis_result():
    """测试分析结果验证"""
    print("\n=== 测试分析结果验证 ===")
    
    try:
        async with LLMService() as llm_service:
            # 创建一个模拟的分析结果
            from src.models.schemas import SchoolCreate
            
            test_school_info = SchoolCreate(
                full_name="测试学校",
                location="测试地点",
                supervisor="测试部门",
                education_level="高职专科",
                institution_code="1234",
                institution_type="公办",
                is_demonstration=True,
                is_backbone=False,
                is_excellent=False,
                is_chuyi_high_level=False,
                advantage_majors="测试专业1,测试专业2",
                advantage_basis="测试依据",
                raw_content="测试原始内容",
                source_url="https://example.com/test.pdf"
            )
            
            # 创建一个测试响应
            test_response = LLMAnalysisResponse(
                school_info=test_school_info,
                confidence=0.85,
                analysis_time=1.5
            )
            
            # 验证结果
            validation_report = await llm_service.validate_analysis_result(test_response)
            
            print(f"验证结果: {'有效' if validation_report['is_valid'] else '无效'}")
            print(f"警告数量: {len(validation_report['warnings'])}")
            print(f"错误数量: {len(validation_report['errors'])}")
            print(f"建议数量: {len(validation_report['suggestions'])}")
            
            if validation_report['is_valid']:
                print("✓ 分析结果验证成功")
                return True
            else:
                print("✗ 分析结果验证失败")
                for error in validation_report['errors']:
                    print(f"  错误: {error}")
                return False
                
    except Exception as e:
        print(f"✗ 分析结果验证测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("开始测试LLM服务模块")
    print("=" * 50)
    
    tests = [
        ("LLM服务初始化", test_llm_service_init),
        ("构建提示词", test_build_prompt),
        ("分析招生简章内容", test_analyze_recruitment_content),
        ("批量分析", test_batch_analyze),
        ("分析结果验证", test_validate_analysis_result),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n正在测试: {test_name}")
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✓ {test_name} 测试通过")
            else:
                print(f"✗ {test_name} 测试失败")
                
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！")
        return True
    else:
        print(f"⚠️  有 {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生异常: {e}")
        sys.exit(1)
