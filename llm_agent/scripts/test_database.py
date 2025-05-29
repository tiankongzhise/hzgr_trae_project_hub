#!/usr/bin/env python3
"""数据库服务测试脚本"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.models.schemas import SchoolCreate, SchoolUpdate
from src.config import get_settings


async def test_database_connection():
    """测试数据库连接"""
    print("\n=== 测试数据库连接 ===")
    
    try:
        settings = get_settings()
        print(f"数据库配置:")
        print(f"  URL: {settings.database.url[:50]}...")
        print(f"  Pool Size: {settings.database.pool_size}")
        print(f"  Max Overflow: {settings.database.max_overflow}")
        
        async with DatabaseService() as db_service:
            # 测试连接
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


async def test_school_crud():
    """测试学校CRUD操作"""
    print("\n=== 测试学校CRUD操作 ===")
    
    try:
        async with DatabaseService() as db_service:
            # 创建测试学校
            test_school = SchoolCreate(
                full_name="测试职业技术学院",
                location="湖南省长沙市",
                supervisor="湖南省教育厅",
                education_level="高职专科",
                institution_code="TEST001",
                institution_type="公办",
                is_demonstration=True,
                is_backbone=False,
                is_excellent=False,
                is_chuyi_high_level=False,
                advantage_majors="计算机技术,软件技术",
                advantage_basis="省级重点专业",
                raw_content="测试招生简章内容",
                source_url="https://example.com/test.pdf"
            )
            
            # 创建学校
            created_school = await db_service.create_school(test_school)
            print(f"✓ 学校创建成功: ID={created_school.id}, 名称={created_school.full_name}")
            
            # 根据ID查询学校
            school_by_id = await db_service.get_school_by_id(created_school.id)
            if school_by_id:
                print(f"✓ 根据ID查询成功: {school_by_id.full_name}")
            else:
                print("✗ 根据ID查询失败")
                return False
            
            # 根据名称查询学校
            school_by_name = await db_service.get_school_by_name("测试职业技术学院")
            if school_by_name:
                print(f"✓ 根据名称查询成功: {school_by_name.full_name}")
            else:
                print("✗ 根据名称查询失败")
                return False
            
            # 更新学校信息
            update_data = SchoolUpdate(
                location="湖南省株洲市",
                advantage_majors="计算机技术,软件技术,人工智能技术"
            )
            updated_school = await db_service.update_school(created_school.id, update_data)
            if updated_school and updated_school.location == "湖南省株洲市":
                print(f"✓ 学校更新成功: 新地点={updated_school.location}")
            else:
                print("✗ 学校更新失败")
                return False
            
            # 查询所有学校
            all_schools = await db_service.get_schools(limit=10)
            print(f"✓ 查询所有学校成功: 共{len(all_schools)}所学校")
            
            # 删除测试学校
            deleted = await db_service.delete_school(created_school.id)
            if deleted:
                print("✓ 学校删除成功")
            else:
                print("✗ 学校删除失败")
                return False
            
            return True
            
    except Exception as e:
        print(f"✗ 学校CRUD操作测试失败: {e}")
        return False


async def test_batch_operations():
    """测试批量操作"""
    print("\n=== 测试批量操作 ===")
    
    try:
        async with DatabaseService() as db_service:
            # 创建多个测试学校
            test_schools = [
                SchoolCreate(
                    full_name=f"批量测试学校{i}",
                    location="湖南省长沙市",
                    supervisor="湖南省教育厅",
                    education_level="高职专科",
                    institution_code=f"BATCH{i:03d}",
                    institution_type="公办",
                    advantage_majors="测试专业",
                    raw_content=f"批量测试内容{i}",
                    source_url=f"https://example.com/batch{i}.pdf"
                )
                for i in range(1, 4)
            ]
            
            # 批量创建
            created_schools = await db_service.batch_create_schools(test_schools)
            print(f"✓ 批量创建成功: 创建了{len(created_schools)}所学校")
            
            # 搜索学校
            search_results = await db_service.search_schools("批量测试")
            print(f"✓ 搜索成功: 找到{len(search_results)}所匹配的学校")
            
            # 清理测试数据
            for school in created_schools:
                await db_service.delete_school(school.id)
            print("✓ 测试数据清理完成")
            
            return True
            
    except Exception as e:
        print(f"✗ 批量操作测试失败: {e}")
        return False


async def test_statistics():
    """测试统计功能"""
    print("\n=== 测试统计功能 ===")
    
    try:
        async with DatabaseService() as db_service:
            # 获取统计信息
            stats = await db_service.get_statistics()
            print(f"✓ 统计信息获取成功:")
            print(f"  总学校数: {stats.get('total_schools', 0)}")
            print(f"  示范院校数: {stats.get('demonstration_schools', 0)}")
            print(f"  骨干院校数: {stats.get('backbone_schools', 0)}")
            print(f"  卓越院校数: {stats.get('excellent_schools', 0)}")
            print(f"  楚怡高水平院校数: {stats.get('chuyi_high_level_schools', 0)}")
            
            return True
            
    except Exception as e:
        print(f"✗ 统计功能测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("开始测试数据库服务模块")
    print("=" * 50)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("创建表", test_create_tables),
        ("学校CRUD操作", test_school_crud),
        ("批量操作", test_batch_operations),
        ("统计功能", test_statistics),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n正在测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                print(f"✓ {test_name} 测试通过")
            else:
                print(f"✗ {test_name} 测试失败")
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 50)
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
    finally:
        # 确保所有异步资源都被正确清理
        import time
        time.sleep(0.1)
