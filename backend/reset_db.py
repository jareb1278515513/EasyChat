from app import create_app, db

def reset_database():
    """
    Drops and recreates the database tables from scratch based on the current models.
    """
    app = create_app()
    with app.app_context():
        print("Dropping all database tables...")
        db.drop_all()
        print("Creating all database tables...")
        db.create_all()
        print("Database has been reset successfully.")

if __name__ == '__main__':
    reset_database() 