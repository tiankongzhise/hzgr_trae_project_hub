from tkzs_bd_db_tool.models import Base
from sqlalchemy import Column, Integer, String, DateTime, Date,  DECIMAL,  func , Text
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime



class JhCostTable(Base):
    __tablename__ = 'jh_cost1'
    __table_args__ = (
        UniqueConstraint('date', 'channel', name='uq_date_channel'),
        {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_0900_ai_ci',
        'mysql_row_format': 'DYNAMIC',
        'schema': 'jh_data'
    })
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    date = Column(Date,  comment='消费日期')
    cost = Column(DECIMAL(10,2), comment='消费金额')
    click = Column(Integer,nullable=True, comment='点击量')
    impression = Column(Integer,nullable=True, comment='展现量')
    consult = Column(Integer,nullable=True, comment='对话')
    channel = Column(String(255), comment='投放渠道')
    created_at = Column(DateTime,default=func.now(),comment='记录创建时间')
    updated_at = Column(DateTime,onupdate=func.now(),comment='记录更新时间')
    

class JhCostNewTable(Base):
    __tablename__ = 'jh_cost_new'
    __table_args__ = (
        UniqueConstraint('date', 'channel','sub_channel','school', name='uq_date_channel_sub_channel_school'),
        {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_0900_ai_ci',
        'mysql_row_format': 'DYNAMIC',
        'schema': 'jh_data'
    })
    key_id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    date = Column(Date,  comment='消费日期')
    cost = Column(DECIMAL(10,2), comment='消费金额')
    school = Column(String(255), comment='校区')
    channel = Column(String(255), comment='投放渠道')
    sub_channel = Column(String(255), comment='投放子渠道')
    created_at = Column(DateTime,default=func.now(),comment='记录创建时间')
    updated_at = Column(DateTime,onupdate=func.now(),comment='记录更新时间')
    
    def get(self, key, default=None):
        return getattr(self, key, default)

class CardTable(Base):
    __tablename__ = 'card'
    __table_args__ = (
        UniqueConstraint('customer_id', name='uq_customer_id'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_0900_ai_ci',
            'mysql_row_format': 'DYNAMIC',
            'schema': 'jh_data'
        })
    
    key_id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    customer_id = Column(String(32), nullable=False, comment='客户ID')
    name = Column(String(50), comment='姓名')
    source = Column(String(100), comment='来源名称')
    feedback_status = Column(String(20), comment='反馈状态')
    project = Column(String(100), comment='项目')
    create_time = Column(DateTime, comment='创建时间')
    remark = Column(Text, comment='备注')
    campus = Column(String(50), comment='咨询校区')
    age = Column(Integer, comment='年龄')
    status = Column(String(20), comment='状态')
    province = Column(String(50), comment='省份')
    region = Column(String(50), comment='地域')
    education = Column(String(20), comment='学历类型')
    first_assignee = Column(String(50), comment='首次分配归属人')
    creator = Column(String(50), comment='创量人')
    create_at = Column(DateTime, default=func.now(), comment='创建时间')
    update_at = Column(DateTime, onupdate=func.now(), comment='更新时间')

    def __init__(self, data_dict):
        # 字段映射配置 (中文字段名: (属性名, 类型))
        field_mapping = {
            '客户ID': ('customer_id', 'str'),
            '姓名': ('name', 'str'),
            '来源名称': ('source', 'str'),
            '反馈状态': ('feedback_status', 'str'),
            '项目': ('project', 'str'),
            '创建时间': ('create_time', 'datetime'),
            '备注': ('remark', 'str'),
            '咨询校区': ('campus', 'str'),
            '年龄': ('age', 'int'),
            '状态': ('status', 'str'),
            '省份': ('province', 'str'),
            '地域': ('region', 'str'),
            '学历类型': ('education', 'str'),
            '首次分配归属人': ('first_assignee', 'str'),
            '创量人': ('creator', 'str')
        }

        for chinese_field, (attr_name, field_type) in field_mapping.items():
            raw_value = data_dict.get(chinese_field)
            
            # 处理 null 值
            value = None if isinstance(raw_value, str) and raw_value.lower() == 'null' else raw_value
            
            # 类型转换
            if value is not None:
                try:
                    if field_type == 'int':
                        value = int(value) if str(value).strip().isdigit() else None
                    elif field_type == 'datetime':
                        value = self._parse_datetime(value)
                    elif field_type == 'str':
                        value = str(value).strip() if value else ''
                except (ValueError, TypeError, AttributeError):
                    value = None
            
            setattr(self, attr_name, value)

    def _parse_datetime(self, time_str):
        """统一处理时间格式转换"""
        if not time_str:
            return None
        try:
            # 处理可能的格式: "2023-10-2316:09:47" 或 "2023-10-23 16:09:47"
            time_str = str(time_str).replace(' ', '')
            return datetime.strptime(time_str, '%Y-%m-%d%H:%M:%S')
        except ValueError:
            return None

    def __repr__(self):
        return f"<CardTable(name='{self.name}', customer_id='{self.customer_id}')>"


