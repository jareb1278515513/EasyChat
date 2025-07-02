from app import create_app, db
from app.models import User


def reset_database():
    """
    删除并根据当前模型重新创建所有数据库表，并创建一个默认管理员账户。
    """
    app = create_app()
    with app.app_context():
        print("Dropping all database tables...")  # 正在删除所有数据库表
        db.drop_all()
        print("Creating all database tables...")  # 正在创建所有数据库表
        db.create_all()

        # 创建管理员账户
        print("Creating admin account...")
        admin_user = User(
            username='admin',
            email='admin@gmail.com',
            is_admin=True
        )
        admin_user.set_password('liujialun')
        db.session.add(admin_user)
        db.session.commit()

        print("Database has been reset and admin account created successfully.")  # 数据库重置成功

if __name__ == '__main__':
    reset_database() 