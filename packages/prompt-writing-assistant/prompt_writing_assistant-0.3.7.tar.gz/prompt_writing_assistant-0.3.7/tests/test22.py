from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine # 异步核心
import asyncio

# 假设你的模型定义
Base = declarative_base()

class Action(Base):
    __tablename__ = 'actions'
    id = Column(Integer, primary_key=True)
    action_type = Column(String) # train, inference, processed
    source_action_id = Column(Integer, nullable=True) # 如果 inference 记录关联到特定的 train 记录

    # 为唯一索引方法准备
    __table_args__ = (
        UniqueConstraint('source_action_id', 'action_type', name='_source_action_id_action_type_uc'),
    )

    def __repr__(self):
        return f"<Action(id={self.id}, action_type='{self.action_type}', source_action_id={self.source_action_id})>"

# 异步数据库引擎
# 使用 aiomysql 驱动
DATABASE_URL = "mysql+pymysql://zxf_root:Zhf4233613%40@rm-2ze0793c6548pxs028o.mysql.rds.aliyuncs.com:3306/serverz"


async_engine = create_async_engine(DATABASE_URL, echo=True)


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 异步 Session 工厂
AsyncSessionLocal = sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)


# --- 解决方案 1: 悲观锁 (SELECT FOR UPDATE) ---
async def process_action_with_pessimistic_lock(action_id: int):
    async with AsyncSessionLocal() as session:
        try:
            # 1. 开始异步事务并使用 with_for_update() 获取悲观锁
            # 这会阻塞其他尝试获取相同行锁的事务
            stmt = select(Action).filter_by(id=action_id).with_for_update()
            result = await session.execute(stmt)
            action = result.scalars().first()

            if action:
                print(f"[{action_id}] Current action_type: {action.action_type}")
                if action.action_type == 'train':
                    # 确保没有其他 inference 针对此 train
                    # 实际上 with_for_update 已经保证了，但也可以多一次检查
                    existing_inference = await session.execute(
                        select(Action).filter_by(action_type='inference', source_action_id=action.id)
                    )
                    if not existing_inference.scalars().first():
                        # 插入新的 inference 记录
                        new_inference_action = Action(action_type='inference', source_action_id=action.id)
                        session.add(new_inference_action)
                        # 如果需要，可以将原始 'train' 记录标记为已处理
                        action.action_type = 'processed' # 或其他状态
                        await session.commit()
                        print(f"[{action_id}] Transaction committed. Inference inserted and train marked as processed.")
                    else:
                        print(f"[{action_id}] Inference already exists for this train, skipping.")
                else:
                    print(f"[{action_id}] Not 'train' (or already processed), skipping insertion.")
            else:
                print(f"[{action_id}] Action with ID {action_id} not found.")

        except Exception as e:
            await session.rollback()
            print(f"[{action_id}] Error: {e}, transaction rolled back.")

# --- 解决方案 2: 唯一索引 (通过捕获 IntegrityError) ---
async def process_action_with_unique_constraint(train_action_id: int):
    async with AsyncSessionLocal() as session:
        try:
            # 1. 检查原始 action_type
            stmt = select(Action).filter_by(id=train_action_id)
            result = await session.execute(stmt)
            train_action = result.scalars().first()

            if train_action and train_action.action_type == 'train':
                # 2. 尝试插入 inference 记录，并关联 source_action_id
                new_inference_action = Action(action_type='inference', source_action_id=train_action_id)
                session.add(new_inference_action)
                
                # 如果需要，将原始 'train' 记录标记为已处理
                train_action.action_type = 'processed' 

                await session.commit()
                print(f"[{train_action_id}] Successfully inserted inference record for train action {train_action_id}.")
            else:
                print(f"[{train_action_id}] Not a 'train' action or not found, skipping insertion.")

        except Exception as e:
            await session.rollback()
            # 捕获唯一约束错误 (SQLAlchemy 可能会包装成 IntegrityError)
            from sqlalchemy.exc import IntegrityError
            if isinstance(e, IntegrityError) and "Duplicate entry" in str(e): # MySQL 错误信息可能不同
                print(f"[{train_action_id}] Inference for train action {train_action_id} already exists (unique constraint violation).")
            else:
                print(f"[{train_action_id}] Error: {e}, transaction rolled back.")

# --- 主执行函数 ---
async def main():
    await init_db()

    # 清空并添加初始数据
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Action)) # 清空
        session.add(Action(action_type='train'))
        session.add(Action(action_type='train'))
        session.add(Action(action_type='train'))
        await session.commit()

    async with AsyncSessionLocal() as session:
        stmt = select(Action).filter_by(action_type='train')
        result = await session.execute(stmt)
        train_actions = result.scalars().all()
        action_ids_to_process = [action.id for action in train_actions]
    
    print(f"Processing action IDs: {action_ids_to_process}")

    # 模拟并发执行
    tasks = [process_action_with_pessimistic_lock(action_id) for action_id in action_ids_to_process]
    # tasks = [process_action_with_unique_constraint(action_id) for action_id in action_ids_to_process]
    
    await asyncio.gather(*tasks)

    # 验证结果
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Action))
        all_actions = result.scalars().all()
        print("\nFinal state of actions:")
        for action in all_actions:
            print(action)


if __name__ == "__main__":
    from sqlalchemy import select, delete # 导入 select, delete 用于异步操作
    asyncio.run(main())