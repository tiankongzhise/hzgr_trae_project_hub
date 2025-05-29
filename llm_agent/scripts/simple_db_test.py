#!/usr/bin/env python3
"""
简化的数据库服务测试脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import setup_logging
from src.services.database_service import DatabaseService
from src.models.schemas import SchoolCreate


async def test_basic_connection():
    """测试基本数据库连接"""
    print("=== 测试数据库连接 ===")
    try:
        async with DatabaseService() as db_service:
            await db_service.test_connection()
            print("✓ 数据库连接成功")
            return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False


async def test_create_tables():
    """测试创建表"""
    print("\n=== 测试创建表 ===")
    try:
        async with DatabaseService() as db_service:
            await db_service.create_tables()
            print("✓ 数据库表创建成功")
            return True
    except Exception as e:
        print(f"✗ 数据库表创建失败: {e}")
        return False


async def test_simple_crud():
    """测试简单的CRUD操作"""
    print("\n=== 测试简单CRUD操作 ===")
    try:
        async with DatabaseService() as db_service:
            # 创建测试学校
            test_school = SchoolCreate(
                full_name="测试学校",
                short_name="测试",
                location="测试市",
                school_type="高职",
                advantage_majors="计算机技术",
                contact_info="测试联系方式"
            )
            
            # 创建学校
            result = await db_service.create_school(test_school)
            if result.success:
                school_id = result.data.id
                print(f"✓ 学校创建成功，ID: {school_id}")
                
                # 查询学校
                school = await db_service.get_school_by_id(school_id)
                if school:
                    print(f"✓ 学校查询成功: {school.full_name}")
                    
                    # 删除测试数据
                    delete_result = await db_service.delete_school(school_id)
                    if delete_result.success:
                        print("✓ 测试数据清理成功")
                        return True
                    else:
                        print("✗ 测试数据清理失败")
                        return False
                else:
                    print("✗ 学校查询失败")
                    return False
            else:
                print(f"✗ 学校创建失败: {result.error}")
                return False
                
    except Exception as e:
        print(f"✗ CRUD操作测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("开始简化数据库服务测试")
    print("=" * 40)
    
    # 初始化日志
    setup_logging()
    
    tests = [
        ("数据库连接", test_basic_connection),
        ("创建表", test_create_tables),
        ("简单CRUD操作", test_simple_crud),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 40)
    print("测试结果汇总:")
    passed = 0
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("🎉 所有测试都通过了！")
    else:
        print(f"⚠️  有 {len(results) - passed} 个测试失败")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试执行出错: {e}")
