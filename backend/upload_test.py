from app.database.connection import engine
from app.coordinator import ImportCoordinator
from app.database.models import Business, Base
from sqlalchemy.orm import Session
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Make sure business 1 exists
Base.metadata.create_all(engine)
with Session(engine) as session:
    b = session.query(Business).filter_by(id=1).first()
    if not b:
        b = Business(name="Test Business", id=1)
        session.add(b)
        session.commit()

coordinator = ImportCoordinator(engine)
with open("test_import2.zip", "rb") as f:
    zip_bytes = f.read()

# We need to use test_import7.zip to avoid deduplication
with open("test_import7.zip", "rb") as f:
    zip_bytes = f.read()

result = coordinator.process_import(business_id=1, file_bytes=zip_bytes, import_name="test_import7.zip")
print("Result is_successful:", result.is_successful)
print("Result warnings:", result.warnings)
print("Result errors:", result.errors)
