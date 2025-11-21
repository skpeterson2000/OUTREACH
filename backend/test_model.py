"""Test if Organization model has organization_type field."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Checking Organization model definition...")

from app.models.organization import Organization
from sqlalchemy import inspect

print(f"\n✅ Organization class imported")
print(f"Table name: {Organization.__tablename__}")

# Check columns
print("\nColumns defined in model:")
for col_name, col in Organization.__table__.columns.items():
    print(f"  - {col_name}: {col.type}")

# Check if organization_type exists
if hasattr(Organization, 'organization_type'):
    print("\n✅ organization_type attribute exists on model")
else:
    print("\n❌ organization_type attribute MISSING from model")

# Check __table__ 
if 'organization_type' in Organization.__table__.columns:
    print("✅ organization_type in __table__.columns")
else:
    print("❌ organization_type NOT in __table__.columns")
