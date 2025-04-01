from tkzs_bd_db_tool.models import Base
from sqlalchemy import Column, Integer, String, DateTime, Date,  DECIMAL,  func
from sqlalchemy.schema import UniqueConstraint


class JhCostTable(Base):
    __tablename__ = 'jh_cost'
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
    
    
