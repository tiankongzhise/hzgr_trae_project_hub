"""数据库服务模块"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import select, update, delete, and_, or_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import School, get_session, create_tables as db_create_tables, get_engine
from ..models.schemas import (
    SchoolCreate,
    SchoolUpdate,
    SchoolResponse,
    DatabaseOperationResult,
)
from ..utils.decorators import monitor_performance, database_operation
from ..utils.logger import get_logger, DatabaseErrorLogger
from ..utils.retry import retry_database_operation, RetryConfig

logger = get_logger(__name__)


class DatabaseService:
    """数据库服务类"""
    
    def __init__(self):
        self.error_logger = DatabaseErrorLogger()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        # 清理资源（如果需要）
        pass
    
    async def test_connection(self):
        """测试数据库连接"""
        try:
            engine = get_engine()
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("数据库连接测试成功")
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            raise
    
    async def create_tables(self):
        """创建数据库表"""
        await db_create_tables()
    
    @monitor_performance()
    @database_operation("create_school")
    async def create_school(self, school_data: SchoolCreate) -> DatabaseOperationResult:
        """创建学校记录"""
        start_time = datetime.now()
        
        async def _create_operation():
            async for session in get_session():
                try:
                    # 检查是否已存在相同名称的学校
                    existing_school = await session.execute(
                        select(School).where(School.full_name == school_data.full_name)
                    )
                    if existing_school.scalar_one_or_none():
                        raise IntegrityError(
                            "学校已存在",
                            "duplicate_school",
                            {"full_name": school_data.full_name}
                        )
                    
                    # 创建新学校记录
                    school = School(**school_data.model_dump())
                    session.add(school)
                    await session.commit()
                    await session.refresh(school)
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"成功创建学校记录: {school.full_name} (ID: {school.id})")
                    
                    return DatabaseOperationResult(
                        success=True,
                        affected_rows=1,
                        execution_time=execution_time,
                    )
                    
                except IntegrityError as e:
                    await session.rollback()
                    execution_time = (datetime.now() - start_time).total_seconds()
                    error_msg = f"学校创建失败，完整性约束违反: {e}"
                    logger.error(error_msg)
                    
                    return DatabaseOperationResult(
                        success=False,
                        affected_rows=0,
                        error_message=error_msg,
                        execution_time=execution_time,
                    )
                    
                except Exception as e:
                    await session.rollback()
                    raise e
        
        try:
            return await retry_database_operation(
                _create_operation,
                config=RetryConfig(max_attempts=3, base_delay=1.0)
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"学校创建最终失败: {e}"
            self.error_logger.log_error("create_school", e, school_data.model_dump())
            
            return DatabaseOperationResult(
                success=False,
                affected_rows=0,
                error_message=error_msg,
                execution_time=execution_time,
            )
    
    @monitor_performance()
    @database_operation("get_school_by_id")
    async def get_school_by_id(self, school_id: int) -> Optional[SchoolResponse]:
        """根据ID获取学校信息"""
        async def _get_operation():
            async for session in get_session():
                result = await session.execute(
                    select(School).where(School.id == school_id)
                )
                school = result.scalar_one_or_none()
                
                if school:
                    return SchoolResponse.model_validate(school)
                return None
        
        try:
            return await retry_database_operation(_get_operation)
        except Exception as e:
            logger.error(f"获取学校信息失败 (ID: {school_id}): {e}")
            return None
    
    @monitor_performance()
    @database_operation("get_school_by_name")
    async def get_school_by_name(self, school_name: str) -> Optional[SchoolResponse]:
        """根据名称获取学校信息"""
        async def _get_operation():
            async for session in get_session():
                result = await session.execute(
                    select(School).where(School.full_name == school_name)
                )
                school = result.scalar_one_or_none()
                
                if school:
                    return SchoolResponse.model_validate(school)
                return None
        
        try:
            return await retry_database_operation(_get_operation)
        except Exception as e:
            logger.error(f"获取学校信息失败 (名称: {school_name}): {e}")
            return None
    
    @monitor_performance()
    @database_operation("update_school")
    async def update_school(self, school_id: int, school_data: SchoolUpdate) -> DatabaseOperationResult:
        """更新学校信息"""
        start_time = datetime.now()
        
        async def _update_operation():
            async for session in get_session():
                try:
                    # 构建更新数据（排除None值）
                    update_data = {k: v for k, v in school_data.model_dump().items() if v is not None}
                    
                    if not update_data:
                        execution_time = (datetime.now() - start_time).total_seconds()
                        return DatabaseOperationResult(
                            success=True,
                            affected_rows=0,
                            error_message="没有需要更新的数据",
                            execution_time=execution_time,
                        )
                    
                    # 执行更新
                    result = await session.execute(
                        update(School)
                        .where(School.id == school_id)
                        .values(**update_data)
                    )
                    
                    await session.commit()
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    affected_rows = result.rowcount
                    
                    if affected_rows > 0:
                        logger.info(f"成功更新学校记录: ID {school_id}")
                    else:
                        logger.warning(f"未找到要更新的学校记录: ID {school_id}")
                    
                    return DatabaseOperationResult(
                        success=True,
                        affected_rows=affected_rows,
                        execution_time=execution_time,
                    )
                    
                except Exception as e:
                    await session.rollback()
                    raise e
        
        try:
            return await retry_database_operation(
                _update_operation,
                config=RetryConfig(max_attempts=3, base_delay=1.0)
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"学校更新最终失败: {e}"
            self.error_logger.log_error("update_school", e, {"school_id": school_id, **school_data.model_dump()})
            
            return DatabaseOperationResult(
                success=False,
                affected_rows=0,
                error_message=error_msg,
                execution_time=execution_time,
            )
    
    @monitor_performance()
    @database_operation("delete_school")
    async def delete_school(self, school_id: int) -> DatabaseOperationResult:
        """删除学校记录"""
        start_time = datetime.now()
        
        async def _delete_operation():
            async for session in get_session():
                try:
                    result = await session.execute(
                        delete(School).where(School.id == school_id)
                    )
                    
                    await session.commit()
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    affected_rows = result.rowcount
                    
                    if affected_rows > 0:
                        logger.info(f"成功删除学校记录: ID {school_id}")
                    else:
                        logger.warning(f"未找到要删除的学校记录: ID {school_id}")
                    
                    return DatabaseOperationResult(
                        success=True,
                        affected_rows=affected_rows,
                        execution_time=execution_time,
                    )
                    
                except Exception as e:
                    await session.rollback()
                    raise e
        
        try:
            return await retry_database_operation(
                _delete_operation,
                config=RetryConfig(max_attempts=3, base_delay=1.0)
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"学校删除最终失败: {e}"
            self.error_logger.log_error("delete_school", e, {"school_id": school_id})
            
            return DatabaseOperationResult(
                success=False,
                affected_rows=0,
                error_message=error_msg,
                execution_time=execution_time,
            )
    
    @monitor_performance()
    @database_operation("list_schools")
    async def list_schools(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SchoolResponse]:
        """获取学校列表"""
        async def _list_operation():
            async for session in get_session():
                query = select(School)
                
                # 应用过滤条件
                if filters:
                    conditions = []
                    
                    if "institution_type" in filters:
                        conditions.append(School.institution_type == filters["institution_type"])
                    
                    if "education_level" in filters:
                        conditions.append(School.education_level == filters["education_level"])
                    
                    if "is_demonstration" in filters:
                        conditions.append(School.is_demonstration == filters["is_demonstration"])
                    
                    if "is_backbone" in filters:
                        conditions.append(School.is_backbone == filters["is_backbone"])
                    
                    if "is_excellent" in filters:
                        conditions.append(School.is_excellent == filters["is_excellent"])
                    
                    if "is_chuyi_high_level" in filters:
                        conditions.append(School.is_chuyi_high_level == filters["is_chuyi_high_level"])
                    
                    if "location_contains" in filters:
                        conditions.append(School.location.contains(filters["location_contains"]))
                    
                    if "name_contains" in filters:
                        conditions.append(School.full_name.contains(filters["name_contains"]))
                    
                    if conditions:
                        query = query.where(and_(*conditions))
                
                # 应用分页
                query = query.offset(skip).limit(limit).order_by(School.created_at.desc())
                
                result = await session.execute(query)
                schools = result.scalars().all()
                
                return [SchoolResponse.model_validate(school) for school in schools]
        
        try:
            return await retry_database_operation(_list_operation)
        except Exception as e:
            logger.error(f"获取学校列表失败: {e}")
            return []
    
    @monitor_performance()
    @database_operation("count_schools")
    async def count_schools(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计学校数量"""
        async def _count_operation():
            async for session in get_session():
                query = select(School.id)
                
                # 应用过滤条件（与list_schools相同的逻辑）
                if filters:
                    conditions = []
                    
                    if "institution_type" in filters:
                        conditions.append(School.institution_type == filters["institution_type"])
                    
                    if "education_level" in filters:
                        conditions.append(School.education_level == filters["education_level"])
                    
                    if "is_demonstration" in filters:
                        conditions.append(School.is_demonstration == filters["is_demonstration"])
                    
                    if "is_backbone" in filters:
                        conditions.append(School.is_backbone == filters["is_backbone"])
                    
                    if "is_excellent" in filters:
                        conditions.append(School.is_excellent == filters["is_excellent"])
                    
                    if "is_chuyi_high_level" in filters:
                        conditions.append(School.is_chuyi_high_level == filters["is_chuyi_high_level"])
                    
                    if "location_contains" in filters:
                        conditions.append(School.location.contains(filters["location_contains"]))
                    
                    if "name_contains" in filters:
                        conditions.append(School.full_name.contains(filters["name_contains"]))
                    
                    if conditions:
                        query = query.where(and_(*conditions))
                
                result = await session.execute(query)
                return len(result.scalars().all())
        
        try:
            return await retry_database_operation(_count_operation)
        except Exception as e:
            logger.error(f"统计学校数量失败: {e}")
            return 0
    
    @monitor_performance()
    @database_operation("batch_create_schools")
    async def batch_create_schools(self, schools_data: List[SchoolCreate]) -> List[DatabaseOperationResult]:
        """批量创建学校记录"""
        results = []
        
        # 使用信号量限制并发数
        semaphore = asyncio.Semaphore(5)  # 最多5个并发数据库操作
        
        async def create_with_semaphore(school_data: SchoolCreate):
            async with semaphore:
                return await self.create_school(school_data)
        
        # 并发创建
        tasks = [create_with_semaphore(school_data) for school_data in schools_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"批量创建第 {i+1} 个学校时发生异常: {result}"
                logger.error(error_msg)
                processed_results.append(DatabaseOperationResult(
                    success=False,
                    affected_rows=0,
                    error_message=error_msg,
                    execution_time=0.0,
                ))
            else:
                processed_results.append(result)
        
        # 统计结果
        successful = sum(1 for r in processed_results if r.success)
        failed = len(processed_results) - successful
        
        logger.info(f"批量创建完成: 成功 {successful}/{len(schools_data)} 个学校")
        
        return processed_results
    
    @monitor_performance()
    @database_operation("upsert_school")
    async def upsert_school(self, school_data: SchoolCreate) -> DatabaseOperationResult:
        """插入或更新学校记录（如果已存在则更新）"""
        start_time = datetime.now()
        
        try:
            # 先尝试查找现有记录
            existing_school = await self.get_school_by_name(school_data.full_name)
            
            if existing_school:
                # 更新现有记录
                update_data = SchoolUpdate(**school_data.model_dump())
                result = await self.update_school(existing_school.id, update_data)
                
                if result.success:
                    logger.info(f"更新现有学校记录: {school_data.full_name}")
                
                return result
            else:
                # 创建新记录
                result = await self.create_school(school_data)
                
                if result.success:
                    logger.info(f"创建新学校记录: {school_data.full_name}")
                
                return result
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"学校插入或更新失败: {e}"
            self.error_logger.log_error("upsert_school", e, school_data.model_dump())
            
            return DatabaseOperationResult(
                success=False,
                affected_rows=0,
                error_message=error_msg,
                execution_time=execution_time,
            )
    
    @monitor_performance()
    async def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            total_schools = await self.count_schools()
            
            # 按类型统计
            public_schools = await self.count_schools({"institution_type": "公办"})
            private_schools = await self.count_schools({"institution_type": "民办"})
            
            # 按特殊类型统计
            demonstration_schools = await self.count_schools({"is_demonstration": True})
            backbone_schools = await self.count_schools({"is_backbone": True})
            excellent_schools = await self.count_schools({"is_excellent": True})
            chuyi_schools = await self.count_schools({"is_chuyi_high_level": True})
            
            return {
                "total_schools": total_schools,
                "by_type": {
                    "public": public_schools,
                    "private": private_schools,
                },
                "special_types": {
                    "demonstration": demonstration_schools,
                    "backbone": backbone_schools,
                    "excellent": excellent_schools,
                    "chuyi_high_level": chuyi_schools,
                },
                "updated_at": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
