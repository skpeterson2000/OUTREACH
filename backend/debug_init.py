"""
Debug script to test database initialization and imports.
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("DEBUG: Starting import tests...")
print("=" * 60)

try:
    print("\n1. Testing Flask app creation...")
    from app import create_app, db
    print("   ✅ Successfully imported create_app and db")
    
    print("\n2. Creating Flask app...")
    app = create_app()
    print(f"   ✅ App created: {app}")
    
    print("\n3. Pushing app context...")
    app.app_context().push()
    print("   ✅ App context pushed")
    
    print("\n4. Checking database configuration...")
    print(f"   Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    
    print("\n5. Testing model imports...")
    from app.models import (
        Organization, Facility, User, Patient, 
        Medication, Visit, AuditLog
    )
    print("   ✅ Core models imported successfully")
    
    print("\n6. Creating database tables...")
    db.create_all()
    print("   ✅ Database tables created")
    
    print("\n7. Testing basic query...")
    org_count = Organization.query.count()
    print(f"   ✅ Query successful - Organizations in DB: {org_count}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Database is ready!")
    print("=" * 60)
    
except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print(f"\nFull traceback:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"\nFull traceback:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
