"""Create patient_safety_alerts and staff_safety_alert_acknowledgments tables."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import PatientSafetyAlert, StaffSafetyAlertAcknowledgment

app = create_app()

with app.app_context():
    print("🔧 Creating patient safety alerts tables...")
    
    # Create tables
    PatientSafetyAlert.__table__.create(db.engine, checkfirst=True)
    StaffSafetyAlertAcknowledgment.__table__.create(db.engine, checkfirst=True)
    
    print("✅ Tables created successfully!")
    
    # Verify
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'patient_safety_alerts' in tables:
        print("   ✓ patient_safety_alerts table exists")
        columns = [col['name'] for col in inspector.get_columns('patient_safety_alerts')]
        print(f"     Columns: {', '.join(columns[:8])}...")
    
    if 'staff_safety_alert_acknowledgments' in tables:
        print("   ✓ staff_safety_alert_acknowledgments table exists")
    
    print("\n📊 Summary:")
    print(f"   Total tables in database: {len(tables)}")
    print(f"   New tables added: 2")
