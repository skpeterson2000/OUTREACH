#!/usr/bin/env python3
"""
Seed realistic MAR (Medication Administration Record) history.

Creates historical medication administrations going back to patient admission,
with realistic patterns, variations, and multiple staff members including
some who are "no longer with the company" (for training scenarios).
"""

from datetime import datetime, timedelta, time
import random
from app import create_app, db
from app.models import (
    MedicationAdministration, Medication, Patient, User, Facility
)

# Former staff members (no longer with company) - for realistic records
FORMER_STAFF = [
    {
        'username': 'former.nurse1',
        'email': 'former.nurse1@harmonyhealth.com',
        'password': 'archived',
        'first_name': 'Patricia',
        'last_name': 'Williams',
        'role': 'RN',
        'status': 'inactive',
        'is_active': False
    },
    {
        'username': 'former.nurse2',
        'email': 'former.nurse2@harmonyhealth.com',
        'password': 'archived',
        'first_name': 'Robert',
        'last_name': 'Martinez',
        'role': 'LPN',
        'status': 'inactive',
        'is_active': False
    },
    {
        'username': 'former.tma',
        'email': 'former.tma@harmonyhealth.com',
        'password': 'archived',
        'first_name': 'Linda',
        'last_name': 'Johnson',
        'role': 'TMA',
        'status': 'inactive',
        'is_active': False
    }
]


def create_former_staff(facility_id):
    """Create former staff members for realistic historical records."""
    former_users = []
    
    for staff_data in FORMER_STAFF:
        # Check if user already exists
        existing = User.query.filter_by(username=staff_data['username']).first()
        if existing:
            former_users.append(existing)
            continue
            
        user = User(
            facility_id=facility_id,
            username=staff_data['username'],
            email=staff_data['email'],
            first_name=staff_data['first_name'],
            last_name=staff_data['last_name'],
            role=staff_data['role'],
            status=staff_data['status'],
            is_active=staff_data['is_active']
        )
        user.set_password(staff_data['password'])
        db.session.add(user)
        former_users.append(user)
    
    db.session.commit()
    return former_users


def get_scheduled_time_for_frequency(frequency, day_offset=0):
    """Get scheduled times for a given frequency."""
    times = []
    
    if frequency == 'QD':  # Once daily
        times = [time(9, 0)]
    elif frequency == 'BID':  # Twice daily
        times = [time(9, 0), time(21, 0)]
    elif frequency == 'TID':  # Three times daily
        times = [time(9, 0), time(14, 0), time(21, 0)]
    elif frequency == 'QID':  # Four times daily
        times = [time(9, 0), time(13, 0), time(17, 0), time(21, 0)]
    elif frequency == 'Q8H':  # Every 8 hours
        times = [time(6, 0), time(14, 0), time(22, 0)]
    elif frequency == 'Q12H':  # Every 12 hours
        times = [time(8, 0), time(20, 0)]
    elif frequency == 'QHS':  # At bedtime
        times = [time(22, 0)]
    elif frequency == 'Q6H':  # Every 6 hours
        times = [time(6, 0), time(12, 0), time(18, 0), time(0, 0)]
    elif frequency.startswith('AC'):  # Before meals
        times = [time(7, 30), time(11, 30), time(17, 30)]
    else:
        times = [time(9, 0)]  # Default
    
    return times


def calculate_actual_time(scheduled_time, status):
    """Calculate actual administration time with realistic variation."""
    if status in ['refused', 'held']:
        return None
    
    # Convert time to datetime for calculation
    base_dt = datetime.combine(datetime.today(), scheduled_time)
    
    # 80% on time (within 30 minutes), 15% early, 5% late
    rand = random.random()
    
    if rand < 0.80:  # On time
        variation = random.randint(-30, 30)
    elif rand < 0.95:  # Early
        variation = random.randint(-60, -5)
    else:  # Late
        variation = random.randint(35, 120)
    
    actual_dt = base_dt + timedelta(minutes=variation)
    return actual_dt.time()


def generate_status_with_realism():
    """Generate status with realistic distribution."""
    rand = random.random()
    
    if rand < 0.92:  # 92% given
        return 'given'
    elif rand < 0.95:  # 3% held
        return 'held'
    elif rand < 0.98:  # 3% refused
        return 'refused'
    else:  # 2% pending (shouldn't happen for historical, but handle it)
        return 'given'


def get_held_reason():
    """Get realistic reason for held medication."""
    reasons = [
        'NPO for procedure',
        'Patient sleeping, will administer when awake',
        'Vital signs out of range',
        'Patient off unit for appointment',
        'Nausea/vomiting present',
        'Hold per provider order',
        'Lab values pending',
        'Patient declined, will retry'
    ]
    return random.choice(reasons)


def get_refused_reason():
    """Get realistic reason for refused medication."""
    reasons = [
        'Patient refused, states feeling well',
        'Patient refused medication',
        'Patient states "too many pills"',
        'Patient refused, MD notified',
        'Patient reports side effects',
        'Patient adamant refusal'
    ]
    return random.choice(reasons)


