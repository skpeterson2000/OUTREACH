"""
Progress monitor for seed data script.
Shows what's being created in real-time with progress indicators.
"""

import sys
import os
import time

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def monitor_seed():
    """Monitor seed data creation step by step."""
    from app import create_app, db
    from app.models import (
        Organization, Facility, Device, User, Patient, 
        Medication, MedicationAdministration, Visit, VitalSigns
    )
    
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("📊 SEED DATA PROGRESS MONITOR")
        print("="*60 + "\n")
        
        # Check tables exist
        print("1️⃣  Checking database tables...")
        db.create_all()
        print("   ✅ Tables created/verified\n")
        
        # Monitor counts
        steps = [
            ("Organizations", Organization),
            ("Facilities", Facility),
            ("Devices", Device),
            ("Users", User),
            ("Patients", Patient),
            ("Medications", Medication),
            ("Medication Administrations", MedicationAdministration),
            ("Visits", Visit),
            ("Vital Signs", VitalSigns)
        ]
        
        print("2️⃣  Current database contents:\n")
        for name, model in steps:
            try:
                count = model.query.count()
                status = "✅" if count > 0 else "⚪"
                print(f"   {status} {name}: {count}")
            except Exception as e:
                print(f"   ❌ {name}: Error - {str(e)[:50]}")
        
        print("\n" + "="*60)
        print("💡 Run seed_data.py to populate the database")
        print("="*60 + "\n")


if __name__ == "__main__":
    monitor_seed()
