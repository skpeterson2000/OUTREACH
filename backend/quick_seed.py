"""
Verbose seed data script with detailed progress tracking.
Shows exactly where the script is and what it's doing.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Organization, Facility, Device, User, Patient, Medication
from werkzeug.security import generate_password_hash


def log_step(step_num, total, message):
    """Log progress step."""
    progress = "=" * int(30 * step_num / total)
    remaining = "." * (30 - len(progress))
    print(f"\n[{progress}{remaining}] Step {step_num}/{total}: {message}")


def quick_seed():
    """Quick seed with minimal data and verbose logging."""
    app = create_app()
    
    with app.app_context():
        print("\n" + "🚀 "*30)
        print("VERBOSE SEED DATA - MINIMAL TEST")
        print("🚀 "*30 + "\n")
        
        total_steps = 6
        
        # Step 1: Create tables
        log_step(1, total_steps, "Creating database tables...")
        db.create_all()
        print("   ✅ Tables created")
        
        # Step 2: Create organization
        log_step(2, total_steps, "Creating organization...")
        org = Organization(
            name="Test Health Agency",
            organization_type="home_health",
            phone="555-0000",
            email="test@test.com",
            is_active=True
        )
        db.session.add(org)
        db.session.flush()
        print(f"   ✅ Organization created: ID={org.id}")
        
        # Step 3: Create facility
        log_step(3, total_steps, "Creating facility...")
        facility = Facility(
            organization_id=org.id,
            name="Test Facility",
            facility_type="HOME_HEALTH",
            facility_code="TEST-001",
            phone="555-0001",
            is_active=True
        )
        db.session.add(facility)
        db.session.flush()
        print(f"   ✅ Facility created: ID={facility.id}")
        
        # Step 4: Create device
        log_step(4, total_steps, "Creating device...")
        device = Device(
            facility_id=facility.id,
            device_name="Test-Tablet",
            device_type="TABLET",
            device_uuid="test-uuid-001",
            is_active=True
        )
        db.session.add(device)
        db.session.flush()
        print(f"   ✅ Device created: ID={device.id}")
        
        # Step 5: Create user
        log_step(5, total_steps, "Creating user...")
        user = User(
            facility_id=facility.id,
            username="test.nurse",
            email="nurse@test.com",
            password_hash=generate_password_hash("password123"),
            first_name="Test",
            last_name="Nurse",
            role="RN",
            is_active=True
        )
        db.session.add(user)
        db.session.flush()
        print(f"   ✅ User created: ID={user.id}, Username={user.username}")
        
        # Step 6: Create patient
        log_step(6, total_steps, "Creating patient...")
        patient = Patient(
            facility_id=facility.id,
            medical_record_number="TEST001",
            first_name="Test",
            last_name="Patient",
            date_of_birth=datetime(1950, 1, 1).date(),
            gender="M",
            status="active",
            admission_date=datetime.utcnow().date()
        )
        db.session.add(patient)
        db.session.flush()
        print(f"   ✅ Patient created: ID={patient.id}, MRN={patient.medical_record_number}")
        
        # Commit all
        print("\n💾 Committing to database...")
        db.session.commit()
        print("   ✅ All data committed successfully!")
        
        # Summary
        print("\n" + "="*60)
        print("✅ SEED COMPLETE - MINIMAL TEST DATA")
        print("="*60)
        print(f"\n📊 Created:")
        print(f"   • 1 Organization: {org.name}")
        print(f"   • 1 Facility: {facility.name}")
        print(f"   • 1 Device: {device.device_name}")
        print(f"   • 1 User: {user.username} ({user.role})")
        print(f"   • 1 Patient: {patient.full_name} (MRN: {patient.medical_record_number})")
        print("\n🔐 Login: username='test.nurse', password='password123'")
        print("="*60 + "\n")


if __name__ == "__main__":
    try:
        quick_seed()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nFull traceback:")
        import traceback
        traceback.print_exc()
        sys.exit(1)
