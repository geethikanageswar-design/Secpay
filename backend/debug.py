from app.schemas.schemas import UserCreate
from app.utils.security import get_password_hash
from app.database import SessionLocal
from app.services.crud import create_user

def test():
    try:
        user_data = UserCreate(name="test", email="test@g.com", password="pwd")
        print("Pydantic validation passed.")
        
        hash = get_password_hash("pwd")
        print("Hash:", hash)
        
        db = SessionLocal()
        print("DB Session created.")
        
        user = create_user(db, user_data)
        print("User created successfully with ID:", user.id)
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