class VisitTable(Base):
    __tablename__ = 'visit'
    __table_args__ = (
        UniqueConstraint('customer_id','visit_time', name='uq_customer_id_visit_time'),
        {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_0900_ai_ci',
        'mysql_row_format': 'DYNAMIC',
        'schema': 'jh_data'
    })
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    customer_id = Column(String(32), nullable=False, comment='客户ID')
    source = Column(String(100), comment='客户来源')
    card_create_time = Column(DateTime, comment='名片创建时间')
    name = Column(String(50), comment='姓名')
    age = Column(Integer,nullable=True, comment='年龄')
    assignee = Column(String(50), comment='归属人')
    province = Column(String(50),nullable=True, comment='省份')
    city = Column(String(50),nullable=True, comment='城市')
    project = Column(String(100), comment='预约项目')
    campus = Column(String(50), comment='预约分校')
    visit_time = Column(DateTime, comment='预约时间')
    remark = Column(Text, comment='备注')
    consult_campus = Column(String(50), comment='咨询校区')
    education = Column(String(20),nullable=True, comment='学历类型')
    create_at = Column(DateTime, default=func.now(),comment='创建时间')
    update_at = Column(DateTime, onupdate=func.now(),comment='更新时间')

    def __init__(self, data_dict):
        # 字段映射关系
        field_mapping = {
            '客户ID': ('customer_id', None),
            '客户来源': ('source', None),
            '名片创建时间': ('card_create_time', 'datetime'),
            '姓名': ('name', None),
            '年龄': ('age', 'int'),
            '归属': ('assignee', None),
            '省份': ('province', None),
            '城市': ('city', None),
            '预约项目': ('project', None),
            '预约分校': ('campus', None),
            '预约时间': ('visit_time', 'datetime'),
            '备注': ('remark', None),
            '咨询校区': ('consult_campus', None),
            '学历类型': ('education', None)
        }

        for chinese_field, (attr_name, field_type) in field_mapping.items():
            raw_value = data_dict.get(chinese_field)
            
            # 处理 null 值
            value = None if isinstance(raw_value, str) and raw_value.lower() == 'null' else raw_value
            
            # 按字段类型处理
            if value is not None:
                if field_type == 'int':
                    value = int(value) if str(value).isdigit() else None
                elif field_type == 'datetime':
                    value = self._parse_datetime(value)
            
            setattr(self, attr_name, value)

    def _parse_datetime(self, time_str):
        """统一处理时间格式转换"""
        if not time_str:
            return None
        try:
            # 处理可能的格式: "2023-10-2316:09:47" 或 "2023-10-23 16:09:47"
            time_str = str(time_str).replace(' ', '')
            return datetime.strptime(time_str, '%Y-%m-%d%H:%M:%S')
        except ValueError as e:
            print(f"时间格式解析错误: {time_str}, 错误: {str(e)}")
            return None

    def __repr__(self):
        return f"<CampusVisitRecord(name='{self.name}', customer_id='{self.customer_id}', visit_time='{self.visit_time}')>"


