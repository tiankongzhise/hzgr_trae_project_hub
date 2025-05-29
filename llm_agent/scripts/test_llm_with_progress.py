#!/usr/bin/env python3
"""测试LLM查询进度条功能"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import RecruitmentProcessor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ProgressBar:
    """简单的进度条显示类"""
    
    def __init__(self, width: int = 50):
        self.width = width
        self.last_update_time = 0
        
    def update(self, progress_info: Dict[str, Any]):
        """更新进度条显示"""
        current_time = time.time()
        
        # 限制更新频率，避免刷屏
        if current_time - self.last_update_time < 0.5:
            return
            
        self.last_update_time = current_time
        
        total = progress_info.get('total_tasks', 0)
        completed = progress_info.get('completed_tasks', 0)
        successful = progress_info.get('successful_tasks', 0)
        failed = progress_info.get('failed_tasks', 0)
        current_task = progress_info.get('current_task', '')
        total_time = progress_info.get('total_time', 0)
        avg_time = progress_info.get('average_time_per_task', 0)
        remaining_time = progress_info.get('estimated_remaining_time', 0)
        
        if total == 0:
            return
            
        # 计算进度百分比
        percentage = (completed / total) * 100
        
        # 绘制进度条
        filled_width = int((completed / total) * self.width)
        bar = '█' * filled_width + '░' * (self.width - filled_width)
        
        # 格式化时间显示
        def format_time(seconds):
            if seconds < 60:
                return f"{seconds:.1f}s"
            elif seconds < 3600:
                return f"{seconds/60:.1f}m"
            else:
                return f"{seconds/3600:.1f}h"
        
        # 清除当前行并显示进度信息
        print(f"\r\033[K", end="")
        print(f"进度: [{bar}] {percentage:.1f}% ({completed}/{total})", end="")
        print(f" | 成功: {successful} | 失败: {failed}", end="")
        print(f" | 总耗时: {format_time(total_time)}", end="")
        
        if avg_time > 0:
            print(f" | 平均: {format_time(avg_time)}/任务", end="")
            
        if remaining_time > 0:
            print(f" | 预计剩余: {format_time(remaining_time)}", end="")
            
        if current_task:
            # 截断过长的任务名
            if len(current_task) > 20:
                current_task = current_task[:17] + "..."
            print(f" | 当前: {current_task}", end="")
            
        sys.stdout.flush()
        
        # 如果完成，换行
        if completed == total:
            print()
            print(f"\n✅ 任务完成！总计: {total} 个任务，成功: {successful} 个，失败: {failed} 个")
            print(f"📊 总耗时: {format_time(total_time)}，平均每任务: {format_time(avg_time)}")


async def test_llm_analysis_with_progress():
    """测试LLM分析功能并显示进度条"""
    print("🚀 开始测试LLM分析功能（带进度条）")
    print("=" * 60)
    
    # 创建进度条
    progress_bar = ProgressBar()
    
    try:
        async with RecruitmentProcessor() as processor:
            # 读取本地文档
            print("📖 正在读取本地招生简章文档...")
            documents = await processor.read_local_documents()
            
            if not documents:
                print("❌ 没有找到本地文档，请先运行爬取任务")
                return
                
            print(f"📄 找到 {len(documents)} 个文档")
            
            # 限制测试文档数量（避免消耗过多API调用）
            test_documents = documents[:5]  # 只测试前5个文档
            print(f"🔬 将分析前 {len(test_documents)} 个文档")
            print()
            
            # 开始分析
            print("🤖 开始LLM分析...")
            start_time = time.time()
            
            analysis_results = await processor.analyze_documents_with_llm(
                test_documents, 
                progress_callback=progress_bar.update
            )
            
            total_time = time.time() - start_time
            
            print("\n" + "=" * 60)
            print("📈 分析结果统计:")
            
            successful_count = sum(1 for r in analysis_results if r.get('success', False))
            failed_count = len(analysis_results) - successful_count
            
            print(f"  📊 总任务数: {len(analysis_results)}")
            print(f"  ✅ 成功: {successful_count}")
            print(f"  ❌ 失败: {failed_count}")
            print(f"  ⏱️  总耗时: {total_time:.2f} 秒")
            print(f"  📏 平均耗时: {total_time/len(analysis_results):.2f} 秒/任务")
            
            # 显示成功分析的学校信息
            if successful_count > 0:
                print("\n🏫 成功分析的学校:")
                for i, result in enumerate(analysis_results):
                    if result.get('success', False):
                        school_info = result.get('school_info', {})
                        school_name = school_info.get('full_name', '未知学校')
                        confidence = result.get('confidence', 0)
                        analysis_time = result.get('analysis_time', 0)
                        print(f"  {i+1}. {school_name} (置信度: {confidence:.2f}, 耗时: {analysis_time:.2f}s)")
            
            # 显示失败的任务
            if failed_count > 0:
                print("\n❌ 失败的任务:")
                for i, result in enumerate(analysis_results):
                    if not result.get('success', False):
                        error = result.get('error', '未知错误')
                        print(f"  {i+1}. 错误: {error}")
                        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        logger.error(f"测试失败: {e}", exc_info=True)


async def main():
    """主函数"""
    try:
        await test_llm_analysis_with_progress()
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断测试")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        logger.error(f"程序异常: {e}", exc_info=True)


if __name__ == "__main__":
    # Windows平台兼容性处理
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行测试
    asyncio.run(main())
