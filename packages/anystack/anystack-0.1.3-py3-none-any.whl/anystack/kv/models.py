"""
SQLAlchemy ORM 模型定义
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class KVStore(Base):
    """KV存储的ORM模型"""
    
    __tablename__ = "kv_store"
    
    key = Column(String, primary_key=True, comment="键名")
    value = Column(JSONB, nullable=False, comment="JSON值")
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    
    def __repr__(self):
        return f"<KVStore(key='{self.key}', created_at='{self.created_at}')>"


def create_kv_table(table_name: str = "kv_store") -> type[KVStore]:
    """动态创建指定表名的KV模型"""
    
    # 检查表是否已经存在于元数据中
    if table_name in Base.metadata.tables:
        # 如果表已存在，返回一个引用现有表的类
        existing_table = Base.metadata.tables[table_name]
        
        class ExistingKVStore(Base):
            __table__ = existing_table
            
            def __repr__(self):
                return f"<{table_name.title()}(key='{self.key}', created_at='{self.created_at}')>"
        
        return ExistingKVStore
    else:
        # 如果表不存在，创建新的表定义
        class DynamicKVStore(Base):
            __tablename__ = table_name
            
            key = Column(String, primary_key=True, comment="键名")
            value = Column(JSONB, nullable=False, comment="JSON值")
            created_at = Column(
                DateTime(timezone=True), 
                nullable=False, 
                server_default=func.now(),
                comment="创建时间"
            )
            updated_at = Column(
                DateTime(timezone=True), 
                nullable=False, 
                server_default=func.now(),
                onupdate=func.now(),
                comment="更新时间"
            )
            
            def __repr__(self):
                return f"<{table_name.title()}(key='{self.key}', created_at='{self.created_at}')>"
        
        return DynamicKVStore
