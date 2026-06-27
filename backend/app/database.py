import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Removed SQLite-specific logic (check_same_thread)
engine = create_engine(settings.database_url, pool_pre_ping=True)

# Temporary logging to confirm connection
try:
    with engine.connect() as conn:
        logger.info("Successfully connected to the MySQL database!")
except Exception as e:
    logger.error(f"Error connecting to MySQL: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        from app.models import core # Ensure models are loaded
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully in MySQL!")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
