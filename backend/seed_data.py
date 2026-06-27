import logging
from datetime import datetime, timedelta, timezone
import random
from app.database import SessionLocal
from app.models.core import User, UserRole, Provider, Bill, BillStatus
from app.utils.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    db = SessionLocal()
    try:
        # 1. Ensure we have an ADMIN user
        admin_email = "admin@secpay.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                name="System Admin", 
                email=admin_email, 
                password_hash=get_password_hash("admin123"), 
                role=UserRole.ADMIN
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            logger.info(f"Created Admin user: {admin_email} (ID: {admin.id})")
        else:
            logger.info("Admin user already exists.")

        # 2. Ensure we have the requested Providers
        provider_names = ["TSSPDCL Electricity", "Water Bill", "Internet Bill", "Previous Electricity"]
        providers = []
        for p_name in provider_names:
            provider = db.query(Provider).filter(Provider.name == p_name).first()
            if not provider:
                provider = Provider(name=p_name, service_type="Utility", is_active=True)
                db.add(provider)
                db.commit()
                db.refresh(provider)
                logger.info(f"Created Provider: {provider.name} (ID: {provider.id})")
            else:
                logger.info(f"Provider '{p_name}' already exists.")
            providers.append(provider)

        # 3. Get ALL normal users
        users = db.query(User).filter(User.role == UserRole.USER).all()
        if not users:
            logger.warning("No regular users found in the database. Please register a user on the frontend first!")
            return
            
        now = datetime.now(timezone.utc)

        # 4. Create bills for every user
        bills_to_create = []
        for user in users:
            logger.info(f"Assigning 7 dummy bills to User: {user.email} (ID: {user.id})")
            
            for i in range(7):
                provider = random.choice(providers)
                amount = round(random.uniform(20.0, 1500.0), 2)
                # Spread due dates across past 45 days and future 30 days
                days_offset = random.randint(-45, 30)
                
                bills_to_create.append(
                    Bill(
                        user_id=user.id, 
                        provider_id=provider.id, 
                        amount=amount, 
                        due_date=now + timedelta(days=days_offset), 
                        status=BillStatus.PENDING
                    )
                )
        
        db.add_all(bills_to_create)
        db.commit()
        logger.info(f"Successfully added {len(bills_to_create)} dummy bills across {len(users)} users!")

    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
