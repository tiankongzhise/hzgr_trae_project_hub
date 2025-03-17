from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, JSON, DECIMAL, INTEGER, func, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import UniqueConstraint

Base = declarative_base()

class BdAuthTokenTable(Base):
    __tablename__ = 'bd_auth_token_new'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_0900_ai_ci',
        'mysql_row_format': 'DYNAMIC',
        'schema': 'baidudb'
    }

    # key = Column(
    #     Integer().with_variant(Integer(unsigned=True), "mysql"),
    #     primary_key=True,
    #     autoincrement=True,
    #     comment='自增主键'
    # )
    key = Column(
        Integer,  # 修正这里
        primary_key=True,
        autoincrement=True,
        comment='自增主键'
    )
    userId = Column(
        String(32),
        default='',
        server_default='',
        unique=True,
        comment='用户ID'
    )
    openId = Column(
        String(32),
        default='',
        server_default='',
        unique=True,
        comment='授权用户查询标识'
    )
    refreshToken = Column(
        Text,
        nullable=True,
        comment='刷新令牌'
    )
    accessToken = Column(
        Text,
        nullable=True,
        comment='访问令牌'
    )
    expiresTime = Column(
        DateTime,
        nullable=True,
        comment='访问令牌过期时间'
    )
    refreshExpiresTime = Column(
        DateTime,
        nullable=True,
        comment='刷新令牌过期时间'
    )
    tableUpdateTime = Column(
        DateTime,
        default=func.now(), 
        onupdate=func.now(),
        comment='记录更新时间'
    )
class BdAdMaterialTransferTable(Base):
    __tablename__ = 'ads_material_transfer'  # 表名
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    material_class = Column(String(64), nullable=False, comment='物料类型')
    source_user_id = Column(String(64), nullable=False, comment='来源用户ID')
    material_id = Column(String(64), nullable=True, comment='物料ID')
    material_url = Column(String(512), nullable=True, comment='物料URL')
    material_name = Column(String(256), nullable=True, comment='物料名称')
    description = Column(JSON, nullable=True, comment='描述')
    target_user_id = Column(String(64), nullable=False, comment='目标用户ID')
    target_material_id = Column(String(64), nullable=True, comment='目标物料ID')
    target_material_url = Column(String(512), nullable=True, comment='目标物料URL')
    target_material_name = Column(String(256), nullable=True, comment='目标物料名称')
    target_description = Column(JSON, nullable=True, comment='目标描述')
    migrate_status = Column(String(64), nullable=False, comment='迁移状态')
    migrate_time = Column(DateTime, default=datetime.now, comment='迁移时间')
    tableUpdateTime = Column(DateTime,default=func.now(), onupdate=func.now(),comment='记录更新时间')
    
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_0900_ai_ci',
        'mysql_row_format': 'DYNAMIC',
        'schema': 'baidu_ads_operation'
    }
    
    
    def __repr__(self):
        # 获取所有类属性（过滤掉特殊方法）
        class_attrs = [
            f"{attr}={value!r}" 
            for attr, value in self.__class__.__dict__.items() 
            if not attr.startswith('__') and not callable(value)
        ]
        return f"<{self.__class__.__name__}({', '.join(class_attrs)})>"

class BdAdCenterBindTable(Base):
    __tablename__ = 'ads_center_bind'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    center_id = Column(String(64), nullable=False, comment='中心ID')
    center_name = Column(String(64), nullable=False, comment='中心名称')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    user_name = Column(String(64), nullable=False, comment='用户名')
    tableUpdateTime = Column(DateTime,default=func.now(), onupdate=func.now(),comment='记录更新时间')
    __table_args__ = (
        UniqueConstraint('center_id', 'user_id', name='uq_center_id_user_id'),
        {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_0900_ai_ci',
        'mysql_row_format': 'DYNAMIC',
        'schema': 'baidu_ads_operation'
        
    })
    
class LeadsNoticePush(Base):
    """百度推送线索数据模型"""
    __tablename__ = 'leadsnotice_push'
    __table_args__ = {'schema': 'baidu_source_data'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Integer,nullable=True,comment='有效性标注')
    ucid = Column(Integer, comment='ucid数值')
    clueId = Column(String(255), comment='clueId字符串')
    commitTime = Column(DateTime, default=datetime.now, comment='commitTime时间时分秒')
    solutionTypeName = Column(String(255), comment='solutionTypeName字符串')
    cluePhoneNumber = Column(String(75), comment='cluePhoneNumber字符串')
    flowChannelName = Column(String(255), comment='flowChannelName字符串')
    formDetail = Column(JSON, comment='formDetail是JsonArray')
    imName = Column(String(255), comment='imName字符串')
    clueUserMsgCount = Column(Integer, comment='clueUserMsgCount数值')
    humanServiceMsgCount = Column(Integer, comment='humanServiceMsgCount数值')
    aiServiceMessageNum = Column(Integer, comment='aiServiceMessageNum数值')
    ip = Column(String(50), comment='ip字符串')
    wechatAccount = Column(String(255), comment='wechatAccount字符串')
    url = Column(Text, comment='url字符串')
    consultUrl = Column(Text, comment='consultUrl字符串')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        return {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
        }
    def __repr__(self):
        return f"<LeadsNoticePush(id={self.ucid}, clueId={self.clueId})>"

class BaiduAccoutCostRrport(Base):
    """百度账户日消费数据"""
    __tablename__ = 'baidu_accout_cost_report'
    __table_args__ = (
        UniqueConstraint('date', 'userId', name='uq_date_user_id'),
        {'schema': 'baidu_source_data'})
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=datetime.now, comment='日期时间')
    userName = Column(String(255), comment='用户名')
    userId = Column(Integer, comment='用户id')
    product = Column(String(255), comment='投放渠道')
    impression = Column(Integer, comment='展现量')
    click = Column(Integer, comment='点击量')
    cost = Column(DECIMAL(8,2), comment='消费金额')
    created_at = Column(DateTime,default=func.now(),comment='记录创建时间')
    updated_at = Column(DateTime,onupdate=func.now(),comment='记录更新时间')
    
    def to_dict(self):
        return {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
        }
    def __repr__(self):
        return f"<BaiduAccoutCostRrport(userId={self.userId}, userName={self.userName},date={self.date},cost = {self.cost},created_at={self.created_at})>"
    

