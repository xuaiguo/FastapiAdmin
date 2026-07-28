from sqlalchemy import create_engine, Column, Integer, String, Identity
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import cx_Oracle
cx_Oracle.init_oracle_client(lib_dir=r"C:\obclient\lib")

# 使用 ?service_name 明确指定服务名  conn = cx_Oracle.connect('XAG/Xag_123456@obot7jbnen7v964g-mi.aliyun-cn-hangzhou-internet.oceanbase.cloud:1521/XAG')
DATABASE_URL = "oracle+cx_oracle://XAG:Xag_123456@obot7jbnen7v964g-mi.aliyun-cn-hangzhou-internet.oceanbase.cloud:1521/?service_name=XAG"

engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, Identity(start=3), primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"


#drop TABLE users;

#CREATE TABLE users (
#	id number generated always as identity,
#	name VARCHAR2(50) NOT NULL,
#	email VARCHAR2(100) NOT NULL,
#	PRIMARY KEY (id),
#	UNIQUE (email)
#)

# 删除旧表（可选，如果表已存在且不需要保留数据）
# Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# 5. CRUD 操作示例
def create_user(session,name: str, email: str):
    """插入新用户"""
    try:
        user = User(name=name, email=email)
        session.add(user)
        session.commit()
        print(f"创建用户成功: {user}")
        return user
    except SQLAlchemyError as e:
        session.rollback()
        print(f"创建用户失败: {e}")
        return None

def get_user(session, user_id: int):
    """根据ID查询用户"""
    return session.query(User).filter(User.id == user_id).first()

def get_user_by_email(session, email: str):
    """根据邮箱查询用户"""
    return session.query(User).filter(User.email == email).first()

def get_all_users(session):
    """查询所有用户"""
    return session.query(User).all()

def update_user_email(session, user_id: int, new_email: str):
    """更新用户邮箱"""
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.email = new_email
            session.commit()
            print(f"更新用户成功: {user}")
            return True
        else:
            print(f"未找到ID为 {user_id} 的用户")
            return False
    except SQLAlchemyError as e:
        session.rollback()
        print(f"更新用户失败: {e}")
        return False

def delete_user(session, user_id: int):
    """删除用户"""
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            session.delete(user)
            session.commit()
            print(f"删除用户成功: {user}")
            return True
        else:
            print(f"未找到ID为 {user_id} 的用户")
            return False
    except SQLAlchemyError as e:
        session.rollback()
        print(f"删除用户失败: {e}")
        return False

# 6. 使用示例
if __name__ == "__main__":
    # 创建一个会话
    db = SessionLocal()

    try:
        # 插入数据
        user1 = create_user(db, "张三", "zhangsan@example.com")
        user2 = create_user(db, "李四", "lisi@example.com")

        # 查询所有用户
        print("\n所有用户:")
        for u in get_all_users(db):
            print(u)

        # 按ID查询
        print("\n查询ID=1的用户:")
        print(get_user(db, 1))

        # 更新邮箱
        print("\n更新用户1的邮箱:")
        update_user_email(db, 1, "new_zhangsan@example.com")

        # 再次查询
        print("\n更新后的用户1:")
        print(get_user(db, 1))

        # 删除用户
        print("\n删除用户2:")
        delete_user(db, 2)

        # 最终所有用户
        print("\n剩余用户:")
        for u in get_all_users(db):
            print(u)

    finally:
        # 关闭会话
        db.close()