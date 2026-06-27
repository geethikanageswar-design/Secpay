import logging
from sqlalchemy import text
from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def alter_tables():
    commands = [
        "ALTER TABLE users ADD COLUMN role ENUM('USER', 'ADMIN') NOT NULL DEFAULT 'USER';",
        "ALTER TABLE providers ADD COLUMN is_active BOOLEAN DEFAULT TRUE;",
        "CREATE INDEX ix_providers_is_active ON providers(is_active);",
        "ALTER TABLE bills MODIFY amount DECIMAL(10,2) NOT NULL;",
        "ALTER TABLE bills ADD INDEX ix_bills_status (status);", # Add index on status if not exists
        "ALTER TABLE payments MODIFY amount_paid DECIMAL(10,2) NOT NULL;",
        "ALTER TABLE payments ADD COLUMN payment_method VARCHAR(50);",
        "ALTER TABLE payments ADD COLUMN transaction_id VARCHAR(100);",
        "ALTER TABLE payments RENAME COLUMN payment_date TO paid_at;", # Assuming MySQL 8+ handles RENAME COLUMN
        "ALTER TABLE payments ADD UNIQUE INDEX ix_payments_transaction_id (transaction_id);"
    ]
    with engine.connect() as conn:
        for cmd in commands:
            try:
                conn.execute(text(cmd))
                conn.commit()
                logger.info(f"Successfully executed: {cmd}")
            except Exception as e:
                logger.error(f"Error executing {cmd}: {e}")

if __name__ == "__main__":
    alter_tables()