class SignUpTable(Base):
    __tablename__ = 'sign_up'
    __table_args__ = (
        UniqueConstraint('customer_id','enrollment_time', name='uq_customer_id_enrollment_time'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_0900_ai_ci',
            'mysql_row_format': 'DYNAMIC',
            'schema': 'jh_data'
        })
    
    key_id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    customer_id = Column(String(32), nullable=False, comment='客户ID')
    source = Column(String(100), comment='客户来源')
    name = Column(String(50), comment='姓名')
    province = Column(String(50), nullable=True, comment='省份')
    region = Column(String(50), nullable=True, comment='地域')
    enrolled_course = Column(String(100), comment='最近报名商品')
    enrollment_time = Column(DateTime, comment='最近报名时间')
    consult_project = Column(String(100), comment='咨询项目')
    remark = Column(Text, nullable=True, comment='备注')
    age = Column(Integer, nullable=True, comment='年龄')
    card_create_date = Column(DateTime, comment='名片创建日期')
    consult_campus = Column(String(50), comment='咨询校区')
    enrolled_campus = Column(String(50), comment='报名校区')
    assignee = Column(String(50), comment='归属人')
    create_at = Column(DateTime, default=func.now(), comment='创建日期')
    update_at = Column(DateTime, onupdate=func.now(), comment='更新日期')

    def __init__(self, data_dict):
        # 字段映射配置 (中文字段名: (属性名, 类型, 是否必填))
        field_mapping = {
            '客户ID': ('customer_id', 'str', True),
            '来源': ('source', 'str', False),
            '姓名': ('name', 'str', False),
            '省份': ('province', 'str', False),
            '地域': ('region', 'str', False),
            '最近报名商品': ('enrolled_course', 'str', False),
            '最近报名时间': ('enrollment_time', 'datetime', False),
            '咨询项目': ('consult_project', 'str', False),
            '备注': ('remark', 'str', False),
            '年龄': ('age', 'int', False),
            '名片创建日期': ('card_create_date', 'datetime', False),
            '咨询校区': ('consult_campus', 'str', False),
            '报名校区': ('enrolled_campus', 'str', False),
            '归属人': ('assignee', 'str', False)
        }

        for chinese_field, (attr_name, field_type, required) in field_mapping.items():
            raw_value = data_dict.get(chinese_field)
            
            # 处理 null 值
            value = None if isinstance(raw_value, str) and raw_value.lower() == 'null' else raw_value
            
            # 必填字段检查
            if required and value is None:
                raise ValueError(f"必填字段缺失: {chinese_field}")
            
            # 类型转换
            if value is not None:
                try:
                    if field_type == 'int':
                        value = int(value) if str(value).strip().isdigit() else None
                    elif field_type == 'datetime':
                        value = self._parse_datetime(value)
                    elif field_type == 'str':
                        value = str(value).strip() if value else ''
                except (ValueError, TypeError, AttributeError) as e:
                    print(f"字段[{chinese_field}]转换错误: {str(e)}")
                    value = None
            
            setattr(self, attr_name, value)

    def _parse_datetime(self, time_str):
        """统一处理时间格式转换"""
        if not time_str:
            return None
        try:
            # 处理可能的格式: "2023-10-2316:09:47" 或 "2023-10-23 16:09:47"
            time_str = str(time_str).replace(' ', '')
            return datetime.strptime(time_str, '%Y-%m-%d%H:%M:%S')
        except ValueError as e:
            print(f"时间格式解析错误: {time_str}, 错误: {str(e)}")
            return None

    def __repr__(self):
        return (f"<SignUpTable(name='{self.name}', "
                f"course='{self.enrolled_course}', "
                f"time='{self.enrollment_time}')>")
