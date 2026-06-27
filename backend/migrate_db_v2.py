import logging
from sqlalchemy import text
from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def alter_tables():
    commands = [
        # Since MySQL ENUMs are strict, we need to redeclare the entire ENUM string
        "ALTER TABLE payments MODIFY COLUMN status ENUM('SUCCESS', 'FAILED', 'PENDING', 'REFUNDED') NOT NULL DEFAULT 'PENDING';",
        # Add new column fraud_flag
        "ALTER TABLE payments ADD COLUMN fraud_flag BOOLEAN DEFAULT FALSE;",
        # Add indexes requested
        "CREATE INDEX ix_payments_status ON payments(status);",
        "CREATE INDEX ix_payments_fraud_flag ON payments(fraud_flag);",
        "CREATE INDEX ix_payments_paid_at ON payments(paid_at);"
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
