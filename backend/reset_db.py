from app import create_app, db


def reset_database():
    """
    删除并根据当前模型重新创建所有数据库表。
    """
    app = create_app()
    with app.app_context():
        print("Dropping all database tables...")  # 正在删除所有数据库表
        db.drop_all()
        print("Creating all database tables...")  # 正在创建所有数据库表
        db.create_all()
        print("Database has been reset successfully.")  # 数据库重置成功

if __name__ == '__main__':
    reset_database() 