def seed_mar_history():
    """Seed realistic MAR history for all active patients."""
    print("🏥 Seeding MAR History with Realistic Data\n")
    
    app = create_app()
    with app.app_context():
        # Get facility
        facility = Facility.query.first()
        if not facility:
            print("❌ No facility found")
            return
        
        # Create former staff
        print("👥 Creating former staff members...")
        former_users = create_former_staff(facility.id)
        print(f"   Created/found {len(former_users)} former staff members\n")
        
        # Get all active staff (current and former)
        all_staff = User.query.filter(
            User.facility_id == facility.id,
            User.role.in_(['RN', 'LPN', 'TMA'])
        ).all()
        
        if not all_staff:
            print("❌ No staff found")
            return
        
        print(f"👥 Available staff for administrations: {len(all_staff)}")
        for user in all_staff:
            status = "INACTIVE" if not user.is_active else "active"
            print(f"   - {user.first_name} {user.last_name} ({user.role}) [{status}]")
        print()
        
        # Get all active patients
        patients = Patient.query.filter_by(status='active').all()
        
        if not patients:
            print("❌ No active patients found")
            return
        
        print(f"📋 Processing {len(patients)} patients\n")
        
        total_administrations = 0
        
        for patient in patients:
            print(f"👤 Patient: {patient.first_name} {patient.last_name}")
            
            # Get patient's scheduled medications
            medications = Medication.query.filter_by(
                patient_id=patient.id,
                status='active'
            ).all()
            
            if not medications:
                print(f"   ⚠️  No active medications\n")
                continue
            
            print(f"   💊 {len(medications)} active medications")
            
            # Calculate days since admission (up to 90 days back)
            if patient.admission_date:
                if isinstance(patient.admission_date, datetime):
                    admission_date = patient.admission_date
                else:
                    admission_date = datetime.combine(patient.admission_date, time(0, 0))
            else:
                admission_date = datetime.now() - timedelta(days=30)
            
            days_since_admission = (datetime.now() - admission_date).days
            lookback_days = min(days_since_admission, 90)  # Max 90 days of history
            
            print(f"   📅 Admission: {admission_date.strftime('%Y-%m-%d')} ({lookback_days} days ago)")
            
            patient_administrations = 0
            
            # For each medication
            for med in medications:
                # Determine when this medication was started
                if med.start_date:
                    if isinstance(med.start_date, datetime):
                        med_start_date = med.start_date
                    else:
                        med_start_date = datetime.combine(med.start_date, time(0, 0))
                else:
                    med_start_date = admission_date
                
                days_on_med = (datetime.now() - med_start_date).days
                
                if days_on_med < 0:
                    continue
                
                # Get scheduled times for this frequency
                scheduled_times = get_scheduled_time_for_frequency(med.frequency)
                
                # Generate administrations for each day
                for day_offset in range(min(days_on_med, lookback_days)):
                    admin_date = datetime.now() - timedelta(days=day_offset)
                    
                    # Skip today (handled by generate_mar_schedule.py)
                    if day_offset == 0:
                        continue
                    
                    # For each scheduled time
                    for sched_time in scheduled_times:
                        scheduled_datetime = datetime.combine(admin_date.date(), sched_time)
                        
                        # Generate realistic status
                        status = generate_status_with_realism()
                        
                        # Calculate actual administration time
                        actual_time = calculate_actual_time(sched_time, status)
                        actual_datetime = datetime.combine(admin_date.date(), actual_time) if actual_time else scheduled_datetime
                        
                        # Choose staff member (weight towards current staff for recent dates)
                        if day_offset < 30:  # Last 30 days - mostly current staff
                            staff_pool = [u for u in all_staff if u.is_active]
                            if not staff_pool:
                                staff_pool = all_staff
                        else:  # Older records - mix of current and former
                            staff_pool = all_staff
                        
                        administered_by = random.choice(staff_pool)
                        
                        # Generate notes based on status
                        notes = None
                        if status == 'held':
                            notes = get_held_reason()
                        elif status == 'refused':
                            notes = get_refused_reason()
                        elif random.random() < 0.1:  # 10% of given meds have notes
                            notes = random.choice([
                                'Tolerated well',
                                'No adverse effects noted',
                                'Patient cooperative',
                                'Given with food as ordered',
                                'Patient requested water'
                            ])
                        
                        # Create administration record
                        admin = MedicationAdministration(
                            medication_id=med.id,
                            patient_id=patient.id,
                            scheduled_time=scheduled_datetime,
                            administration_time=actual_datetime,
                            status=status,
                            administered_by=administered_by.id,
                            dose_given=med.dose if status == 'given' else None,
                            notes=notes
                        )
                        
                        db.session.add(admin)
                        patient_administrations += 1
            
            db.session.commit()
            print(f"   ✅ Created {patient_administrations} administration records\n")
            total_administrations += patient_administrations
        
        print(f"✅ Seeding complete!")
        print(f"📊 Total administrations created: {total_administrations}")
        print(f"\n💡 Note: Former staff members are marked as 'inactive' for realism")
        print(f"   These can be used for training scenarios in the future.")


if __name__ == '__main__':
    seed_mar_history()
