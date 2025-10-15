
from sqlalchemy import Column, Integer, String, Text, DateTime, text, UniqueConstraint
from sqlalchemy.orm import declarative_base


Base = declarative_base()

class Content(Base):
    __tablename__ = 'content' # 数据库中的表名，你可以改成你希望的名字

    # id (int, primary_key=True, autoincrement=True)
    # 你的属性表中 id 为 int, true (not null), true (primary key), 0 (length), ASC (key order), true (auto increment)
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True, # 自动递增
        nullable=False,     # 不能为空
        comment="自增"
    )

    # prompt_id (varchar 255, not null, unique)
    # 你的属性表中 prompt_id 为 varchar, 255 (length), true (not null)
    embed_name_id = Column(
        String(255),        # VARCHAR 类型，长度 255
        nullable=False,     # 不能为空    # 必须是唯一的，这会创建唯一索引
        comment="Unique identifier for the prompt"
    )

    # version (varchar 50, not null)
    # 你的属性表中 version 为 varchar, 50 (length), true (not null)
    name = Column(
        String(255),         # VARCHAR 类型，长度 50
        nullable=False,     # 不能为空
        comment="Version of the prompt"
    )

    # version (varchar 50, not null)
    # 你的属性表中 version 为 varchar, 50 (length), true (not null)
    version = Column(
        String(50),         # VARCHAR 类型，长度 50
        nullable=False,     # 不能为空
        comment="版本"
    )
    timestamp = Column(
        DateTime,
        nullable=False,      # 不能为空
        server_default=text('CURRENT_TIMESTAMP'),
        onupdate=text('CURRENT_TIMESTAMP'),
        comment="时间戳"
    )
    content = Column(
        Text,               # TEXT 类型，适用于长文本
        nullable=False,     # 不能为空
        comment="内容"
    )
    type = Column(
        Integer,
        nullable=True,      # 可以为空 (因为你的表格中 Not Null 为 false)
        comment="类型"      # 列注释
    )

    # 定义 __repr__ 方法以便打印对象时有清晰的表示
    def __repr__(self):
        return (f"<Prompt(id={self.id}, prompt_id='{self.prompt_id}', "
                f"version='{self.version}', timestamp='{self.timestamp}', "
                f"prompt='{self.prompt[:50]}...', use_case='{self.use_case}')>")


class Prompt(Base):
    __tablename__ = 'prompts_table' # 数据库中的表名，你可以改成你希望的名字
    # __tablename__ = 'llm_prompt' # 数据库中的表名，你可以改成你希望的名字

    # 定义联合唯一约束
    # 这是一个元组，包含你希望应用于表的额外定义，例如索引或约束
    __table_args__ = (
        UniqueConstraint('prompt_id', 'version', name='_prompt_id_version_uc'),
        # 'name' 参数是可选的，用于给数据库中的约束指定一个名称，方便管理和调试
    )

    # id (int, primary_key=True, autoincrement=True)
    # 你的属性表中 id 为 int, true (not null), true (primary key), 0 (length), ASC (key order), true (auto increment)
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True, # 自动递增
        nullable=False,     # 不能为空
        comment="Primary key ID"
    )

    # prompt_id (varchar 255, not null, unique)
    # 你的属性表中 prompt_id 为 varchar, 255 (length), true (not null)
    prompt_id = Column(
        String(255),        # VARCHAR 类型，长度 255
        nullable=False,     # 不能为空    # 必须是唯一的，这会创建唯一索引
        comment="Unique identifier for the prompt"
    )

    # version (varchar 50, not null)
    # 你的属性表中 version 为 varchar, 50 (length), true (not null)
    version = Column(
        String(50),         # VARCHAR 类型，长度 50
        nullable=False,     # 不能为空
        comment="Version of the prompt"
    )

    # timestamp (datetime, not null, default current_timestamp, on update current_timestamp)
    # 你的属性表中 timestamp 为 datetime, true (not null), false (default value), true (generated always on update current_timestamp)
    timestamp = Column(
        DateTime,
        nullable=False,      # 不能为空
        # MySQL 的 DEFAULT CURRENT_TIMESTAMP
        server_default=text('CURRENT_TIMESTAMP'),
        # MySQL 的 ON UPDATE CURRENT_TIMESTAMP
        onupdate=text('CURRENT_TIMESTAMP'),
        comment="Timestamp of creation or last update"
    )

    # prompt (text, not null)
    # 你的属性表中 prompt 为 text, true (not null)
    prompt = Column(
        Text,               # TEXT 类型，适用于长文本
        nullable=False,     # 不能为空
        comment="The actual prompt text content"
    )

    # use_case (text, nullable)
    # 你的属性表中 use_case 为 text, false (not null, 即 nullable=True), NULL (default value), '用例' (comment)
    use_case = Column(
        Text,
        nullable=True,      # 可以为空 (因为你的表格中 Not Null 为 false)
        comment="用例"      # 列注释
    )

    # 执行类型
    action_type = Column(
        String(255),        # VARCHAR 类型，长度 255
        nullable=False,     # 不能为空    # 必须是唯一的，这会创建唯一索引
        comment="type train inference summary"
    )

    demand = Column(
        Text,
        nullable=True,      # 可以为空 (因为你的表格中 Not Null 为 false)
        comment="提示词改动需求"      # 列注释
    )


    # 定义 __repr__ 方法以便打印对象时有清晰的表示
    def __repr__(self):
        return (f"<Prompt(id={self.id}, prompt_id='{self.prompt_id}', "
                f"version='{self.version}', timestamp='{self.timestamp}', "
                f"prompt='{self.prompt[:50]}...', use_case='{self.use_case}')>"
                f"action_type='{self.action_type}...', demand='{self.demand[:30]}')>"
                )


class UseCase(Base):
    __tablename__ = 'usecase' # 数据库中的表名，你可以改成你希望的名字

    # id (int, primary_key=True, autoincrement=True)
    # 你的属性表中 id 为 int, true (not null), true (primary key), 0 (length), ASC (key order), true (auto increment)
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True, # 自动递增
        nullable=False,     # 不能为空
        comment="Primary key ID"
    )

    # prompt_id (varchar 255, not null, unique)
    # 你的属性表中 prompt_id 为 varchar, 255 (length), true (not null)
    prompt_id = Column(
        String(255),        # VARCHAR 类型，长度 255
        nullable=False,     # 不能为空    # 必须是唯一的，这会创建唯一索引
        comment="Unique identifier for the prompt"
    )


    # prompt (text, not null)
    # 你的属性表中 prompt 为 text, true (not null)
    use_case = Column(
        Text,               # TEXT 类型，适用于长文本
        nullable=False,     # 不能为空
        comment="用例"
    )

    output = Column(
        Text,               # TEXT 类型，适用于长文本
        nullable=False,     # 不能为空
        comment="AI输出"
    )

    # use_case (text, nullable)
    # 你的属性表中 use_case 为 text, false (not null, 即 nullable=True), NULL (default value), '用例' (comment)
    solution = Column(
        Text,
        nullable=True,      # 可以为空 (因为你的表格中 Not Null 为 false)
        comment="理想结果"      # 列注释
    )

    # 定义 __repr__ 方法以便打印对象时有清晰的表示
    def __repr__(self):
        return (f"<Prompt(id={self.id}, prompt_id='{self.prompt_id}', "
                f"use_case='{self.use_case[:50]}...', solution='{self.solution}')>")


